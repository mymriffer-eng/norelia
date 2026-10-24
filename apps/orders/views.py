from django.shortcuts import render, get_object_or_404
from .models import Order


def order_success(request, order_number):
    """Order success page"""
    order = get_object_or_404(Order, order_number=order_number)
    
    context = {
        'order': order,
    }
    
    return render(request, 'orders/order_success.html', context)


def order_detail(request, order_number):
    """View order details"""
    # Check if user owns the order or is staff
    order = get_object_or_404(Order, order_number=order_number)
    
    # Basic security check
    if request.user.is_authenticated:
        if order.user != request.user and not request.user.is_staff:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("You don't have permission to view this order.")
    else:
        # Guest users can view using order number (weak security, improve if needed)
        pass
    
    context = {
        'order': order,
    }
    
    return render(request, 'orders/order_detail.html', context)
