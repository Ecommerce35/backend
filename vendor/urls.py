from django.urls import include, path
from userauths import views as account_views
from . import views


from .views import *

urlpatterns = [
 ############################  VENDOR  ####################
    path('', account_views.dashboard, name='dashboard'),
    path('vendor/', views.index, name="index"),
    path("all/", views.vendor_list_view, name="vendor-list"),
    path('dashboard/', views.vendor_dashboard, name='vendor-dashboard'),
    path('profile/', views.vendor_profile, name='vendor_profile'),
    path('v/products/', views.vendor_product, name='vendor_product'),
    path('reviews/<slug:slug>/', views.vendor_review, name='vendor_review'),
    path('operating-hours/', views.operating_hours, name='operating-hours'),
    path('operating-hours/add/', views.add_operating_hours, name='add-operating-hours'),
    path('operating-hours/remove/<int:pk>/', views.remove_operating_hours, name='remove-operating-hours'),
    path("v/add-product/", views.add_product, name="add_product"),

    path('register/', VendorSignUpView.as_view(), name='vendor-register'),
    path('detail/', VendorDetailView.as_view(), name='vendor-detail'),
    path('data/', VendorAPIView.as_view(), name='vendor'),
    path('opening-hours/', OpeningHourDetailView.as_view(), name='opening-hour'),
    path('order/<int:id>/', OrderDetailsAPIView.as_view(), name='order-details'),
    path('opening-hours/<int:pk>/', OpeningHourDetailView.as_view(), name='opening-hour-detail'),
    path('order-status-change/<int:order_id>/', UpdateOrderStatusAPIView.as_view(), name='change-order-status'),
    path('order/<int:id>/update-status/', UpdateOrderProductStatusAPIView.as_view(), name='update-order-product-status'),
    path('about/', AboutAPIView.as_view(), name='about-list-create'),
    path('product-related-data/', ProductRelatedDataAPIView.as_view(), name='product-related-data'),
    path('product/add/', VendorProductAPIView.as_view(), name='add-product'),
    path('product/change/<int:product_id>/', VendorProductAPIView.as_view(), name='edit-product'),
    path('products/', VendorProducts.as_view(), name='products'),
    path('payment-method/', VendorPaymentMethodAPIView.as_view(), name='vendor-payment-method'),

]