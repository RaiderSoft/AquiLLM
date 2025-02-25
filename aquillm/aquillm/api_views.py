import requests
import logging
import gzip
import tarfile
import io
import chardet
from xml.dom import minidom

from django.core.files.base import ContentFile

from .models import PDFDocument, TeXDocument, Collection, CollectionPermission
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from django.shortcuts import get_object_or_404

from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.db import DatabaseError
logger = logging.getLogger(__name__)

# helper func, not a view
def insert_one_from_arxiv(arxiv_id, collection, user):

    def save_pdf_doc(content, title):
        doc = PDFDocument(
            collection=collection,
            title=title,
            ingested_by=user
        )
        doc.pdf_file.save(f'arxiv:{arxiv_id}.pdf', ContentFile(content), save=False)
        doc.save()

    status = {"message": "", "errors": []}
    tex_req = requests.get('https://arxiv.org/src/' + arxiv_id)
    pdf_req = requests.get('https://arxiv.org/pdf/' + arxiv_id)
    metadata_req = requests.get('http://export.arxiv.org/api/query?id_list=' + arxiv_id)

    if metadata_req.status_code == 404 or (tex_req.status_code == 404 and pdf_req.status_code == 404):
        status["errors"].append("ERROR: 404 from ArXiv, is the DOI correct?")
    elif (tex_req.status_code not in [200, 404] or 
          pdf_req.status_code not in [200, 404] or 
          metadata_req.status_code not in [200, 404]):
        error_str = (
            f"ERROR -- DOI {arxiv_id}: LaTeX status code {tex_req.status_code}, "
            f"PDF status code {pdf_req.status_code}, metadata status code {metadata_req.status_code}"
        )
        logger.error(error_str)
        status["errors"].append(error_str)
    else:
        # Parse metadata to extract the title.
        xmldoc = minidom.parseString(metadata_req.content)
        title = ' '.join(
            xmldoc.getElementsByTagName('entry')[0]
                 .getElementsByTagName('title')[0]
                 .firstChild.data.split() # type: ignore
        )
        
        # Process the /src/ endpoint if it returned 200.
        if tex_req.status_code == 200:
            # Check if the content appears to be a PDF.
            if tex_req.content.startswith(b'%PDF'):
                status["message"] += f"Got PDF for {arxiv_id}\n"
                save_pdf_doc(tex_req.content, title)
            else:
                status["message"] += f"Got LaTeX source for {arxiv_id}\n"
                tgz_io = io.BytesIO(tex_req.content)
                tex_str = ""
                # Extract the tar.gz archive containing the LaTeX source.
                with gzip.open(tgz_io, 'rb') as gz:
                    with tarfile.open(fileobj=gz) as tar: # type: ignore
                        for member in tar.getmembers():
                            if member.isfile() and member.name.endswith('.tex'):
                                f = tar.extractfile(member)
                                if f:
                                    tex_bytes = f.read()
                                    encoding = chardet.detect(tex_bytes)['encoding']
                                    if not encoding:
                                        raise ValueError("Could not detect encoding of LaTeX source")
                                    content = tex_bytes.decode(encoding)
                                    tex_str += content + '\n\n'
                doc = TeXDocument(
                    collection=collection,
                    title=title,
                    full_text=tex_str,
                    ingested_by=user
                )
                # Optionally attach the PDF if available.
                if pdf_req.status_code == 200:
                    status["message"] += f"Got PDF for {arxiv_id}\n"
                    doc.pdf_file.save(f'arxiv:{arxiv_id}.pdf', ContentFile(pdf_req.content), save=False)
                doc.save()
        # If the /src/ endpoint didn't work but the PDF endpoint did, use that.
        elif pdf_req.status_code == 200:
            status["message"] += f"Got PDF for {arxiv_id}\n"
            save_pdf_doc(pdf_req.content, title)
            
    return status



@login_required
@require_http_methods(["POST"])
def ingest_arxiv(request):
    user = request.user
    arxiv_id = request.POST.get('arxiv_id')
    collection = Collection.objects.filter(pk=request.POST.get('collection')).first()
    if not collection or not collection.user_can_edit(user):
        return JsonResponse({'error': 'Collection does not exist, was not provided, or user does not have permission to edit this collection'}, status=403)
    if not arxiv_id:
        return JsonResponse({'error': 'No arXiv ID provided'}, status=400)
    try:
        status = insert_one_from_arxiv(arxiv_id, collection, user)
        if status["errors"]:
            return JsonResponse({'error': status["errors"]}, status=500)
        return JsonResponse({'message': status["message"]})
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        return JsonResponse({'error': 'Database error occurred while saving document'}, status=500)

@login_required
@require_http_methods(["POST"])
def ingest_pdf(request):
    user = request.user
    pdf_file = request.FILES.get('pdf_file')
    title = request.POST.get('title')
    collection = Collection.objects.filter(pk=request.POST.get('collection')).first()
    if not collection or not collection.user_can_edit(user):
        return JsonResponse({'error': 'Collection does not exist, was not provided, or user does not have permission to edit this collection'}, status=403)
    if not pdf_file:
        return JsonResponse({'error': 'No PDF file provided'}, status=400)
    if not title:
        return JsonResponse({'error': 'No title provided'}, status=400)
    try:
        FileExtensionValidator(['pdf'])(pdf_file)
    except ValidationError as e:
        return JsonResponse({'error': 'Invalid file extension. Only PDF files are allowed.'}, status=400)
    doc = PDFDocument(
        collection = collection,
        title = pdf_file.name,
        ingested_by = user
    )
    doc.pdf_file = pdf_file
    try:
        doc.save()
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        return JsonResponse({'error': 'Database error occurred while saving PDFDocument'}, status=500)
    return JsonResponse({'status_message': 'Success'})