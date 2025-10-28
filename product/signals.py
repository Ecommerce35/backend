from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from order.models import Cart, Location, Address
from address.models import Address

@receiver(user_logged_in)
def merge_carts(sender, request, user, **kwargs):
    try:
        device = request.COOKIES['device']
    except KeyError:
        device = None

    if device:
        anonymous_cart_items = Cart.objects.filter(session_id=device)
        for item in anonymous_cart_items:
            cart_item, created = Cart.objects.get_or_create(
                user=user, 
                product=item.product,
                variant=item.variant or None,
                quantity = item.quantity
            )
            if not created:
                cart_item.quantity += item.quantity
                cart_item.save()
            item.delete()
            
@receiver(user_logged_out)
def save_carts_before_logout(sender, request, user, **kwargs):
    try:
        device = request.COOKIES['device']
    except KeyError:
        device = None

    if device:
        anonymous_cart_items = Cart.objects.filter(user=user)
        for item in anonymous_cart_items:
            cart_item, created = Cart.objects.get_or_create(
                session_id=device,
                product=item.product,
                variant=item.variant or None,
                quantity = item.quantity
            )
            if not created:
                cart_item.quantity += item.quantity
                cart_item.save()
            item.delete()