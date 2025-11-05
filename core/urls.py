from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('index/', MainAPIView.as_view(), name='index'),
    path('viewed-products/', ViewedProductsView.as_view(), name='viewed-products'),
    path('searched-products/', SearchedProducts.as_view(), name='searched-products'),
    path('recommended-products/', RecommendedProducts.as_view(), name='recommended-products'),
    path('products/<slug:slug>/increment-view/', IncrementViewCount.as_view(), name='increment-view-count'),
    path('add-review/', AddProductReviewView.as_view(), name='product-review-create'),
    path('user/<int:user_id>/', get_user_data, name='get_user_data'),
    path('check-email-phone/', CheckEmailPhoneView.as_view(), name='check-email-phone'),
    path('protected/', protected_view, name='protected_view'),
    path('cart/add/', AddToCartView.as_view(), name='add-cart'),
    path('cart/remove/', RemoveFromCartView.as_view(), name='remove-cart'),
    path('cart/check/', CheckCartView.as_view(), name='check-cart'),
    path('cart/sync/', SyncCartView.as_view(), name='sync-cart'),
    path('cart/count/', CartItemCountView.as_view(), name='count-cart'),
    path('cart/items/', CartItemsView.as_view(), name='get_cart_items'),
    path('cart/progress/', UserProgressCheck.as_view(), name='cart_progress'),
    path('checkout/', CheckoutAPIView.as_view(), name='checkout'),
    path('update-delivery-option/', UpdateDeliveryOptionAPIView.as_view(), name='update'),

    path('products/<slug:slug>/', CategoryProductListView.as_view(), name='category-product-list'),
    path('brand/<slug:slug>/', BrandProductListView.as_view(), name='brand-product-list'),
    path('search/', ProductSearchAPIView.as_view(), name='product-search-api'),

    # ###############################################CATEGORY
    # path('subcategory/<slug:slug>/', SubcategoryListView.as_view(), name='sub-category'),
    path('subcategory/<slug:slug>/<slug:category>/', SubcategoryListView.as_view(), name='subcategory-list'),
    # ###############################################CATEGORY

    # ###############################################VENDOR
    path('vendor/<slug>/', VendorDetailView.as_view(), name='vendor-detail'),
    # ###############################################VENDOR
]
