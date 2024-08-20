from django.apps import AppConfig

from django.template import Engine, Context
import cohere
import openai
import anthropic
from dotenv import load_dotenv
from os import getenv
from typing import TypedDict

load_dotenv()

RAG_PROMPT_STRING = """
{% if message.context_chunks %}
<context>
<instructions>
The user's retrieval augmented generation system has provided these document segments, which are relevant to their message. Base your answer on the information in these segments. If these do not include the information required to ask the user's question, do not go off-script, simply inform the user that the retrieval augmented generation system did not provide the relevant information.
</instructions>
RAG Search Results:

{% for chunk in message.context_chunks.all %}
    [{{ forloop.counter }}] {{ chunk.document.title }} chunk #{{chunk.chunk_number}}

    {{ chunk.content }}

{% endfor %}
</context>
The user's query is as follows: 
<user-query>
    {{ message.content }}
</user-query>
{% else %}
    {{ message.content }}
{% endif %}
"""




def get_embedding_func(cohere_client):


    def get_embedding(query: str, input_type: str='search_query'):
        if input_type not in ('search_document', 'search_query', 'classification', 'clustering'):
            raise ValueError(f'bad input type to embedding call: {input_type}')
        response = cohere_client.embed(
            texts=[query],
            model="embed-english-v3.0",
            input_type=input_type
        )
        return response.embeddings[0]
    return get_embedding

class AquillmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aquillm'
    cohere_client = None
    openai_client = None
    anthropic_client = None
    get_embedding = None
    
    
    
    vector_top_k = 30
    trigram_top_k = 30
    rag_prompt_template = Engine().from_string(RAG_PROMPT_STRING)



    chunk_size = 2048
    chunk_overlap = 512 # at each end.
#   |-----------CHUNK-----------|
#   <---------chunk_size-------->
#                       <------->  chunk_overlap
#                       |-----------CHUNK-----------|
    def ready(self):

        self.cohere_client = cohere.Client(getenv('COHERE_KEY'))
        self.openai_client = openai.OpenAI()
        self.anthropic_client = anthropic.Anthropic()
        self.get_embedding = get_embedding_func(self.cohere_client)
