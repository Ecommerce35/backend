import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from vendor import routing
from django.urls import path
from vendor.consumers import *


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            # routing.websocket_urlpatterns
            path("ws/seller/<int:seller_id>/", VendorOrderConsumer.as_asgi()),
        )
    ),
})

