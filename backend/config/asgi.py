import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from ai.api.router import websocket_routes as prompt_urls

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": URLRouter(
            [
                # URLRouter just takes standard Django path() or url() entries.
                *prompt_urls,
            ]
        ),
    },
)
