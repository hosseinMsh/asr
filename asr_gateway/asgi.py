import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "asr_gateway.settings")

from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from asr.routing import websocket_urlpatterns
from asr.auth.ws import JWTQueryStringAuthMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTQueryStringAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})

