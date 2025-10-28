from django.urls import re_path
from .consumers import *

websocket_urlpatterns = [
    re_path(r"^ws/vendor/order/", VendorOrderConsumer.as_asgi()),
]