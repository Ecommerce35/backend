from django.urls import include, path

from .views import *


urlpatterns = [
    path('ajaxcolor/', AjaxColorAPIView.as_view(), name='change_color'),
    path('<sku>/<slug>/', ProductDetailAPIView.as_view(), name='product-detail-api'),
]