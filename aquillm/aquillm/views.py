from django.shortcuts import render
from django.apps import apps
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Case, When
from django.db import DatabaseError
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
import logging
import re
import io
import gzip
import tarfile
from xml.dom import minidom

logger = logging.getLogger(__name__)


from pgvector.django import L2Distance


from .forms import SearchForm, ArXiVForm
from .models import TextChunk, TeXDocument, PDFDocument

import requests

def index(request):
    return render(request, 'aquillm/index.html')


def search(request):
    
    def get_embedding(query):
        cohere = apps.get_app_config('aquillm').cohere_client
        response = cohere.embed(
            texts=[query],
            model="embed-english-v3.0",
            input_type="search_query"
        )
        return response.embeddings[0]
    
    def rerank(query, chunks, top_k):
        cohere = apps.get_app_config('aquillm').cohere_client
        response = cohere.rerank(
            model="rerank-english-v3.0",
            query=query,
            documents=list([{"content": chunk.content, "id": chunk.pk} for chunk in chunks]),
            rank_fields=['content'],
            top_n=top_k,
            return_documents=True 
        )
        #breakpoint()
        ranked_list = list([result.document.id for result in response.results])
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ranked_list)])
        return TextChunk.objects.filter(pk__in=ranked_list).order_by(preserved)

    
    vector_results = []
    trigram_results = []
    reranked_results = []
    error_message = None

    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            top_k = form.cleaned_data['top_k']
            vector_top_k = apps.get_app_config('aquillm').vector_top_k
            trigram_top_k = apps.get_app_config('aquillm').trigram_top_k

            try:
              
                vector_results = TextChunk.objects.order_by(L2Distance('embedding', get_embedding(query)))[:vector_top_k]
                trigram_results = TextChunk.objects.annotate(similarity = TrigramSimilarity('content', query)
                ).filter(similarity__gt=0.000001).order_by('-similarity')[:trigram_top_k]

                for chunk in vector_results | trigram_results:
                    content_type = chunk.content_type
                    model = content_type.model_class()
                    chunk.document = model.objects.get(id=chunk.object_id)

                reranked_results = rerank(query, vector_results | trigram_results, top_k)
            except DatabaseError as e:
                logger.error(f"Database error during search: {str(e)}")
                error_message = "An error occurred while searching the database. Please try again later."
            except ValidationError as e:
                logger.error(f"Validation error during search: {str(e)}")
                error_message = "Invalid search parameters. Please check your input and try again."
            except Exception as e:
                logger.error(f"Unexpected error during search: {str(e)}")
                error_message = "An unexpected error occurred. Please try again later."
        else:
            error_message = "Invalid form submisison"
    else:
        form = SearchForm()

    context = {
        'form': form,
        'reranked_results': reranked_results,
        'vector_results': vector_results,
        'trigram_results': trigram_results,
        'error_message': error_message
    }

    return render(request, 'aquillm/search.html', context)

def insert_one_from_arxiv(arxiv_id):
    status_message = ""
    tex_req = requests.get('https://arxiv.org/src/' + arxiv_id)
    pdf_req = requests.get('https://arxiv.org/pdf/' + arxiv_id)
    metadata_req = requests.get('http://export.arxiv.org/api/query?id_list=' + arxiv_id)
    if metadata_req.status_code == 404 or (tex_req.status_code == 404 and pdf_req.status_code == 404):
        status_message += "ERROR: 404 from ArXiv, is the DOI correct?"
    elif tex_req.status_code not in [200, 404] or pdf_req.status_code not in [200, 404] or metadata_req.status_code not in [200, 404]:
        error_str = f"ERROR -- DOI {arxiv_id}: LaTeX status code {tex_req.status_code}, PDF status code {pdf_req.status_code}, metadata status code {metadata_req.status_code}"
        logger.error(error_str)
        status_message += error_str
    else:
        xmldoc = minidom.parseString(metadata_req.content)
        title = ' '.join(xmldoc.getElementsByTagName('entry')[0].getElementsByTagName('title')[0].firstChild.data.split())
        if tex_req.status_code == 200:
            status_message += f"Got LaTeX source for {arxiv_id}\n"
            tgz_io = io.BytesIO(tex_req.content)
            tex_str = ""
            with gzip.open(tgz_io, 'rb') as gz:
                with tarfile.open(fileobj=gz) as tar:
                    for member in tar.getmembers():
                        if member.isfile() and member.name.endswith('.tex'):
                            f = tar.extractfile(member)
                            if f:
                                content = f.read().decode('utf-8')
                                tex_str += content + '\n\n'
            doc = TeXDocument(
                title = title,
                full_text = tex_str
            )
            if pdf_req.status_code == 200:
                status_message += f'Got PDF for {arxiv_id}\n'
                doc.pdf_file.save(f'arxiv:{arxiv_id}.pdf', ContentFile(pdf_req.content), save=False)
            doc.save()
        elif pdf_req.status_code == 200:
            status_message += f'Got PDF for {arxiv_id}\n'
            doc = PDFDocument(
                title = title
            )
            doc.pdf_file.save(f'arxiv:{arxiv_id}.pdf', ContentFile(pdf_req.content), save=False)
            doc.save()
    return status_message



def insert_arxiv(request):
    status_message = None
    if request.method == 'POST':
        form = ArXiVForm(request.POST)
        if form.is_valid():
            arxiv_id = re.sub(r'[^\d.]', '', form.cleaned_data['arxiv_id'])
            status_message = insert_one_from_arxiv(arxiv_id)
    else:
        form = ArXiVForm()

    context = {
        'status_message' : status_message,
        'form' : form
    }

    return render(request, 'aquillm/insert_arxiv.html', context)