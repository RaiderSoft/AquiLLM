from channels.generic.websocket import AsyncWebsocketConsumer
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async, aclose_old_connections

from django.contrib.auth.models import User
from django.apps import apps
from json import dumps
from aquillm.settings import DEBUG
class IngestMonitorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user = self.scope['user']
            await self.accept()
            await self.send(dumps({"progress": 50}))
            await self.send(dumps({"messages": ["chunking thing 1", "getting embedding for thing 1"]}))
        except Exception as e:
            if DEBUG:
                raise e
            else:
                await self.send(dumps({"exception": "A server error has occurred. Try reloading the page"}))
        

    async def receive(self, text_data):
        pass