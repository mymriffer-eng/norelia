from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Category, Product
from .forms import CheckoutForm
from apps.orders.services import OrderService


def category_list(request):
    """List all categories"""
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'shop/category_list.html', context)


def category_detail(request, slug):
    """Show products in a category"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    # Get products
    products = Product.objects.filter(
        category=category,
        is_active=True
    ).select_related('category')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'products': page_obj,
    }
    
    return render(request, 'shop/category_detail.html', context)


def product_detail(request, slug):
    """Show single product detail"""
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images'),
        slug=slug,
        is_active=True
    )
    
    # Get related products
    related_products = product.get_related_products(limit=4)
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    
    return render(request, 'shop/product_detail.html', context)


def product_search(request):
    """Search products"""
    query = request.GET.get('q', '')
    products = Product.objects.none()
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(brand__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query),
            is_active=True
        ).select_related('category')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'query': query,
    }
    
    return render(request, 'shop/search_results.html', context)


# ============= CART VIEWS =============

def get_cart(request):
    """Get cart from session"""
    cart = request.session.get('cart', {})
    return cart


def save_cart(request, cart):
    """Save cart to session"""
    request.session['cart'] = cart
    request.session.modified = True


def cart_view(request):
    """View shopping cart"""
    cart = get_cart(request)
    cart_items = []
    total = 0
    
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            subtotal = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal
        except Product.DoesNotExist:
            pass
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    
    return render(request, 'shop/cart.html', context)


def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    quantity = int(request.POST.get('quantity', 1))
    
    # Check stock
    if quantity > product.stock_quantity:
        messages.error(request, f'Недостатъчна наличност. Налични: {product.stock_quantity}')
        return redirect('shop:product_detail', slug=product.slug)
    
    # Get cart
    cart = get_cart(request)
    product_id_str = str(product_id)
    
    # Add or update quantity
    if product_id_str in cart:
        new_quantity = cart[product_id_str] + quantity
        if new_quantity > product.stock_quantity:
            messages.error(request, f'Недостатъчна наличност. Налични: {product.stock_quantity}')
            return redirect('shop:cart')
        cart[product_id_str] = new_quantity
    else:
        cart[product_id_str] = quantity
    
    save_cart(request, cart)
    messages.success(request, f'Продуктът "{product.name}" е добавен в количката!')
    
    return redirect('shop:cart')


def update_cart(request, product_id):
    """Update cart item quantity"""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            return remove_from_cart(request, product_id)
        
        # Check stock
        product = get_object_or_404(Product, id=product_id)
        if quantity > product.stock_quantity:
            messages.error(request, f'Недостатъчна наличност. Налични: {product.stock_quantity}')
            return redirect('shop:cart')
        
        # Update cart
        cart = get_cart(request)
        cart[str(product_id)] = quantity
        save_cart(request, cart)
        
        messages.success(request, 'Количката е актуализирана!')
    
    return redirect('shop:cart')


def remove_from_cart(request, product_id):
    """Remove product from cart"""
    cart = get_cart(request)
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        del cart[product_id_str]
        save_cart(request, cart)
        messages.success(request, 'Продуктът е премахнат от количката!')
    
    return redirect('shop:cart')


def clear_cart(request):
    """Clear entire cart"""
    request.session['cart'] = {}
    request.session.modified = True
    messages.success(request, 'Количката е изчистена!')
    return redirect('shop:cart')


# ============= CHECKOUT =============

def checkout(request):
    """Checkout page"""
    cart = get_cart(request)
    
    if not cart:
        messages.warning(request, 'Количката е празна!')
        return redirect('shop:cart')
    
    # Calculate cart items and total
    cart_items = []
    total = 0
    
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            
            # Check stock availability
            if quantity > product.stock_quantity:
                messages.error(
                    request, 
                    f'Недостатъчна наличност за "{product.name}". Налични: {product.stock_quantity}'
                )
                return redirect('shop:cart')
            
            subtotal = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal
        except Product.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Create order
            order_data = form.cleaned_data
            order_data['user'] = request.user if request.user.is_authenticated else None
            order_data['cart_items'] = cart_items
            order_data['total'] = total
            
            # Use OrderService to create order
            order_service = OrderService()
            order = order_service.create_order(order_data)
            
            if order:
                # Clear cart
                request.session['cart'] = {}
                request.session.modified = True
                
                messages.success(request, f'Поръчката е направена успешно! Номер: {order.order_number}')
                return redirect('orders:order_success', order_number=order.order_number)
            else:
                messages.error(request, 'Възникна грешка при създаването на поръчката.')
    else:
        # Pre-fill form for authenticated users
        initial_data = {}
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            profile = request.user.profile
            initial_data = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'phone': profile.phone,
                'city': profile.city,
                'address': profile.address,
            }
        
        form = CheckoutForm(initial=initial_data)
    
    context = {
        'form': form,
        'cart_items': cart_items,
        'total': total,
    }
    
    return render(request, 'shop/checkout.html', context)
