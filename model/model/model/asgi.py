import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from prompt.consumers import urls as prompt_urls

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
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
