from django import template

register = template.Library()


@register.filter
def discount_percentage(old_price, new_price):
    """Calculate discount percentage"""
    if not old_price or not new_price:
        return 0
    try:
        old_price = float(old_price)
        new_price = float(new_price)
        if old_price > 0:
            discount = ((old_price - new_price) / old_price) * 100
            return int(discount)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
    return 0


@register.filter
def multiply(value, arg):
    """Multiply two numbers"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
