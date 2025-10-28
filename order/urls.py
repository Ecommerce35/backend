from django.urls import path,include
from . import views
from product.views import *

app_name = "order"

urlpatterns = [
    path('addtocart/<id>/', views.addtocart, name='addtocart' ),
    path('deletecart/', views.deletefromcart, name='deletefromcart' ),
    path('update', views.updateQuantity, name='incart'),
    path('increase/', views.increase_quantity, name='increase-quantity'),
    path('decrease/', views.decrease_quantity, name='decrease-quantity'),
    path('shopcart/', views.shopcart, name='shopcart' ),
    path('remove_coupon/', views.remove_coupon, name='remove_coupon'),

    #####################BUY NOW########################
    path('buy-now/<id>/', views.buy_now, name='buy_now' ),
    path('initiate/', views.paystack_create_payment, name='initiate_payment' ),
    path('buynow/initiate/', views.initiate_buynow, name='initiate_buynow' ),
    path('update-delivery-option/<int:option_id>/', views.update_delivery_option, name='update_delivery_option'),
    path('update-location/', views.update_profile_location, name='update_profile_location'),
    path('o/execute/', views.paystack_execute, name='paystack_execute' ),

    #####################BUY NOW########################

    path('checkout/', views.checkout_view, name='checkout' ),
    path('cart/save-for-later/', views.save_product_for_later, name='save_product_for_later' ),
    path('update_delivery_fee/', views.update_delivery_fee, name='update-delivery-fee'),
    # path('address/', views.address_view, name='address' ),
     #Paypal URL
    path('paypal/', include('paypal.standard.ipn.urls')),
]