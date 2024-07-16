from django.apps import AppConfig
import cohere
from dotenv import load_dotenv
from os import getenv
load_dotenv()

class AquillmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aquillm'
    cohere_client = None

    vector_top_k = 30
    trigram_top_k = 30

    chunk_size = 2048
    chunk_overlap = 512 # at each end.
#   |-----------CHUNK-----------|
#   <---------chunk_size-------->
#                       <------->  chunk_overlap
#                       |-----------CHUNK-----------|
    def ready(self):

        self.cohere_client = cohere.Client(getenv('COHERE_KEY'))

        