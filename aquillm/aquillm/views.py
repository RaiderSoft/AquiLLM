from django.shortcuts import render, redirect
from django.apps import apps

from django.core.files.base import ContentFile
import logging
import re
import io
import gzip
import tarfile
from xml.dom import minidom
from django.db import transaction
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from pgvector.django import L2Distance
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import requires_csrf_token

from .forms import SearchForm, ArXiVForm, PDFDocumentForm, VTTDocumentForm, NewCollectionForm
from .models import TextChunk, TeXDocument, PDFDocument, VTTDocument, Collection, CollectionPermission, LLMConversation, WSConversation, DESCENDED_FROM_DOCUMENT
from . import vtt
from .settings import DEBUG

import requests
from django.http import JsonResponse
from django.forms.models import model_to_dict
import json
logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def index(request):
    return render(request, 'aquillm/index.html')

@login_required
@require_http_methods(['GET'])
def react_test(request):
    return render(request, 'aquillm/react_test.html', {"hello_string": "Hello, world!"})


@require_http_methods(['GET', 'POST'])
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


# helper func, not a view
def get_doc(request, doc_id):
    doc = None
    for t in DESCENDED_FROM_DOCUMENT:
        doc = t.objects.filter(id=doc_id).first()
        if doc:
            break
    if not doc:
        raise Http404("Requested document does not exist")
    if not doc.collection.user_can_view(request.user):
        raise HttpResponseForbidden("You don't have access to the collection containing this document")
    return doc

@require_http_methods(['GET'])
@login_required
def pdf(request, doc_id):
    doc = get_doc(request, doc_id)
    if doc.pdf_file:
        response = HttpResponse(doc.pdf_file, content_type='application/pdf')
        return response
    else:
        raise Http404("Requested document does not have an associated PDF")
    
    
@require_http_methods(['GET'])
@login_required
def document(request, doc_id):
    doc = get_doc(request, doc_id)
    context = {'document': doc}
    return render(request, 'aquillm/document.html', context)


# helper func, not a view
def insert_one_from_arxiv(arxiv_id, collection, user):
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
                full_text = tex_str,
                ingested_by=user
            )
            if pdf_req.status_code == 200:
                status_message += f'Got PDF for {arxiv_id}\n'
                doc.pdf_file.save(f'arxiv:{arxiv_id}.pdf', ContentFile(pdf_req.content), save=False)
            doc.save()
        elif pdf_req.status_code == 200:
            status_message += f'Got PDF for {arxiv_id}\n'
            doc = PDFDocument(
                collection = collection,
                title = title,
                ingested_by=user
            )
            doc.pdf_file.save(f'arxiv:{arxiv_id}.pdf', ContentFile(pdf_req.content), save=False)
            doc.save()
    return status_message



@require_http_methods(['GET', 'POST'])
@login_required
def insert_arxiv(request):
    status_message = None
    if request.method == 'POST':
        form = ArXiVForm(request.user, request.POST)
        if form.is_valid():
            arxiv_id = re.sub(r'[^\d.]', '', form.cleaned_data['arxiv_id']).lstrip('.')
            collection = Collection.objects.get(id=form.cleaned_data['collection'])
            status_message = insert_one_from_arxiv(arxiv_id, collection, request.user)
    else:
        form = ArXiVForm(request.user)

    context = {
        'status_message' : status_message,
        'form' : form
    }

    return render(request, 'aquillm/insert_arxiv.html', context)


@require_http_methods(['GET'])
@login_required
def raw_convo(request, convo_id):
    convo = get_object_or_404(LLMConversation, pk=convo_id)
    if convo.owner != request.user:
        return HttpResponseForbidden("User does not own this conversation")
    context = {'conversation': convo}
    return render(request, 'aquillm/raw_convo.html', context)

@require_http_methods(['GET'])
@login_required
def convo(request, convo_id):
    convo = get_object_or_404(LLMConversation, pk=convo_id)
    if convo.owner != request.user:
        return HttpResponseForbidden("User does not own this conversation")
   
    return render(request, 'aquillm/convo.html', {'conversation': convo,
                                                  'convo_id' : convo_id,
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


@require_http_methods(['GET'])
@login_required
def user_conversations(request):
    conversations = LLMConversation.objects.filter(owner=request.user).order_by('-updated_at')
    return render(request, 'aquillm/user_conversations.html', {'conversations': conversations})

@login_required
def new_convo(request):
    convo = LLMConversation(owner=request.user) # TODO: let user set system prompt
    convo.save()
    return redirect('convo', convo_id=convo.id)


#TODO: make this much nicer
@require_http_methods(['GET', 'POST'])
@login_required
def user_collections(request):
    if request.method == 'POST':
        form = NewCollectionForm(request.POST, user=request.user)
        if form.is_valid():
            data = form.cleaned_data
            name = data['name']
            viewers = data['viewers']
            editors = data['editors']
            admins = data['admins']
            with transaction.atomic():
                col = Collection.objects.create(name=name)
                CollectionPermission.objects.create(user=request.user, collection=col, permission='MANAGE')
                for user in admins:
                    CollectionPermission.objects.create(user=user, collection=col, permission='MANAGE')
                for user in editors:
                    CollectionPermission.objects.create(user=user, collection=col, permission='EDIT')
                for user in viewers:
                    CollectionPermission.objects.create(user=user, collection=col, permission='VIEW')
        else:
            status_message = "Invalid Form Input"
            return render(request, "aquillm/user_collections.html", {'col_perms': colperms, 'form': form, 'status_message': status_message}) 

        return redirect('collection', col_id=col.id)
    else:
        colperms = CollectionPermission.objects.filter(user=request.user)
        form = NewCollectionForm(user=request.user)
        return render(request, "aquillm/user_collections.html", {'col_perms': colperms, 'form': form}) 

@requires_csrf_token
@require_http_methods(['GET'])
@login_required
def get_collections_json(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)

        with transaction.atomic():
            collection = Collection.objects.create(name=name)
            CollectionPermission.objects.create(
                collection=collection,
                user=request.user,
                permission='MANAGE'
            )

            # Handle additional permissions
            for viewer in data.get('viewers', []):
                CollectionPermission.objects.create(
                    collection=collection,
                    user=get_user_model().objects.get(id=viewer),
                    permission='VIEW'
                )
            for editor in data.get('editors', []):
                CollectionPermission.objects.create(
                    collection=collection,
                    user=get_user_model().objects.get(id=editor),
                    permission='EDIT'
                )
            for admin in data.get('admins', []):
                CollectionPermission.objects.create(
                    collection=collection,
                    user=get_user_model().objects.get(id=admin),
                    permission='MANAGE'
                )

            return JsonResponse({
                'id': collection.id,
                'name': collection.name,
                'document_count': len(collection.documents),
                'permission': 'MANAGE'
            })

    colperms = CollectionPermission.objects.filter(user=request.user)
    collections = []
    for colperm in colperms:
        collections.append({
            'id': colperm.collection.id,
            'name': colperm.collection.name,
            'document_count': len(colperm.collection.documents),
            'permission': colperm.permission
        })
    return JsonResponse(collections, safe=False)

@require_http_methods(['POST'])
@login_required
def update_collection_permissions(request, col_id):
    collection = get_object_or_404(Collection, pk=col_id)
    if not collection.user_can_manage(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        data = json.loads(request.body)
        with transaction.atomic():
            # Remove all existing permissions except the owner's
            CollectionPermission.objects.filter(collection=collection).exclude(user=request.user).delete()

            # Add new permissions
            for viewer in data.get('viewers', []):
                CollectionPermission.objects.create(
                    collection=collection,
                    user=get_user_model().objects.get(id=viewer),
                    permission='VIEW'
                )
            for editor in data.get('editors', []):
                CollectionPermission.objects.create(
                    collection=collection,
                    user=get_user_model().objects.get(id=editor),
                    permission='EDIT'
                )
            for admin in data.get('admins', []):
                CollectionPermission.objects.create(
                    collection=collection,
                    user=get_user_model().objects.get(id=admin),
                    permission='MANAGE'
                )

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(['GET'])
@login_required
def collection(request, col_id):
    collection = get_object_or_404(Collection, pk=col_id)
    if not collection.user_can_view(request.user):
        raise PermissionDenied()
    
    # Get all collections the user can edit for move functionality
    available_collections = Collection.objects.filter_by_user_perm(request.user, 'EDIT')
    
    return render(request, 'aquillm/collection.html', {
        'collection': collection,
        'can_edit': collection.user_can_edit(request.user),
        'can_delete': collection.user_can_manage(request.user),
        'available_collections': available_collections,
    })

@require_http_methods(['GET', 'POST'])
@login_required
def ingest_pdf(request):
    status_message = None
    if request.method == 'POST':
        form = PDFDocumentForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            pdf_file = form.cleaned_data['pdf_file']
            collection = form.cleaned_data['collection']
            title = form.cleaned_data['title'].strip()
            PDFDocument(title=title, pdf_file=pdf_file, collection=collection, ingested_by=request.user).save()
            status_message = "Success"
        else:
            status_message = "Invalid Form Input"
    else:
        form = PDFDocumentForm(request.user)
    
    context = {
        'status_message' : status_message,
        'form' : form
    }

    return render(request, 'aquillm/ingest_pdf.html', context)

@require_http_methods(['GET', 'POST'])
@login_required
def ingest_vtt(request):
    status_message = None
    if request.method == 'POST':
        form = VTTDocumentForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            audio_file = form.cleaned_data['audio_file']
            vtt_file = form.cleaned_data['vtt_file']
            title = form.cleaned_data['title'].strip()
            collection = form.cleaned_data['collection']
            full_text = vtt.to_text(vtt.coalesce_captions(vtt.parse(vtt_file), max_gap=20.0, max_size=1024))
            VTTDocument(title=title,
                        audio_file=audio_file,
                        full_text=full_text,
                        collection=collection,
                        ingested_by=request.user).save()
            status_message = 'Success'
        else:
            status_message = 'Invalid Form Input'
    else:
        form = VTTDocumentForm(request.user)

    context = {
        'status_message' : status_message,
        'form' : form
    }
    
    return render(request, 'aquillm/ingest_vtt.html', context)


@require_http_methods(['DELETE'])
def delete_document(request, doc_id):
    doc = get_doc(request, doc_id)
    if not doc.collection.user_can_edit(request.user):
        return HttpResponseForbidden("User does not have permission to delete this item.")
    doc.delete()
    return HttpResponse(status=200)

@require_http_methods(['GET'])
@login_required
def ws_convo(request, convo_id):
    return render(request, 'aquillm/ws_convo.html', {'convo_id': convo_id})

@require_http_methods(['DELETE'])
@login_required
def delete_ws_convo(request, convo_id):
    convo = get_object_or_404(WSConversation, pk=convo_id)
    if convo.owner != request.user:
        return HttpResponseForbidden("User does not have permission to delete this conversation.")
    convo.delete()
    return HttpResponse(status=200)    

@require_http_methods(['GET'])
def health_check(request):
    return HttpResponse(status=200)

@require_http_methods(['GET'])
@login_required
def user_ws_convos(request):
    convos = WSConversation.objects.filter(owner=request.user).order_by('-updated_at')
    return render(request, 'aquillm/user_ws_convos.html', {'conversations': convos})


# breaks for local debugging with all model objects in scope. 
# also good to have a hardcoded breakpoint, because the debugger won't attach if no breakpoints are set.
if DEBUG:
    @require_http_methods(['GET'])
    @login_required
    def debug_models(request):
        models = apps.get_models()
        model_instances = {model.__name__ : list(model.objects.all()) for model in models}
        breakpoint()
        return HttpResponse(status=200)


@login_required
@require_http_methods(['POST'])
def move_document(request, doc_id):
    document = None
    for model in DESCENDED_FROM_DOCUMENT:
        try:
            document = model.objects.get(id=doc_id)
            break
        except model.DoesNotExist:
            continue
    
    if not document:
        return JsonResponse({'error': 'Document not found'}, status=404)
    
    target_collection_id = request.POST.get('target_collection')
    try:
        target_collection = Collection.objects.get(id=target_collection_id)
    except Collection.DoesNotExist:
        return JsonResponse({'error': 'Target folder not found'}, status=404)
    
    # Check permissions
    if not (document.collection.user_can_edit(request.user) and target_collection.user_can_edit(request.user)):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Move document
    document.collection = target_collection
    document.folder = None  # Reset folder when moving to new collection
    document.save()
    
    return JsonResponse({'success': True})

@login_required
@require_http_methods(['GET'])
def collection_tree(request):
    """View to display the collection hierarchy as a tree"""
    # Get root collections (those without parents) that user can access
    root_collections = Collection.objects.filter(parent=None).filter_by_user_perm(request.user)
    context = {
        'collections': root_collections
    }
    return render(request, 'aquillm/collection_tree.html', context)

@login_required
@require_http_methods(['GET', 'POST'])
def create_collection(request, parent_id=None):
    """View to create a new collection, optionally under a parent"""
    parent = None
    if parent_id:
        parent = get_object_or_404(Collection, id=parent_id)
        if not parent.user_can_edit(request.user):
            return HttpResponseForbidden("You don't have permission to create collections here")

    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            collection = Collection.objects.create(
                name=name,
                parent=parent
            )
            # Give the creator MANAGE permission
            CollectionPermission.objects.create(
                user=request.user,
                collection=collection,
                permission='MANAGE'
            )
            return redirect('collection_tree')
    
    context = {
        'parent': parent
    }
    return render(request, 'aquillm/create_collection.html', context)

@login_required
@require_http_methods(['POST'])
def move_collection(request, collection_id):
    """View to move a collection to a new parent"""
    collection = get_object_or_404(Collection, id=collection_id)
    if not collection.user_can_edit(request.user):
        return HttpResponseForbidden("You don't have permission to move this collection")

    new_parent_id = request.POST.get('new_parent_id')
    new_parent = None
    if new_parent_id:
        new_parent = get_object_or_404(Collection, id=new_parent_id)
        if not new_parent.user_can_edit(request.user):
            return HttpResponseForbidden("You don't have permission to move to this location")

    try:
        collection.move_to(new_parent)
        return JsonResponse({'success': True})
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(['GET'])
def collection_detail(request, collection_id):
    """View to show collection details and its contents"""
    collection = get_object_or_404(Collection, id=collection_id)
    if not collection.user_can_view(request.user):
        return HttpResponseForbidden("You don't have permission to view this collection")

    context = {
        'collection': collection,
        'documents': collection.documents,
        'children': collection.children.all(),
        'can_edit': collection.user_can_edit(request.user),
        'can_manage': collection.user_can_manage(request.user)
    }
    return render(request, 'aquillm/collection_detail.html', context)

@login_required
@require_http_methods(['POST'])
def move_document(request, doc_id):
    """View to move a document to a different collection"""
    doc = get_doc(request, doc_id)
    if not doc.collection.user_can_edit(request.user):
        return HttpResponseForbidden("You don't have permission to move this document")

    new_collection_id = request.POST.get('new_collection_id')
    if new_collection_id:
        new_collection = get_object_or_404(Collection, id=new_collection_id)
        if not new_collection.user_can_edit(request.user):
            return HttpResponseForbidden("You don't have permission to move to this collection")

        try:
            doc.move_to(new_collection)
            return JsonResponse({'success': True})
        except ValidationError as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'No target collection specified'})
