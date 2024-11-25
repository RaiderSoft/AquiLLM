from channels.generic.websocket import WebsocketConsumer
from channels.auth import AuthMiddlewareStack

from django.contrib.auth.models import User
from django.apps import apps

from pydantic import ValidationError

from aquillm import llm
from aquillm.llm import UserMessage, Conversation
from aquillm.settings import DEBUG

class ChatConsumer(WebsocketConsumer):
    llm_if: llm.LLMInterface = apps.get_app_config('aquillm').llm_interface
    convo: Conversation = Conversation(system="You are a helpful assistant.")
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        try:
            msg = UserMessage.model_validate_json(text_data)
            self.convo += msg
            self.convo, _ = self.llm_if.complete(self.convo, max_tokens=2048)
            self.send(text_data=self.convo.model_dump_json())
        except Exception as e:
            if DEBUG:
                self.send(text_data='{"exception": "%s"}' % str(e))
            else:
                self.send(text_data='{"exception": "A server error has occurred. Try reloading the page"}')

