# consumers.py

from typing import Optional, List
from json import loads, dumps
from uuid import UUID
from django.core.cache import cache

from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async, aclose_old_connections

from django.contrib.auth.models import User
from django.apps import apps
from django.db.models import Q

import requests
import tempfile
import os
from pypdf import PdfReader
from django.conf import settings

from pydantic_core import to_jsonable_python
from aquillm.llm import (
    UserMessage,
    Conversation,
    LLMTool,
    LLMInterface,
    test_function,
    ToolChoice,
    llm_tool,
    ToolResultDict,
)
from aquillm.settings import DEBUG
from aquillm.models import (
    TextChunk,
    Collection,
    CollectionPermission,
    WSConversation,
    Document,
    DocumentChild,
    ZoteroTextChunk,
)
from aquillm.zotero_api import ZoteroClient

from anthropic._exceptions import OverloadedError


class CollectionsRef:
    def __init__(self, collections: List[int]):
        self.collections = collections


class ChatRef:
    def __init__(self, chat: 'ChatConsumer'):
        self.chat = chat


def get_zotero_vector_search(chat_ref: ChatRef) -> LLMTool:
    @llm_tool(
        for_whom='assistant',
        required=['search_string', 'top_k'],
        param_descs={
            'search_string': 'The query string for vector search',
            'top_k': 'Number of results to return per item'
        },
    )
    def zotero_vector_search(search_string: str, top_k: int) -> ToolResultDict:
        """
        Perform vector search on Zotero PDF content
        """
        try:
            # Use the class method to get the shared client
            if not hasattr(chat_ref.chat, 'zotero_client') or chat_ref.chat.zotero_client is None:
                print("WARNING: Zotero client not initialized in zotero_vector_search!")
                chat_ref.chat.zotero_client = ChatConsumer.get_zotero_client()
            
            # Special handling for references/bibliography queries
            if "reference" in search_string.lower() or "bibliography" in search_string.lower():
                print("References query detected - using specialized handling")
                # Query vector database for all chunks that might contain references
                from django.db.models import Q
                chunks = ZoteroTextChunk.objects.filter(
                    Q(content__icontains="reference") | 
                    Q(content__icontains="bibliography") |
                    Q(content__icontains="[1]") |
                    Q(content__icontains="[2]")
                ).order_by('item_key', 'chunk_number')
                
                # Group by item_key
                results_by_item = {}
                
                for chunk in chunks:
                    if chunk.item_key not in results_by_item:
                        # Get metadata
                        try:
                            metadata = chat_ref.chat.zotero_client.get_item_metadata(chunk.item_key)
                            title = metadata.get('data', {}).get('title', 'Unknown')
                        except Exception as e:
                            print(f"Error getting metadata for {chunk.item_key}: {e}")
                            title = f"Item {chunk.item_key}"
                        
                        results_by_item[chunk.item_key] = {
                            'title': title,
                            'chunks': []
                        }
                    
                    results_by_item[chunk.item_key]['chunks'].append(chunk)
                
                # Format results with complete reference sections
                formatted_results = {}
                for item_key, data in results_by_item.items():
                    # Sort chunks by number to maintain order
                    sorted_chunks = sorted(data['chunks'], key=lambda x: x.chunk_number)
                    formatted_chunks = []
                    
                    for chunk in sorted_chunks:
                        formatted_chunks.append(
                            f"[Chunk {chunk.chunk_number}]\n{chunk.content}"
                        )
                    
                    formatted_results[f"{data['title']} ({item_key})"] = "\n\n".join(formatted_chunks)
                
                return {"result": formatted_results}
            
            
            # Regular vector search (unchanged)
            _, _, chunks = ZoteroTextChunk.text_chunk_search(search_string, top_k * 3)
            
            if not chunks:
                return {"result": {"message": "No results found in Zotero library"}}
            
            # Group by item_key and get metadata
            results_by_item = {}
            
            for chunk in chunks:
                if chunk.item_key not in results_by_item:
                    try:
                        metadata = chat_ref.chat.zotero_client.get_item_metadata(chunk.item_key)
                        title = metadata.get('data', {}).get('title', 'Unknown')
                    except Exception as e:
                        print(f"Error getting metadata for {chunk.item_key}: {e}")
                        title = f"Item {chunk.item_key}"
                    
                    results_by_item[chunk.item_key] = {
                        'title': title,
                        'chunks': []
                    }
                
                results_by_item[chunk.item_key]['chunks'].append(chunk)
            
            # Format results
            formatted_results = {}
            for item_key, data in results_by_item.items():
                # Take top chunks per item
                top_chunks = data['chunks'][:top_k]
                formatted_chunks = []
                for chunk in top_chunks:
                    formatted_chunks.append(
                        f"[Chunk {chunk.chunk_number}]\n{chunk.content}"
                    )
                
                formatted_results[f"{data['title']} ({item_key})"] = "\n\n".join(formatted_chunks)
            
            return {"result": formatted_results}
            
        except Exception as e:
            print(f"Error in zotero vector search: {e}")
            import traceback
            traceback.print_exc()
            return {"exception": str(e)}
    
    return zotero_vector_search


def get_document_ids_func(user: User, col_ref: CollectionsRef) -> LLMTool:
    @llm_tool(for_whom='assistant', required=[], param_descs={})
    def document_ids() -> ToolResultDict:
        """
        Return names and IDs of all documents in the selected collections.
        """
        docs = Collection.get_user_accessible_documents(
            user, Collection.objects.filter(id__in=col_ref.collections)
        )
        if not docs:
            return {
                "exception": "No documents to search! Either no collections were selected, or they're empty."
            }
        return {"result": {doc.title: str(doc.id) for doc in docs}}

    return document_ids


def get_whole_document_func(user: User, chat_ref: ChatRef) -> LLMTool:
    @llm_tool(
        for_whom='assistant',
        required=['doc_id'],
        param_descs={'doc_id': 'UUID (as a string) of the document to return in full'},
    )
    def whole_document(doc_id: str) -> ToolResultDict:
        """
        Get the full text of a document (if not too large).
        """
        doc_uuid = UUID(doc_id)
        doc: Optional[DocumentChild] = Document.get_by_id(doc_uuid)
        if doc is None:
            return {"exception": f"Document {doc_id} does not exist!"}
        if not doc.collection.user_can_view(user):
            return {"exception": f"User cannot access document {doc_id}!"}

        token_count = async_to_sync(chat_ref.chat.llm_if.token_count)(
            chat_ref.chat.convo, doc.full_text
        )
        if token_count > 150_000:
            return {"exception": f"Document {doc_id} is too large to open in this chat."}
        return {"result": doc.full_text}

    return whole_document


def get_search_single_document_func(user: User) -> LLMTool:
    @llm_tool(
        for_whom='assistant',
        required=['doc_id', 'search_string', 'top_k'],
        param_descs={
            'doc_id': 'UUID of the document to search.',
            'search_string': 'String to search the document by.',
            'top_k': 'Number of results to return.',
        },
    )
    def search_single_document(doc_id: str, search_string: str, top_k: int) -> ToolResultDict:
        """
        Vector search within a single document.
        """
        doc_uuid = UUID(doc_id)
        doc = Document.get_by_id(doc_uuid)
        if doc is None:
            return {"exception": f"Document {doc_id} does not exist!"}
        if not doc.collection.user_can_view(user):
            return {"exception": f"User cannot access document {doc_id}!"}

        _, _, results = TextChunk.text_chunk_search(search_string, top_k, [doc])
        return {
            "result": {
                f"[Result {i+1}] -- {chunk.document.title} "
                f"chunk #: {chunk.chunk_number} chunk_id:{chunk.id}": chunk.content
                for i, chunk in enumerate(results)
            }
        }

    return search_single_document


def get_more_context_func(user: User) -> LLMTool:
    @llm_tool(
        for_whom='assistant',
        required=['chunk_id', 'adjacent_chunks'],
        param_descs={
            'chunk_id': 'ID number of the chunk for which more context is desired',
            'adjacent_chunks': 'How many chunks on either side to return (1–10).',
        },
    )
    def more_context(chunk_id: int, adjacent_chunks: int) -> ToolResultDict:
        """
        Return adjacent text chunks around a given chunk.
        """
        if not (1 <= adjacent_chunks <= 10):
            return {"exception": "Invalid value for adjacent_chunks!"}

        central = TextChunk.objects.filter(id=chunk_id).first()
        if central is None:
            return {"exception": f"Text chunk {chunk_id} does not exist!"}
        if not central.document.collection.user_can_view(user):
            return {"exception": f"User cannot access document containing chunk {chunk_id}!"}

        center_num = central.chunk_number
        low = center_num - adjacent_chunks
        high = center_num + adjacent_chunks
        window = TextChunk.objects.filter(
            doc_id=central.doc_id,
            chunk_number__in=range(low, high + 1),
        ).order_by('chunk_number')

        blob = "".join(chunk.content for chunk in window)
        return {
            "result": f"chunk_numbers:{window.first().chunk_number}"
                      f" -> {window.last().chunk_number}\n\n{blob}"
        }

    return more_context


def get_dual_retrieve_func(user: User, col_ref: CollectionsRef, chat_ref: ChatRef) -> LLMTool:
    @llm_tool(
        param_descs={
            "search_string": "The query string.",
            "top_k": "Number of results per source.",
            "use_zotero": "Include Zotero library (True/False).",
        },
        required=['search_string', 'top_k'],
        for_whom='assistant',
    )
    def dual_retrieve(search_string: str, top_k: int, use_zotero: bool = True) -> ToolResultDict:
        """
        Search both local documents and the Zotero library using vector search.
        """
        print(f"dual_retrieve called with: {search_string}, top_k={top_k}, use_zotero={use_zotero}")
        results = {"Local Documents": {}, "Zotero Library": {}}

        if use_zotero:
            try:
                print("Starting Zotero search")
                
                # Get client from class method
                if not hasattr(chat_ref.chat, 'zotero_client') or chat_ref.chat.zotero_client is None:
                    print("WARNING: Zotero client not initialized in dual_retrieve!")
                    chat_ref.chat.zotero_client = ChatConsumer.get_zotero_client()
                
                client = chat_ref.chat.zotero_client
                
                # Verify the client is working
                if client is None:
                    results["Zotero Library"] = {"error": "Zotero client unavailable"}
                    return {"result": results}  # Early return to avoid exceptions
            except Exception as e:
                print(f"Error initializing Zotero client: {str(e)}")
                results["Zotero Library"] = {"error": f"Error initializing Zotero: {str(e)}"}

        # Local search (vector search on local documents)
        try:
            print("Starting local document search")
            docs = Collection.get_user_accessible_documents(
                user, Collection.objects.filter(id__in=col_ref.collections)
            )
            if docs:
                print(f"Found {len(docs)} accessible documents")
                _, _, local_chunks = TextChunk.text_chunk_search(search_string, top_k, docs)
                results["Local Documents"] = {
                    f"[Result {i+1}] -- {chunk.document.title} chunk#: {chunk.chunk_number} chunk_id:{chunk.id}":
                    chunk.content
                    for i, chunk in enumerate(local_chunks)
                }
                print(f"Found {len(local_chunks)} local document chunks")
            else:
                print("No local documents available")
                results["Local Documents"] = {"info": "No local documents available."}
        except Exception as e:
            print(f"Error in local search: {str(e)}")
            results["Local Documents"] = {"error": str(e)}

        # Zotero search
        if use_zotero:
            try:
                print("Starting Zotero search")
                
                # First search Zotero by keyword - use existing client
                if hasattr(chat_ref.chat, 'zotero_client'):
                    client = chat_ref.chat.zotero_client
                    print(f"Searching Zotero for: {search_string}")
                    zotero_items = client.search(search_string, limit=top_k)
                    print(f"Found {len(zotero_items)} Zotero items")
                    
                    zotero_results = {}
                    
                    for i, item in enumerate(zotero_items):
                        try:
                            item_key = item['key']
                            title = item['data'].get('title', 'Untitled')
                            print(f"Processing item {i+1}: {title}")
                            
                            # Check if this item has embeddings
                            has_embeddings = ZoteroTextChunk.objects.filter(item_key=item_key).exists()
                            
                            if has_embeddings:
                                print(f"Found embeddings for {item_key}")
                                # Get chunks from vector database
                                chunks = ZoteroTextChunk.objects.filter(item_key=item_key)[:top_k]
                                for j, chunk in enumerate(chunks):
                                    key = f"[Zotero {i+1}-{j+1}] -- {title} chunk#: {chunk.chunk_number}"
                                    zotero_results[key] = chunk.content
                            else:
                                print(f"No embeddings for {item_key}, checking if it's a PDF")
                                # Check if it's a PDF that needs processing
                                item_type = item.get('data', {}).get('itemType')
                                if item_type == 'attachment':
                                    content_type = item.get('data', {}).get('contentType', '')
                                    if 'pdf' in content_type.lower():
                                        print(f"PDF found, triggering processing for {item_key}")
                                        # Trigger processing asynchronously
                                        client.process_pdf_background(item_key)
                                        key = f"[Zotero {i+1}] -- {title}"
                                        zotero_results[key] = "PDF processing started. Please check back in a few moments."
                                    else:
                                        print(f"Non-PDF attachment: {content_type}")
                                else:
                                    print(f"Not an attachment: {item_type}")
                                    # Try to get children attachments
                                    attachments = client.zot.children(item_key)
                                    for att in attachments:
                                        att_type = att.get('data', {}).get('contentType', '')
                                        if 'pdf' in att_type.lower():
                                            att_key = att['key']
                                            print(f"Found PDF attachment {att_key}, triggering processing")
                                            client.process_pdf_background(att_key)
                                            key = f"[Zotero {i+1}] -- {title}"
                                            zotero_results[key] = "PDF processing started. Please check back in a few moments."
                                            break
                                
                                # If no PDF found, still get some metadata
                                if title not in [k for k in zotero_results.keys() if title in k]:
                                    key = f"[Zotero {i+1}] -- {title}"
                                    zotero_results[key] = item['data'].get('abstractNote', 'No PDF available for this item.')
                        
                        except Exception as item_err:
                            print(f"Error processing item {i+1}: {str(item_err)}")
                            import traceback
                            traceback.print_exc()
                    
                    results["Zotero Library"] = zotero_results
                else:
                    results["Zotero Library"] = {"error": "Zotero client not available"}
                    
            except Exception as e:
                print(f"Error in Zotero search: {str(e)}")
                import traceback
                traceback.print_exc()
                results["Zotero Library"] = {"error": str(e)}
        else:
            print("Zotero search was disabled")
            results["Zotero Library"] = {"info": "Zotero search disabled."}

        print("dual_retrieve completed successfully")
        return {"result": results}

    return dual_retrieve

def get_zotero_item_func(chat_ref: ChatRef) -> LLMTool:
    @llm_tool(
        for_whom='assistant',
        required=['item_key'],
        param_descs={'item_key': 'The Zotero item key to retrieve'},
    )
    def get_zotero_item(item_key: str) -> ToolResultDict:
        """
        Retrieve detailed metadata for a Zotero item.
        """
        print(f"get_zotero_item called for key: {item_key}")
        cache_key = f"zotero_item_response:{item_key}"
        cached = cache.get(cache_key)
        if cached:
            print(f"Using cached response for {item_key}")
            return cached

        try:
            # Use the class method to get the shared client
            if not hasattr(chat_ref.chat, 'zotero_client') or chat_ref.chat.zotero_client is None:
                print("WARNING: Zotero client not initialized!")
                chat_ref.chat.zotero_client = ChatConsumer.get_zotero_client()
                
            metadata = chat_ref.chat.zotero_client.get_item_metadata(item_key)
 
            data = metadata.get('data', {})

            # Return only metadata
            result = {
                "result": {
                    "metadata": {
                        "title": data.get('title', 'Unknown'),
                        "authors": ", ".join(
                            f"{c.get('firstName','')} {c.get('lastName','')}"
                            for c in data.get('creators', [])
                        ),
                        "publication": data.get('publicationTitle', ''),
                        "date": data.get('date', ''),
                        "DOI": data.get('DOI', ''),
                        "URL": data.get('url', ''),
                        "abstract": data.get('abstractNote', ''),
                    }
                }
            }

            cache.set(cache_key, result, 3600)
            print(f"Successfully retrieved metadata for {item_key}")
            return result

        except Exception as e:
            print(f"Error retrieving Zotero item {item_key}: {e}")
            import traceback
            traceback.print_exc()
            return {"exception": f"Error retrieving Zotero item: {e}"}

    return get_zotero_item


def get_zotero_extract_func(chat_ref: ChatRef) -> LLMTool:
    @llm_tool(
        for_whom='assistant',
        required=['item_key', 'page_start', 'page_count'],
        param_descs={
            'item_key': 'The Zotero item key to retrieve',
            'page_start': 'Starting page (0-indexed)',
            'page_count': 'Number of pages to extract (max 3)'
        },
    )
    def get_zotero_extract(item_key: str, page_start: int = 0, page_count: int = 3) -> ToolResultDict:
        """
        Extract specific pages from Zotero PDF attachment.
        """
        print(f"get_zotero_extract called for key: {item_key}, pages {page_start}-{page_start+page_count-1}")
        # Limit page count to avoid performance issues
        page_count = min(page_count, 3)
        
        try:
            if not hasattr(chat_ref.chat, 'zotero_client') or chat_ref.chat.zotero_client is None:
                print("WARNING: Zotero client not initialized!")
                chat_ref.chat.zotero_client = ChatConsumer.get_zotero_client()
            
            # First, check if the cached processed text is available
            status = cache.get(f"zotero_pdf_status:{item_key}")
            if status == "complete":
                print(f"Using cached PDF pages for {item_key}")
                title = None
                text = []
                
                # Get title from metadata
                try:
                    metadata = chat_ref.chat.zotero_client.get_item_metadata(item_key)
                    title = metadata.get('data', {}).get('title', 'Unknown')
                except Exception as e:
                    print(f"Error getting metadata: {e}")
                    title = "Unknown Title"
                
                # Get pages from cache
                for i in range(page_start, page_start + page_count):
                    page_text = cache.get(f"zotero_page:{item_key}:{i}")
                    if page_text:
                        text.append(f"--- PAGE {i+1} ---\n{page_text}")
                    else:
                        break
                
                if text:
                    return {
                        "result": {
                            "title": title,
                            "pages": f"{page_start+1} to {page_start+len(text)}",
                            "content": "\n\n".join(text)
                        }
                    }
            
            # Get the item metadata to check its type
            item = chat_ref.chat.zotero_client.get_item_metadata(item_key)
            item_type = item.get('data', {}).get('itemType')
            title = item.get('data', {}).get('title', 'Unknown')
            
             
            
        except Exception as e:
            print(f"Error extracting from PDF {item_key}: {e}")
            import traceback
            traceback.print_exc()
            return {"exception": f"Error extracting from PDF: {e}"}

    return get_zotero_extract


def get_zotero_pdf_status_func(chat_ref: ChatRef) -> LLMTool:
    @llm_tool(
        for_whom='assistant',
        required=['item_key'],
        param_descs={'item_key': 'The Zotero item key to check'},
    )
    def get_zotero_pdf_status(item_key: str) -> ToolResultDict:
        """
        Check the processing status of a Zotero PDF.
        """
        print(f"get_zotero_pdf_status called for key: {item_key}")
        status = cache.get(f"zotero_pdf_status:{item_key}")
        pages = cache.get(f"zotero_pdf_pages:{item_key}")
        
        if not status:
            print(f"No status found for {item_key}, starting processing")
            # Trigger processing if not started
            if not hasattr(chat_ref.chat, 'zotero_client') or chat_ref.chat.zotero_client is None:
                print("WARNING: Zotero client not initialized!")
                chat_ref.chat.zotero_client = ChatConsumer.get_zotero_client()
                
            if chat_ref.chat.zotero_client.process_pdf_background(item_key):
                return {"result": {"status": "processing_started", "message": "PDF processing has been started."}}
            else:
                return {"result": {"status": "error", "message": "Failed to start PDF processing."}}
        
        print(f"Status for {item_key}: {status}")
        if status == "complete":
            return {"result": {"status": "complete", "total_pages": pages, "message": f"PDF processing complete. {pages} pages extracted."}}
        elif status.startswith("processing_"):
            return {"result": {"status": "processing", "message": f"PDF processing in progress: {status.replace('processing_', '')}"}}
        else:
            return {"result": {"status": status, "message": f"PDF status: {status}"}}
    
    return get_zotero_pdf_status

def get_zotero_list_func(chat_ref: ChatRef) -> LLMTool:
    @llm_tool(
        for_whom='assistant',
        required=[],
        param_descs={},
    )
    def list_zotero_items() -> ToolResultDict:
        """
        List all Zotero PDFs that have been processed and embedded.
        """
        try:
            # Update this client check to use the class method
            if not hasattr(chat_ref.chat, 'zotero_client') or chat_ref.chat.zotero_client is None:
                print("WARNING: Zotero client not initialized in list_zotero_items!")
                chat_ref.chat.zotero_client = ChatConsumer.get_zotero_client()
                
            # Get all unique item keys from the database
            item_keys = ZoteroTextChunk.objects.values_list('item_key', flat=True).distinct()
            
            results = {}
            client = chat_ref.chat.zotero_client
            
            for i, item_key in enumerate(item_keys):
                try:
                    metadata = client.get_item_metadata(item_key)
                    title = metadata.get('data', {}).get('title', 'Unknown')
                    chunk_count = ZoteroTextChunk.objects.filter(item_key=item_key).count()
                    
                    results[f"[{i+1}] {title}"] = {
                        "item_key": item_key,
                        "chunks": chunk_count,
                        "status": "ready"
                    }
                except Exception as e:
                    results[f"[{i+1}] Item {item_key}"] = {
                        "item_key": item_key,
                        "status": f"error: {str(e)}"
                    }
            
            return {"result": results}
            
        except Exception as e:
            return {"exception": str(e)}
    
    return list_zotero_items


def get_zotero_search_func(chat_ref: ChatRef) -> LLMTool:
    @llm_tool(
        for_whom='assistant',
        required=['item_identifier', 'query'],
        param_descs={
            'item_identifier': 'The Zotero item title, filename, or item key to search within',
            'query': 'The text to search for in the PDF'
        },
    )
    def search_zotero_pdf(item_identifier: str, query: str) -> ToolResultDict:
        """
        Search within an extracted Zotero PDF for specific content.
        Automatically finds the item key based on title, filename, or existing item key.
        """
        print(f"search_zotero_pdf called for identifier: {item_identifier}, query: {query}")
        
         
        from django.db.models import Q
        
        # Try to find the real item key if the identifier looks like a filename/title
        item_key = item_identifier
        
        # Check if we can find this item in our database
        if not item_key.isalnum() or len(item_key) != 8:  # Likely not a valid Zotero key
            print(f"Searching for item key using identifier: {item_identifier}")
            try:
                # Look for the item in embedded chunks first
                chunks = ZoteroTextChunk.objects.filter(
                    Q(content__icontains=item_identifier)
                ).order_by('item_key')
                
                if chunks.exists():
                    item_key = chunks.first().item_key
                    print(f"Found item key from database: {item_key}")
                else:
                    # Search Zotero for the item
                    if not hasattr(chat_ref.chat, 'zotero_client') or chat_ref.chat.zotero_client is None:
                        print("WARNING: Zotero client not initialized in search_zotero_pdf!")
                        chat_ref.chat.zotero_client = ChatConsumer.get_zotero_client()
                        
                    client = chat_ref.chat.zotero_client
                    # Clean the identifier for searching
                    search_term = item_identifier
                    if ' - ' in item_identifier:
                        # Extract title from filename
                        search_term = item_identifier.split(' - ')[-1].replace('.pdf', '')
                    
                    items = client.search(search_term, limit=5)
                    
                    # Find matching item
                    for item in items:
                        title = item.get('data', {}).get('title', '')
                        if title and (search_term.lower() in title.lower() or 
                                    any(part.lower() in title.lower() for part in search_term.split())):
                            item_key = item['key']
                            print(f"Found matching item with key: {item_key}")
                            break
                    else:
                        return {"result": {"status": "error", "message": f"Could not find item matching '{item_identifier}'"}}
            except Exception as e:
                print(f"Error finding item: {e}")
                import traceback
                traceback.print_exc()
                return {"result": {"status": "error", "message": f"Error finding item: {str(e)}"}}
        
        # First, check if the PDF is already processed
        chunks_exist = ZoteroTextChunk.objects.filter(item_key=item_key).exists()
        print(f"Chunks exist for {item_key}: {chunks_exist}")
        
        if chunks_exist:
            # PDF is already processed, search within it
            print(f"Searching within existing chunks for {item_key}")
            try:
                chunks = ZoteroTextChunk.objects.filter(item_key=item_key)
                
                # Perform text search on chunks
                query_terms = query.lower().split()
                matching_chunks = []
                
                for chunk in chunks:
                    if all(term in chunk.content.lower() for term in query_terms):
                        matching_chunks.append(chunk)
                
                if matching_chunks:
                    # Format results
                    content = []
                    for i, chunk in enumerate(matching_chunks[:5]):  # Limit to 5 chunks
                        preview = chunk.content
                        content.append(f"--- Chunk {chunk.chunk_number} ---\n{preview}")
                    
                    return {
                        "result": {
                            "status": "success",
                            "matching_chunks": len(matching_chunks),
                            "content": "\n\n".join(content)
                        }
                    }
                else:
                    # No matches found, trigger extraction to get more content
                    print(f"No matches found for '{query}', extracting more content")
                    # Trigger PDF extraction
                    if not hasattr(chat_ref.chat, 'zotero_client') or chat_ref.chat.zotero_client is None:
                        chat_ref.chat.zotero_client = ChatConsumer.get_zotero_client()
                    
                    # Extract key pages that might contain what we're looking for
                    
                    extract_result = chat_ref.chat.zotero_client.extract_pdf_page(item_key, 2, 3)
                    
                    if extract_result:
                        return {
                            "result": {
                                "status": "direct_extract",
                                "message": f"Found potential content from direct extraction:",
                                "content": extract_result
                            }
                        }
                    else:
                        return {"result": {"status": "no_matches", "message": f"No matches found for '{query}' in the document."}}
            except Exception as e:
                print(f"Error searching content: {e}")
                import traceback
                traceback.print_exc()
                return {"result": {"status": "error", "message": f"Error searching content: {str(e)}"}}
        else:
            # PDF is not processed yet, start extraction
            print(f"No chunks found, starting extraction for {item_key}")
            try:
                if not hasattr(chat_ref.chat, 'zotero_client') or chat_ref.chat.zotero_client is None:
                    print("WARNING: Zotero client not initialized!")
                    chat_ref.chat.zotero_client = ChatConsumer.get_zotero_client()
                
                # Direct extraction approach
                extract_result = chat_ref.chat.zotero_client.extract_pdf_page(item_key, 2, 3)
                
                if extract_result:
                    print(f"Successfully extracted content directly")
                    return {
                        "result": {
                            "status": "direct_extract",
                            "message": f"Direct extraction successful while processing is started:",
                            "content": extract_result
                        }
                    }
                
                # Also trigger the background processing for future queries
                chat_ref.chat.zotero_client.process_pdf_background(item_key)
                
                # If direct extraction failed, let the user know processing has started
                return {
                    "result": {
                        "status": "processing_started",
                        "message": "PDF processing has been started. The PDF may not be fully indexed yet. Please try again in a few moments or try a different query."
                    }
                }
            except Exception as e:
                print(f"Error processing PDF: {e}")
                import traceback
                traceback.print_exc()
                return {"result": {"status": "error", "message": f"Error processing PDF: {str(e)}"}}
    
    return search_zotero_pdf

     
def get_zotero_embedding_status_func(chat_ref: ChatRef) -> LLMTool:
    @llm_tool(
        for_whom='assistant',
        required=['item_key'],
        param_descs={'item_key': 'The Zotero item key to check'}
    )
    def check_zotero_embedding_status(item_key: str) -> ToolResultDict:
        """Check if Zotero PDF embeddings are ready"""
        try:
             
            if not hasattr(chat_ref.chat, 'zotero_client') or chat_ref.chat.zotero_client is None:
                print("WARNING: Zotero client not initialized in check_zotero_embedding_status!")
                chat_ref.chat.zotero_client = ChatConsumer.get_zotero_client()
                
            status = cache.get(f"zotero_embedding_status:{item_key}")
            chunk_count = ZoteroTextChunk.objects.filter(item_key=item_key).count()
            
            if status == "complete" and chunk_count > 0:
                return {
                    "result": {
                        "status": "ready",
                        "chunk_count": chunk_count,
                        "message": "Vector search ready"
                    }
                }
            elif status and status.startswith("error"):
                return {
                    "result": {
                        "status": "error",
                        "message": status
                    }
                }
            else:
                return {
                    "result": {
                        "status": "processing",
                        "message": "Embeddings being created, please wait"
                    }
                }
                
        except Exception as e:
            return {"exception": str(e)}
    
    return check_zotero_embedding_status   


class ChatConsumer(AsyncWebsocketConsumer):
    llm_if: LLMInterface = apps.get_app_config('aquillm').llm_interface
    db_convo: Optional[WSConversation] = None
    convo: Optional[Conversation] = None
    tools: List[LLMTool] = []
    user: Optional[User] = None
    dead: bool = False
    col_ref = CollectionsRef([])
    _zotero_client_instance = None

    @classmethod
    def get_zotero_client(cls):
        """Return the singleton Zotero client instance"""
        if cls._zotero_client_instance is None:
            print("Creating shared Zotero client instance")
            cls._zotero_client_instance = ZoteroClient()
        return cls._zotero_client_instance

    @database_sync_to_async
    def __save(self):
        assert self.db_convo is not None
        self.db_convo.convo = to_jsonable_python(self.convo)
        if len(self.db_convo.convo['messages']) >= 2 and not self.db_convo.name:
            self.db_convo.set_name()
        self.db_convo.save()

    @database_sync_to_async
    def __get_convo(self, convo_id: int, user: User):
        convo = WSConversation.objects.filter(id=convo_id).first()
        if convo and convo.owner == user:
            return convo
        return None

    @database_sync_to_async
    def __get_all_user_collections(self):
        self.col_ref.collections = [
            perm.collection.id
            for perm in CollectionPermission.objects.filter(user=self.user)
        ]

    async def connect(self):
        print("WebSocket connecting...")
        # Initialize the Zotero client once globally
        try:
            self.zotero_client = self.__class__.get_zotero_client()   
            print("Zotero client initialized or retrieved successfully")
        except Exception as e:
            print(f"Error with Zotero client: {e}")
            import traceback
            traceback.print_exc()
            # Still continue even if Zotero client fails
        
        await self.accept()
        self.user = self.scope['user']
        await self.__get_all_user_collections()

        # Create chat_ref  
        chat_ref = ChatRef(self)
        self.tools = [
            test_function,
            get_dual_retrieve_func(self.user, self.col_ref, chat_ref),
            get_more_context_func(self.user),
            get_document_ids_func(self.user, self.col_ref),
            get_whole_document_func(self.user, chat_ref),
            get_search_single_document_func(self.user),
            get_zotero_item_func(chat_ref),
            get_zotero_extract_func(chat_ref),
            get_zotero_pdf_status_func(chat_ref),
            get_zotero_search_func(chat_ref),
            get_zotero_vector_search(chat_ref),
            get_zotero_embedding_status_func(chat_ref),
            get_zotero_list_func(chat_ref),
        ]


        convo_id = self.scope['url_route']['kwargs']['convo_id']
        self.db_convo = await self.__get_convo(convo_id, self.user)
        if self.db_convo is None:
            self.dead = True
            await self.send(text_data='{"exception":"Invalid chat_id"}')
            return

        try:
            print(f"Loading conversation {convo_id}")
            self.convo = Conversation.model_validate(self.db_convo.convo)
            self.convo.rebind_tools(self.tools)
            print("Spinning LLM interface")
            await self.llm_if.spin(
                self.convo,
                max_func_calls=5,
                max_tokens=2048,
                send_func=lambda c: self._send_and_save(c),
            )
        except OverloadedError:
            self.dead = True
            await self.send(text_data='{"exception":"LLM provider overloaded."}')
        except Exception as e:
            print(f"Exception in connect: {str(e)}")
            import traceback
            traceback.print_exc()
            if DEBUG:
                raise
            await self.send(text_data='{"exception":"Server error."}')

    async def _send_and_save(self, convo: Conversation):
        try:
            await aclose_old_connections()
            self.convo = convo
            await self.send(text_data=dumps({"conversation": to_jsonable_python(convo)}))
            await self.__save()
        except Exception as e:
            # Log error but don't crash
            print(f"Error in send_and_save: {e}")
            self.dead = True  # Mark as dead so no more processing happens

    async def receive(self, text_data):
        if self.dead:
            return

        data = loads(text_data)
        action = data.get('action')

        if action == 'append':
            await self._handle_append(data)
        elif action == 'rate':
            await self._handle_rate(data)
        else:
            await self.send(text_data='{"exception":"Invalid action"}')
            return

        await self.llm_if.spin(
            self.convo,
            max_func_calls=5,
            max_tokens=2048,
            send_func=lambda c: self._send_and_save(c),
        )

    async def _handle_append(self, data: dict):
        self.col_ref.collections = data['collections']
        self.convo += UserMessage.model_validate(data['message'])
        self.convo[-1].tools = self.tools
        self.convo[-1].tool_choice = ToolChoice(type='auto')
        await self.__save()

    async def _handle_rate(self, data: dict):
        try:
            msg = next(
                (m for m in self.convo if str(m.message_uuid) == data['uuid']), None
            )
            if msg:
                msg.rating = data['rating']
                await self.__save()
        except Exception as e:
            print(f"Error in _handle_rate: {e}")
            self.dead = True  # Mark as dead so no more processing happens