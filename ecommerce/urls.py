
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render


def home(request):
    return render(request, "home.html")

urlpatterns = [
    # path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),
    path('', home, name='home'),  
    path('secret/', admin.site.urls),
    path("api/", include("core.urls")),
    path("api/v1/auth/", include("userauths.urls")),
    path("api/v1/product/", include("product.urls")),
    path("api/v1/auth/", include("social_accounts.urls")),
    path("api/v1/auth/user/", include("customer.urls")),
    path("api/v1/payments/", include("payments.urls")),
    path("api/v1/address/", include("address.urls")),
    path("vendor/", include("vendor.urls")),
    path("", include("product.urls")),
    path("ckeditor/", include("ckeditor_uploader.urls")),   
]



if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)