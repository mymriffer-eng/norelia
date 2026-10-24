from apps.shop.models import Product


def cart(request):
    """
    Add cart information to all templates
    """
    cart_data = request.session.get('cart', {})
    cart_count = sum(cart_data.values())
    cart_total = 0
    
    # Calculate total
    for product_id, quantity in cart_data.items():
        try:
            product = Product.objects.get(id=product_id)
            cart_total += product.price * quantity
        except Product.DoesNotExist:
            pass
    
    return {
        'cart_count': cart_count,
        'cart_total': cart_total,
    }
