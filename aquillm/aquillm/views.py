from django.shortcuts import render, redirect
from django.apps import apps

from django.core.files.base import ContentFile
import logging
import re
import io
import gzip
import tarfile
from xml.dom import minidom

from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from pgvector.django import L2Distance
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from .forms import SearchForm, ArXiVForm
from .models import TextChunk, TeXDocument, PDFDocument, Collection, LLMConversation
import requests

from django.http import JsonResponse

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'aquillm/index.html')




@login_required
def search(request):
    


    vector_results = []
    trigram_results = []
    reranked_results = []
    error_message = None

    if request.method == 'POST':
        form = SearchForm(request.user, request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            top_k = form.cleaned_data['top_k']
            collections = form.cleaned_data['collections']
            searchable_docs = Collection.get_user_accessible_documents(request.user, collections=collections)
            vector_results, trigram_results, reranked_results = TextChunk.text_chunk_search(query, top_k, searchable_docs)
        else:
            error_message = "Invalid form submisison"
    else:
        form = SearchForm(request.user)

    context = {
        'form': form,
        'reranked_results': reranked_results,
        'vector_results': vector_results,
        'trigram_results': trigram_results,
        'error_message': error_message
    }

    return render(request, 'aquillm/search.html', context)


# def llm_convo(request):


#     reranked_results = []
#     error_message = None
#     llm_response = None
#     if request.method == 'POST':
#         form = SearchForm(request.user, request.POST)
#         if form.is_valid():
#             query = form.cleaned_data['query']
#             top_k = form.cleaned_data['top_k']
#             collections = form.cleaned_data['collections']
#             searchable_docs = get_user_accessible_documents(request.user, collections=collections)
#             _, _, reranked_results = text_chunk_search(query, top_k, searchable_docs)
#         else:
#             error_message = "Invalid form submisison"
#     else:
#         form = SearchForm(request.user)

#     context = {
#         'form': form,
#         'reranked_results': reranked_results,
#         'vector_results': vector_results,
#         'trigram_results': trigram_results,
#         'error_message': error_message
#     }

#     return render(request, 'aquillm/llm_convo.html', context)


@login_required
def raw_convo(request, convo_id):
    convo = get_object_or_404(LLMConversation, pk=convo_id)
    if convo.owner != request.user:
        return HttpResponseForbidden("User does not own this conversation")
    context = {'conversation': convo}
    return render(request, 'aquillm/raw_convo.html', context)

@login_required
def convo(request, convo_id):
    convo = get_object_or_404(LLMConversation, pk=convo_id)
    if convo.owner != request.user:
        return HttpResponseForbidden("User does not own this conversation")
   
    return render(request, 'aquillm/convo.html', {'convo_id' : convo_id,
                                                  'form' : SearchForm(request.user)})

@require_http_methods(['POST'])
@login_required
def send_message(request, convo_id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        convo = get_object_or_404(LLMConversation, pk=convo_id)
        if convo.owner != request.user:
            return HttpResponseForbidden("User does not own this conversation")
        form = SearchForm(request.user, request.POST)
        if form.is_valid():
            collections = form.cleaned_data['collections']
            content = form.cleaned_data['query']
            top_k = form.cleaned_data['top_k']
            docs = Collection.get_user_accessible_documents(request.user, collections)
            convo = convo.send_message(content, top_k, docs)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': form.errors})
    logger.error(f"Wrong x-requested-with: {request.headers.get('x-requested-with')}")
    return JsonResponse({'success': False, 'error': 'Invalid Request'})

@login_required
def user_conversations(request):
    conversations = LLMConversation.objects.filter(owner=request.user).order_by('-updated_at')
    return render(request, 'aquillm/user_conversations.html', {'conversations': conversations})

@login_required
def new_convo(request):
    convo = LLMConversation(owner=request.user) # TODO: let user set system prompt
    convo.save()
    return redirect('convo', convo_id=convo.id)

def insert_one_from_arxiv(arxiv_id, collection):
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
                collection = collection,
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
                collection = collection,
                title = title
            )
            doc.pdf_file.save(f'arxiv:{arxiv_id}.pdf', ContentFile(pdf_req.content), save=False)
            doc.save()
    return status_message




@login_required
def insert_arxiv(request):
    status_message = None
    if request.method == 'POST':
        form = ArXiVForm(request.user, request.POST)
        if form.is_valid():
            arxiv_id = re.sub(r'[^\d.]', '', form.cleaned_data['arxiv_id']).lstrip('.')
            collection = Collection.objects.get(id=form.cleaned_data['collection'])
            status_message = insert_one_from_arxiv(arxiv_id, collection)
    else:
        form = ArXiVForm(request.user)

    context = {
        'status_message' : status_message,
        'form' : form
    }

    return render(request, 'aquillm/insert_arxiv.html', context)