from django import template
from django.db.models import Sum
from django.urls import reverse

from order.models import Cart

register = template.Library()



@register.simple_tag
def shopcartcount(userid):
    count = Cart.objects.filter(user_id=userid).count()
    return count 


@register.filter(name='multiply')
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None