from . import models
import functools
import logging
from django.core.exceptions import ValidationError
from django.contrib.postgres.search import TrigramSimilarity
from pgvector.django import L2Distance


from django.db import DatabaseError
from django.db.models import Case, When

from django.apps import apps

from django.db.models.query import QuerySet
from typing import  List, Type, Tuple

from .models import *
get_embedding = apps.get_app_config('aquillm').get_embedding
anthropic_client = apps.get_app_config('aquillm').anthropic_client

logger = logging.getLogger(__name__)


# def get_llm_response(query, context: QuerySet[TextChunk]=None):
#     system = 
#     messages = [{
#         'role' : 'user',
#         'content' : [
#             {
#                 'type' : 'text',
#                 'text' : query
#             }
#         ]
#     }]
    


# returns a list of objects, not a queryset!
def get_user_accessible_documents(user, collections=None, perm='VIEW'):

    if collections is None:
        collections = Collection.objects.all()

    collections = collections.filter_by_user_perm(user, perm)
    documents = functools.reduce(lambda l, r: l + r, [list(x.objects.filter(collection__in=collections)) for x in DESCENDED_FROM_DOCUMENT])
    return documents





def rerank(query:str, chunks: QuerySet[TextChunk], top_k: int) -> QuerySet[TextChunk]:
    cohere = apps.get_app_config('aquillm').cohere_client
    response = cohere.rerank(
        model="rerank-english-v3.0",
        query=query,
        documents=list([{"content": chunk.content, "id": chunk.pk} for chunk in chunks]),
        rank_fields=['content'],
        top_n=top_k,
        return_documents=True 
    )
    ranked_list = list([result.document.id for result in response.results])
    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ranked_list)])
    return TextChunk.objects.filter(pk__in=ranked_list).order_by(preserved)


def text_chunk_search(query:str, top_k: str, docs: List[Type[Document]]) -> Tuple[QuerySet[TextChunk]]:
    vector_top_k = apps.get_app_config('aquillm').vector_top_k
    trigram_top_k = apps.get_app_config('aquillm').trigram_top_k

    try:
        vector_results = TextChunk.objects.filter_by_documents(docs).order_by(L2Distance('embedding', get_embedding(query)))[:vector_top_k]
        trigram_results = TextChunk.objects.filter_by_documents(docs).annotate(similarity = TrigramSimilarity('content', query)
        ).filter(similarity__gt=0.000001).order_by('-similarity')[:trigram_top_k]

        for chunk in vector_results | trigram_results:
            content_type = chunk.content_type
            model = content_type.model_class()
            chunk.document = model.objects.get(id=chunk.object_id)

        reranked_results = rerank(query, vector_results | trigram_results, top_k)
        return vector_results, trigram_results, reranked_results
    except DatabaseError as e:
        logger.error(f"Database error during search: {str(e)}")
        error_message = "An error occurred while searching the database. Please try again later."
    except ValidationError as e:
        logger.error(f"Validation error during search: {str(e)}")
        error_message = "Invalid search parameters. Please check your input and try again."
    except Exception as e:
        logger.error(f"Unexpected error during search: {str(e)}")
        error_message = "An unexpected error occurred. Please try again later."