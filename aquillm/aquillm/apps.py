from django.apps import AppConfig
import cohere
from dotenv import load_dotenv
from os import getenv
load_dotenv()

class AquillmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aquillm'
    cohere_client = None

    def ready(self):

        self.cohere_client = cohere.Client(getenv('COHERE_KEY'))
        