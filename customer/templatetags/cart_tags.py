# customer/templatetags/cart_tags.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, [])

@register.filter
def cart_item_count(cart_items):
    if not cart_items:
        return 0
    return sum(item.get('quantity', 1) for item in cart_items)