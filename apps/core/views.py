from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from apps.shop.models import Product, Category
from .models import Testimonial, Newsletter


class HomeView(TemplateView):
    """
    Homepage view with all sections:
    - Hero banner
    - Categories
    - New products
    - Best sellers
    - Promotions
    - Testimonials
    """
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get active categories
        context['categories'] = Category.objects.filter(is_active=True)[:8]
        
        # Get new products (last 8)
        context['new_products'] = Product.objects.filter(
            is_active=True
        ).order_by('-created_at')[:8]
        
        # Get best sellers (products with most orders)
        from apps.orders.models import OrderItem
        best_seller_ids = (
            OrderItem.objects
            .values('product_id')
            .annotate(total_sold=Sum('quantity'))
            .order_by('-total_sold')
            .values_list('product_id', flat=True)[:8]
        )
        context['best_sellers'] = Product.objects.filter(
            id__in=best_seller_ids,
            is_active=True
        )
        
        # Get featured products
        context['featured_products'] = Product.objects.filter(
            is_active=True,
            is_featured=True
        )[:8]
        
        # Get products on sale (with old_price)
        context['sale_products'] = Product.objects.filter(
            is_active=True,
            old_price__isnull=False
        )[:8]
        
        # Get testimonials
        context['testimonials'] = Testimonial.objects.filter(is_active=True)[:6]
        
        return context


def newsletter_subscribe(request):
    """Handle newsletter subscription via AJAX or POST"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Моля, въведете имейл адрес.')
            return redirect('core:home')
        
        # Check if already subscribed
        if Newsletter.objects.filter(email=email).exists():
            newsletter = Newsletter.objects.get(email=email)
            if newsletter.is_active:
                messages.info(request, 'Вече сте абонирани за нашия бюлетин.')
            else:
                newsletter.is_active = True
                newsletter.save()
                messages.success(request, 'Абонаментът Ви е активиран отново!')
        else:
            Newsletter.objects.create(email=email)
            messages.success(request, 'Благодарим! Успешно се абонирахте за нашия бюлетин.')
        
        from django.shortcuts import redirect
        return redirect('core:home')
    
    return redirect('core:home')


def robots_txt(request):
    """Generate robots.txt"""
    from django.http import HttpResponse
    
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /orders/",
        "Disallow: /cart/",
        "Disallow: /checkout/",
        "",
        "Sitemap: " + request.build_absolute_uri('/sitemap.xml')
    ]
    
    return HttpResponse("\n".join(lines), content_type="text/plain")


@staff_member_required
def admin_dashboard(request):
    """Custom admin dashboard with statistics"""
    from apps.orders.models import Order
    from apps.inventory.models import ProductInventory
    
    # Get today's date
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # Orders today
    orders_today = Order.objects.filter(created_at__date=today)
    orders_today_count = orders_today.count()
    revenue_today = orders_today.aggregate(total=Sum('total'))['total'] or 0
    
    # Orders this month
    orders_month = Order.objects.filter(created_at__date__gte=month_start)
    orders_month_count = orders_month.count()
    revenue_month = orders_month.aggregate(total=Sum('total'))['total'] or 0
    
    # Recent orders (last 10)
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    
    # Out of stock products
    out_of_stock = Product.objects.filter(stock_quantity=0, is_active=True)
    
    # Low stock products
    low_stock = ProductInventory.objects.filter(
        current_quantity__lte=10,
        current_quantity__gt=0
    ).select_related('product')
    
    # Best selling products (last 30 days)
    from apps.orders.models import OrderItem
    thirty_days_ago = today - timedelta(days=30)
    best_sellers = (
        OrderItem.objects
        .filter(order__created_at__date__gte=thirty_days_ago)
        .values('product__name')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:10]
    )
    
    # Status breakdown
    status_breakdown = (
        Order.objects
        .filter(created_at__date__gte=month_start)
        .values('status')
        .annotate(count=Count('id'))
    )
    
    context = {
        'orders_today_count': orders_today_count,
        'revenue_today': revenue_today,
        'orders_month_count': orders_month_count,
        'revenue_month': revenue_month,
        'recent_orders': recent_orders,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'best_sellers': best_sellers,
        'status_breakdown': status_breakdown,
    }
    
    return render(request, 'admin/dashboard.html', context)
