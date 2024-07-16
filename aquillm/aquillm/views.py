from django.shortcuts import render
from django.apps import apps
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Case, When



from pgvector.django import L2Distance


from .forms import SearchForm
from .models import TextChunk



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
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            top_k = form.cleaned_data['top_k']
            vector_top_k = apps.get_app_config('aquillm').vector_top_k
            trigram_top_k = apps.get_app_config('aquillm').trigram_top_k

            vector_results = TextChunk.objects.order_by(L2Distance('embedding', get_embedding(query)))[:vector_top_k]
            trigram_results = TextChunk.objects.annotate(similarity = TrigramSimilarity('content', query)
            ).filter(similarity__gt=0.000001).order_by('-similarity')[:trigram_top_k]

            for chunk in vector_results | trigram_results:
                content_type = chunk.content_type
                model = content_type.model_class()
                chunk.document = model.objects.get(id=chunk.object_id)

            reranked_results = rerank(query, vector_results | trigram_results, top_k)
    else:
        form = SearchForm()

    context = {
        'form': form,
        'reranked_results': reranked_results,
        'vector_results': vector_results,
        'trigram_results': trigram_results
    }

    return render(request, 'aquillm/search.html', context)
