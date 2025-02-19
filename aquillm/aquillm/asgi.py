"""
ASGI config for aquillm project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aquillm.settings")
from django.core.asgi import get_asgi_application
asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator



from chat.routing import websocket_urlpatterns as chat_patterns
from ingest.routing import websocket_urlpatterns as ingest_patterns

application = ProtocolTypeRouter(
    {
        "http": asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(chat_patterns + ingest_patterns)
            )
        )

    }
)
