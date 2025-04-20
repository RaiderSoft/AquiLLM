from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Route for crawl status updates, requires authentication
    re_path(r'ws/crawl_status/$', consumers.CrawlStatusConsumer.as_asgi()),
]