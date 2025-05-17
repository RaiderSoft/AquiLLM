import hashlib
from typing import Dict, List, Optional, Any
from pyzotero import zotero
from django.conf import settings
import logging
import time
from django.core.cache import cache
import requests
from pypdf import PdfReader
import tempfile
import os
from aquillm.models import ZoteroTextChunk
from django.db import transaction
from django.apps import apps

logger = logging.getLogger(__name__)


def _generate_cache_key(prefix: str, *parts: str) -> str:
    """
    Generate a safe cache key by hashing parts that may be long or contain unsafe chars.
    """
    raw = ":".join(parts)
    hashed = hashlib.sha1(raw.encode()).hexdigest()
    return f"{prefix}:{hashed}"


def process_zotero_embeddings(item_key: str):
    """
    Create embeddings for Zotero PDF chunks
    """
    try:
        chunks = cache.get(f"zotero_chunks:{item_key}")
        if not chunks:
            logger.error(f"No chunks found for {item_key}")
            return
            
        # Delete existing chunks for this item
        ZoteroTextChunk.objects.filter(item_key=item_key).delete()
        
        batch_size = 10
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            
            # Create and save chunks (embeddings will be created automatically on save)
            chunk_objects = []
            for chunk_data in batch:
                chunk_objects.append(
                    ZoteroTextChunk(
                        item_key=item_key,
                        chunk_number=chunk_data['chunk_number'],
                        content=chunk_data['content']
                    )
                )
            
            with transaction.atomic():
                ZoteroTextChunk.objects.bulk_create(chunk_objects)
        
        cache.set(f"zotero_embedding_status:{item_key}", "complete", 24 * 3600)
        logger.info(f"Embeddings created for {item_key}")
        
    except Exception as e:
        logger.error(f"Error creating embeddings for {item_key}: {e}", exc_info=True)
        cache.set(f"zotero_embedding_status:{item_key}", f"error_{str(e)}", 24 * 3600)

 
def extract_full_pdf(item_key: str):
    """
    Extract all text from a PDF and save it to cache.
    Now also creates chunks for vector embedding.
    """
    logger.info(f"Starting full PDF extraction for {item_key}")
    zot_client = ZoteroClient()

    try:
        cache.set(f"zotero_pdf_status:{item_key}", "processing_started", 3600)

        # Check if this is already a PDF attachment
        item = zot_client.zot.item(item_key)
        item_type = item.get('data', {}).get('itemType')
        is_attachment = item_type == 'attachment'
        
        # Variables to hold PDF information
        url = None
        pdf_att = None
        
        if is_attachment:
            logger.info(f"Item {item_key} is already a PDF attachment")
            content_type = item.get('data', {}).get('contentType', '')
            filename = item.get('data', {}).get('filename', '')
            
            if ('pdf' in content_type.lower() or 
                'pdf' in filename.lower()):
                pdf_att = item
                
                # Get links directly from the item
                if 'links' in item:
                    links = item['links']
                    logger.info(f"Attachment links: {links}")
                    
                    if 'enclosure' in links:
                        url = links['enclosure']['href']
                        logger.info(f"Using enclosure link: {url}")
                    elif 'attachment' in links:
                        url = links['attachment']['href']
                        logger.info(f"Using attachment link: {url}")
                    elif 'self' in links:
                        url = f"{links['self']['href']}/file"
                        logger.info(f"Using self link + /file: {url}")
        else:
             
            logger.info(f"Item {item_key} is not an attachment, looking for child PDF")
            attachments = zot_client.zot.children(item_key)
            
            # Log detailed attachment info
            logger.info(f"Found {len(attachments)} attachments for item {item_key}")
            for i, att in enumerate(attachments):
                content_type = att.get('data', {}).get('contentType', 'unknown')
                filename = att.get('data', {}).get('filename', 'unknown')
                logger.info(f"Attachment {i}: {filename}, type: {content_type}")
                if 'links' in att:
                    logger.info(f"Links for attachment {i}: {att['links']}")
            
            # Find PDF attachment using multiple methods
            for att in attachments:
                content_type = att.get('data', {}).get('contentType', '')
                filename = att.get('data', {}).get('filename', '')
                
                if (content_type == 'application/pdf' or 
                    'pdf' in content_type.lower() or 
                    filename.lower().endswith('.pdf')):
                    pdf_att = att
                    logger.info(f"Found PDF attachment: {filename}")
                    break

            if pdf_att and 'links' in pdf_att:
                # Get download URL using multiple methods
                links = pdf_att['links']
                
                if 'enclosure' in links:
                    url = links['enclosure']['href']
                    logger.info(f"Using enclosure link: {url}")
                elif 'attachment' in links:
                    url = links['attachment']['href']
                    logger.info(f"Using attachment link: {url}")
                elif 'self' in links:
                    url = f"{links['self']['href']}/file"
                    logger.info(f"Using self link + /file: {url}")

        # If no PDF found or no URL available
        if not pdf_att or not url:
            if not pdf_att:
                logger.warning(f"No PDF attachment found for {item_key}")
            else:
                logger.warning(f"No download URL could be determined")
            cache.set(f"zotero_pdf_status:{item_key}", "no_pdf_or_url", 24 * 3600)
            return

        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {settings.ZOTERO_API_KEY}",
            "User-Agent": "AquiLLM/1.0"
        })
        
        # Always follow redirects and stream the response
        resp = session.get(url, timeout=30, allow_redirects=True, stream=True)
        logger.info(f"Response status: {resp.status_code}")
        logger.info(f"Response headers: {dict(resp.headers)}")
        
        # Validate content type
        content_type = resp.headers.get('Content-Type', '').lower()
        logger.info(f"Content-Type of response: {content_type}")
        if 'pdf' not in content_type and 'octet-stream' not in content_type and 'application/' not in content_type:
            logger.warning(f"Response may not be a PDF. Content-Type: {content_type}")

        if resp.status_code != 200:
            logger.error(f"Failed to download PDF: status code {resp.status_code}")
            logger.error(f"Response text preview: {resp.text[:500] if hasattr(resp, 'text') else 'No text available'}")
            cache.set(
                f"zotero_pdf_status:{item_key}",
                f"download_failed_{resp.status_code}",
                24 * 3600
            )
            return

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            logger.info(f"Created temporary file: {tmp.name}")
            bytes_written = 0
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    tmp.write(chunk)
                    bytes_written += len(chunk)
            tmp_path = tmp.name
            logger.info(f"Wrote {bytes_written} bytes to temporary file")

        try:
            logger.info(f"Opening PDF file: {tmp_path}")
            reader = PdfReader(tmp_path)
            total_pages = len(reader.pages)
            logger.info(f"Successfully opened PDF with {total_pages} pages")

            all_text = []
            all_chunks = []
            current_chunk = ""
            chunk_size = apps.get_app_config('aquillm').chunk_size
            overlap = apps.get_app_config('aquillm').chunk_overlap
            chunk_pitch = chunk_size - overlap
            chunk_number = 0
            
            for i in range(total_pages):
                try:
                    logger.info(f"Extracting text from page {i+1}/{total_pages}")
                    page_text = reader.pages[i].extract_text() or ""
                    text_length = len(page_text)
                    logger.info(f"Extracted {text_length} characters from page {i+1}")
                    all_text.append(page_text)
                    
                    # Store individual page
                    cache.set(f"zotero_page:{item_key}:{i}", page_text, 24 * 3600)
                    
                    # Add page to current chunk
                    current_chunk += page_text + " "
                    
                    # When chunk is large enough, save it and start new one
                    while len(current_chunk) >= chunk_size:
                        chunk_content = current_chunk[:chunk_size]
                        all_chunks.append({
                            'chunk_number': chunk_number,
                            'content': chunk_content,
                            'pages': list(range(max(0, i-5), i+1))  # Track page refs
                        })
                        
                        # Keep overlap for context
                        current_chunk = current_chunk[chunk_size-overlap:]
                        chunk_number += 1
                    
                    # Update status more frequently
                    if i % 5 == 0 or i == total_pages - 1:
                        cache.set(
                            f"zotero_pdf_status:{item_key}",
                            f"processing_{i+1}_of_{total_pages}",
                            300
                        )
                except Exception as err:
                    logger.warning(f"Error extracting page {i+1}: {err}", exc_info=True)
                    all_text.append(
                        f"[Error extracting text from page {i+1}: {err}]"
                    )

            # Save any remaining chunk
            if current_chunk.strip():
                all_chunks.append({
                    'chunk_number': chunk_number,
                    'content': current_chunk.strip(),
                    'pages': list(range(max(0, total_pages-5), total_pages))
                })

            # Store basic text data
            full_text = "\n\n".join(
                f"--- PAGE {i+1} ---\n{text}" for i, text in enumerate(all_text)
            )
            cache.set(f"zotero_fulltext:{item_key}", full_text, 24 * 3600)
            
            # Store chunks for embedding processing
            cache.set(f"zotero_chunks:{item_key}", all_chunks, 24 * 3600)
            cache.set(f"zotero_pdf_status:{item_key}", "complete", 24 * 3600)
            cache.set(f"zotero_pdf_pages:{item_key}", total_pages, 24 * 3600)

            searchable = " ".join(all_text)
            cache.set(f"zotero_searchable:{item_key}", searchable, 24 * 3600)
            logger.info(f"Successfully processed PDF: {total_pages} pages, {len(searchable)} chars")

            # Trigger embedding processing
            process_zotero_embeddings(item_key)

        except Exception as e:
            logger.error(f"Error processing PDF {item_key}: {e}", exc_info=True)
            cache.set(
                f"zotero_pdf_status:{item_key}", f"error_{str(e)[:50]}", 24 * 3600
            )
        finally:
            # Clean up temp file
            logger.info(f"Cleaning up temporary file: {tmp_path}")
            try:
                os.unlink(tmp_path)
                logger.info(f"Successfully deleted temporary file")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")
    except Exception as e:
        logger.error(f"Error in extract_full_pdf for {item_key}: {e}", exc_info=True)
        cache.set(
            f"zotero_pdf_status:{item_key}", f"error_{str(e)[:50]}", 24 * 3600
        )


class ZoteroClient:
    """Client for interacting with the Zotero API."""

    def __init__(self):
        library_id = settings.ZOTERO_LIBRARY_ID
        library_type = settings.ZOTERO_LIBRARY_TYPE
        api_key = settings.ZOTERO_API_KEY

        logger.info(
            f"Initializing Zotero client with Library ID: {library_id}, Type: {library_type}"
        )
        if not library_id or not api_key:
            logger.error("Missing Zotero credentials!")
            raise RuntimeError(
                "Missing Zotero credentials: set ZOTERO_LIBRARY_ID and ZOTERO_API_KEY"
            )

        self.zot = zotero.Zotero(library_id, library_type, api_key)
        self._rate_limit_remaining = 300
        self._rate_limit_reset = 0

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search Zotero library with the given query (qmode=everything).
        Returns list of item metadata dicts.
        """
        logger.info(f"Searching Zotero for: '{query}' with limit {limit}")
        cache_key = _generate_cache_key("zotero_search", query, str(limit))
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f"Using cached search results for '{query}'")
            return cached

        try:
            # Just do the search without trying to access last_response
            items = self.zot.items(q=query, limit=limit, qmode="everything")
            
            logger.info(f"Found {len(items)} items for query '{query}'")
            cache.set(cache_key, items, 3600)
            return items
        except Exception as e:
            logger.error(f"Zotero search error: {e}", exc_info=True)
            return []

    def fetch_fulltext(self, item_key: str) -> Optional[str]:
        """
        Download PDF attachment for item_key, extract up to 30 pages of text.
        """
        logger.info(f"Fetching fulltext for item: {item_key}")
        cache_key = _generate_cache_key("zotero_fulltext", item_key)
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f"Using cached fulltext for {item_key}")
            return cached

        try:
            item = self.zot.item(item_key)
            attachments = self.zot.children(item_key)
            
            # Log all attachments for debugging
            logger.info(f"Found {len(attachments)} attachments for item {item_key}")
            
            # Try to find PDF attachment
            pdf_att = None
            for att in attachments:
                content_type = att.get('data', {}).get('contentType', '')
                filename = att.get('data', {}).get('filename', '')
                logger.info(f"Attachment details: type={content_type}, filename={filename}")
                
                if (content_type == 'application/pdf' or 
                    'pdf' in content_type.lower() or
                    filename.lower().endswith('.pdf')):
                    pdf_att = att
                    logger.info(f"Found PDF attachment: {filename}")
                    break
            
            if not pdf_att:
                logger.warning(f"No PDF attachment found for {item_key}")
                # Return metadata summary as fallback
                return self.get_item_metadata_summary(item_key)

            # Get download URL
            url = None
            if 'links' in pdf_att:
                links = pdf_att['links']
                logger.info(f"Attachment links: {links}")
                
                if 'enclosure' in links:
                    url = links['enclosure']['href']
                    logger.info(f"Using enclosure link: {url}")
                elif 'attachment' in links:
                    url = links['attachment']['href']
                    logger.info(f"Using attachment link: {url}")
                elif 'self' in links:
                    url = f"{links['self']['href']}/file"
                    logger.info(f"Using self/file link: {url}")
            
            if not url:
                logger.error(f"Could not find download URL for PDF attachment")
                return self.get_item_metadata_summary(item_key)

            # Download the PDF with proper redirect handling and streaming
            logger.info(f"Downloading PDF from {url}")
            session = requests.Session()
            session.headers.update({
                "Authorization": f"Bearer {settings.ZOTERO_API_KEY}",
                "User-Agent": "AquiLLM/1.0"
            })
            
            # Follow redirects and use streaming
            resp = session.get(url, timeout=30, allow_redirects=True, stream=True)
            
            # Log full response details for debugging
            logger.info(f"Response status: {resp.status_code}")
            logger.info(f"Response headers: {dict(resp.headers)}")
            logger.info(f"Content type: {resp.headers.get('Content-Type', 'unknown')}")
            
            if resp.status_code != 200:
                logger.error(f"Failed to download PDF: status code {resp.status_code}")
                logger.error(f"Response text preview: {resp.text[:500] if hasattr(resp, 'text') else 'No text available'}")
                return self.get_item_metadata_summary(item_key)

            # Check content type
            content_type = resp.headers.get('Content-Type', '').lower()
            if 'pdf' not in content_type and 'octet-stream' not in content_type and 'application/' not in content_type:
                logger.warning(f"Response may not be a PDF. Content-Type: {content_type}")

            # Save the PDF to a temporary file using proper streaming
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                bytes_written = 0
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        tmp.write(chunk)
                        bytes_written += len(chunk)
                tmp_path = tmp.name
                logger.info(f"PDF downloaded to temporary file: {tmp_path} ({bytes_written} bytes)")

            # Process the PDF
            text = ""
            try:
                reader = PdfReader(tmp_path)
                logger.info(f"PDF opened successfully, contains {len(reader.pages)} pages")
                
                for i in range(min(30, len(reader.pages))):
                    try:
                        page_text = reader.pages[i].extract_text() or ""
                        text += page_text + "\n"
                        logger.info(f"Extracted page {i+1} ({len(page_text)} chars)")
                    except Exception as err:
                        logger.warning(f"Error on page {i+1}: {err}", exc_info=True)
            except Exception as pdf_err:
                logger.error(f"Error processing PDF: {pdf_err}", exc_info=True)
                return self.get_item_metadata_summary(item_key)
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                    logger.info(f"Deleted temporary file {tmp_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")

            text = text.replace('\0', '')
            cache.set(cache_key, text, 24 * 3600)
            return text

        except Exception as e:
            logger.error(f"Fulltext fetch error for {item_key}: {e}", exc_info=True)
            return self.get_item_metadata_summary(item_key)

    def get_item_metadata_summary(self, item_key: str) -> str:
        """Helper method to return metadata summary when PDF can't be downloaded"""
        try:
            item = self.get_item_metadata(item_key)
            data = item.get('data', {})
            creators = ", ".join(
                f"{c.get('firstName','')} {c.get('lastName','')}"
                for c in data.get('creators', [])
            ) or "Unknown"
            
            summary = (
                f"Title: {data.get('title','Untitled')}\n"
                f"Authors: {creators}\n"
                f"Publication: {data.get('publicationTitle','')}\n"
                f"Date: {data.get('date','')}\n"
                f"DOI: {data.get('DOI','')}\n"
                f"URL: {data.get('url','')}\n\n"
                f"Abstract:\n{data.get('abstractNote','')}\n"
            )
            return summary
        except Exception as e:
            logger.error(f"Failed to create metadata summary: {e}", exc_info=True)
            return "Unable to retrieve item information"

    def process_pdf_background(self, item_key: str) -> bool:
        """
        Initiates background processing of a PDF.
        Returns True if processing started successfully, False otherwise.
        """
        try:
            logger.info(f"Starting background PDF processing for {item_key}")
            # Set initial status in cache
            cache.set(f"zotero_pdf_status:{item_key}", "processing_started", 3600)
            
            # Call the standalone function in a try/except block
            try:
                # Using the globally defined extract_full_pdf function
                extract_full_pdf(item_key)
                return True
            except Exception as e:
                logger.error(f"Error in extract_full_pdf: {e}", exc_info=True)
                # Store a more helpful error message
                cache.set(f"zotero_pdf_status:{item_key}", f"error_processing_{str(e)[:50]}", 3600)
                return False
                
        except Exception as e:
            logger.error(f"Failed to start PDF processing for {item_key}: {e}", exc_info=True)
            cache.set(f"zotero_pdf_status:{item_key}", f"error_starting_{str(e)[:50]}", 3600)
            return False

    def get_item_metadata(self, item_key: str) -> Dict[str, Any]:
        """
        Fetch and cache full item metadata for item_key.
        """
        logger.info(f"Getting metadata for item: {item_key}")
        cache_key = _generate_cache_key("zotero_metadata", item_key)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            item = self.zot.item(item_key)
            cache.set(cache_key, item, 24 * 3600)
            return item
        except Exception as e:
            logger.error(f"Metadata fetch error for {item_key}: {e}", exc_info=True)
            return {"data": {"title": "Unknown Item", "creators": []}}

    def extract_pdf_page(
        self, item_key: str, page_start: int, page_count: int
    ) -> Optional[str]:
        """
        Extract a specific range of pages from a PDF.
        Limits page_count to 3 to avoid performance issues.
        """
        page_count = min(page_count, 3)
        cache_key = _generate_cache_key(
            "zotero_page_range", item_key, str(page_start), str(page_count)
        )
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            logger.info(
                f"Extracting PDF pages for {item_key}, pages {page_start}-{page_start+page_count}"
            )
            
            # Get item and attachments
            item = self.get_item_metadata(item_key)
            attachments = self.zot.children(item_key)
            
            # Find PDF attachment
            pdf_att = None
            for att in attachments:
                content_type = att.get('data', {}).get('contentType', '')
                filename = att.get('data', {}).get('filename', '')
                logger.info(f"Attachment: type={content_type}, filename={filename}")
                
                if (content_type == 'application/pdf' or 
                    'pdf' in content_type.lower() or 
                    filename.lower().endswith('.pdf')):
                    pdf_att = att
                    logger.info(f"Found PDF attachment: {filename}")
                    break
            
            if not pdf_att or 'links' not in pdf_att:
                logger.warning(f"No PDF attachment found for {item_key}")
                return None

            # Get download URL - try multiple approaches
            links = pdf_att['links']
            logger.info(f"Attachment links: {links}")
            
            url = None
            if 'enclosure' in links:
                url = links['enclosure']['href']
                logger.info(f"Using enclosure link: {url}")
            elif 'attachment' in links:
                url = links['attachment']['href']
                logger.info(f"Using attachment link: {url}")
            elif 'self' in links:
                url = f"{links['self']['href']}/file"
                logger.info(f"Using self/file link: {url}")
            
            if not url:
                logger.error(f"Could not find download URL for PDF")
                return None

            # Download the PDF with proper redirect handling
            logger.info(f"Downloading PDF from {url}")
            session = requests.Session()
            session.headers.update({
                "Authorization": f"Bearer {settings.ZOTERO_API_KEY}",
                "User-Agent": "AquiLLM/1.0"
            })
            
            # Use allow_redirects=True and stream=True
            resp = session.get(url, timeout=30, allow_redirects=True, stream=True)
            logger.info(f"Response status: {resp.status_code}")
            logger.info(f"Response headers: {dict(resp.headers)}")
            logger.info(f"Content type: {resp.headers.get('Content-Type', 'unknown')}")
            
            if resp.status_code != 200:
                logger.error(f"Failed to download PDF: status code {resp.status_code}")
                logger.error(f"Response text preview: {resp.text[:500] if hasattr(resp, 'text') else 'No text available'}")
                return None

            # Check content type
            content_type = resp.headers.get('Content-Type', '').lower()
            if 'pdf' not in content_type and 'octet-stream' not in content_type and 'application/' not in content_type:
                logger.warning(f"Response may not be a PDF. Content-Type: {content_type}")

            # Save to temp file using streaming
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                bytes_written = 0
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        tmp.write(chunk)
                        bytes_written += len(chunk)
                tmp_path = tmp.name
                logger.info(f"Downloaded {bytes_written} bytes to {tmp_path}")
            
            # Process the PDF
            text = ""
            try:
                reader = PdfReader(tmp_path)
                total_pages = len(reader.pages)
                logger.info(f"PDF has {total_pages} pages total")

                if page_start >= total_pages:
                    os.unlink(tmp_path)  # Clean up
                    return f"Start page {page_start} exceeds document length ({total_pages} pages)"
                    
                for i in range(page_start, min(page_start + page_count, total_pages)):
                    try:
                        logger.info(f"Extracting page {i+1}")
                        page_text = reader.pages[i].extract_text() or ""
                        text += f"--- PAGE {i+1} ---\n{page_text}\n\n"
                        logger.info(f"Extracted {len(page_text)} chars from page {i+1}")
                    except Exception as err:
                        logger.warning(f"Error extracting page {i+1}: {err}", exc_info=True)
                        text += f"--- PAGE {i+1} ---\n[Error extracting text: {err}]\n\n"
            finally:
                # Clean up the temp file
                try:
                    os.unlink(tmp_path)
                    logger.info(f"Deleted temporary file {tmp_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")

            # Clean and return result
            text = text.replace("\0", "")
            if len(text) > 5000:
                text = text[:5000] + "... [truncated]"
            cache.set(cache_key, text, 24 * 3600)
            return text

        except Exception as e:
            logger.error(f"PDF page extraction error for {item_key}: {e}", exc_info=True)
            return None

    def download_pdf_for_testing(self, item_key: str, output_path: str) -> bool:
        """
        Download a PDF directly to a file for testing purposes.
        Returns True on success, False on failure.
        """
        try:
            logger.info(f"Testing direct PDF download for {item_key} to {output_path}")
            item = self.get_item_metadata(item_key)
            attachments = self.zot.children(item_key)
            
            # Find PDF attachment
            pdf_att = None
            for att in attachments:
                content_type = att.get('data', {}).get('contentType', '')
                filename = att.get('data', {}).get('filename', '')
                logger.info(f"Test download - attachment: {filename}, type: {content_type}")
                
                if (content_type == 'application/pdf' or 
                    'pdf' in content_type.lower() or 
                    filename.lower().endswith('.pdf')):
                    pdf_att = att
                    logger.info(f"Test download - found PDF: {filename}")
                    break
            
            if not pdf_att or 'links' not in pdf_att:
                logger.error(f"Test download - no PDF attachment found for {item_key}")
                return False

            # Get download URL
            links = pdf_att['links']
            logger.info(f"Test download - attachment links: {links}")
            
            url = None
            if 'enclosure' in links:
                url = links['enclosure']['href']
                logger.info(f"Test download - using enclosure link: {url}")
            elif 'attachment' in links:
                url = links['attachment']['href']
                logger.info(f"Test download - using attachment link: {url}")
            elif 'self' in links:
                url = f"{links['self']['href']}/file"
                logger.info(f"Test download - using self/file link: {url}")
            
            if not url:
                logger.error(f"Test download - could not find download URL")
                return False

            # Download with proper headers
            session = requests.Session()
            session.headers.update({
                "Authorization": f"Bearer {settings.ZOTERO_API_KEY}",
                "User-Agent": "AquiLLM/1.0"
            })
            
            logger.info(f"Test download - requesting {url}")
            resp = session.get(url, timeout=30, allow_redirects=True, stream=True)
            logger.info(f"Test download - response status: {resp.status_code}")
            logger.info(f"Test download - response headers: {dict(resp.headers)}")
            
            if resp.status_code != 200:
                logger.error(f"Test download - failed: status code {resp.status_code}")
                return False

            # Write to file directly
            with open(output_path, 'wb') as f:
                bytes_written = 0
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        bytes_written += len(chunk)
            
            logger.info(f"Test download - PDF successfully downloaded to {output_path} ({bytes_written} bytes)")
            
            # Validate the file is a PDF
            try:
                reader = PdfReader(output_path)
                page_count = len(reader.pages)
                logger.info(f"Test download - PDF validation successful: {page_count} pages")
                return True
            except Exception as val_err:
                logger.error(f"Test download - PDF validation failed: {val_err}", exc_info=True)
                return False
            
        except Exception as e:
            logger.error(f"Test download - error: {e}", exc_info=True)
            return False


def test_zotero_pdf(item_key: str = "QYVA8KBT"):
    """
    Test function to verify Zotero PDF download and processing works correctly.
    """
    logger.info(f"Starting Zotero PDF test for item {item_key}")
    client = ZoteroClient()
    
    # Check if the item is already a PDF attachment
    try:
        item = client.zot.item(item_key)
        item_type = item.get('data', {}).get('itemType')
        logger.info(f"Item type: {item_type}")
        
        # If it's an attachment
        if item_type == 'attachment':
            content_type = item.get('data', {}).get('contentType', '')
            filename = item.get('data', {}).get('filename', '')
            logger.info(f"This is an attachment item with filename: {filename}, content_type: {content_type}")
            
            # Check if it has download links
            if 'links' in item:
                links = item['links']
                logger.info(f"Item has links: {links}")
                
                # Determine download URL
                url = None
                if 'enclosure' in links:
                    url = links['enclosure']['href']
                    logger.info(f"Using enclosure link: {url}")
                elif 'attachment' in links:
                    url = links['attachment']['href']
                    logger.info(f"Using attachment link: {url}")
                elif 'self' in links:
                    url = f"{links['self']['href']}/file"
                    logger.info(f"Using self/file link: {url}")
                
                if url:
                    # Download the file
                    test_path = "/tmp/test_zotero.pdf"
                    logger.info(f"Downloading file from {url} to {test_path}")
                    
                    session = requests.Session()
                    session.headers.update({
                        "Authorization": f"Bearer {settings.ZOTERO_API_KEY}",
                        "User-Agent": "AquiLLM/1.0"
                    })
                    
                    resp = session.get(url, timeout=30, allow_redirects=True, stream=True)
                    logger.info(f"Response status: {resp.status_code}")
                    logger.info(f"Response headers: {dict(resp.headers)}")
                    
                    if resp.status_code == 200:
                        with open(test_path, 'wb') as f:
                            bytes_written = 0
                            for chunk in resp.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    bytes_written += len(chunk)
                                    
                        logger.info(f"Downloaded {bytes_written} bytes to {test_path}")
                        
                        # Validate PDF
                        try:
                            reader = PdfReader(test_path)
                            page_count = len(reader.pages)
                            logger.info(f"PDF has {page_count} pages")
                            
                            if page_count > 0:
                                sample_text = reader.pages[0].extract_text()[:100]
                                logger.info(f"First page text sample: {sample_text}")
                                
                            return True
                        except Exception as e:
                            logger.error(f"Error reading PDF: {e}", exc_info=True)
                    else:
                        logger.error(f"Failed to download: {resp.status_code}")
            else:
                logger.error("Item has no links")
        else:
            # Original implementation for non-attachment items
            # Try direct download using the client method
            logger.info("Item is not an attachment, using original test method")
            return client.download_pdf_for_testing(item_key, "/tmp/test_zotero.pdf")
            
    except Exception as e:
        logger.error(f"Error in test_zotero_pdf: {e}", exc_info=True)
        
    return False