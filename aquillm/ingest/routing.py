from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ingest/monitor/(?P<doc_id>[0-9]+)/$", consumers.IngestMonitorConsumer.as_asgi()),
]