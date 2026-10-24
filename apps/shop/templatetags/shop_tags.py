from django import template

register = template.Library()


@register.simple_tag
def cart_item_count(cart, product_id):
    """Get quantity of specific product in cart"""
    return cart.get(str(product_id), 0)


@register.filter
def in_cart(product_id, cart):
    """Check if product is in cart"""
    return str(product_id) in cart
