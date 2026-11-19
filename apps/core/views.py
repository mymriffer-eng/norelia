import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage, send_mail
from django.core.validators import validate_email
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import TemplateView
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from apps.shop.models import Product, Category
from .models import Testimonial, Newsletter
from .forms import ContactForm

logger = logging.getLogger(__name__)


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
        best_seller_ids = list(
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


def contact(request):
    """Contact page with company details and a contact form"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            body = (
                f"Име: {data['name']}\n"
                f"Имейл: {data['email']}\n"
                f"Телефон: {data['phone'] or '-'}\n\n"
                f"{data['message']}"
            )
            try:
                EmailMessage(
                    subject='Ново съобщение от контактната форма',
                    body=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[settings.CONTACT_EMAIL],
                    reply_to=[data['email']],
                ).send(fail_silently=False)
            except Exception:
                logger.exception('Contact form email failed')
                messages.error(
                    request,
                    f'Съобщението не беше изпратено. Моля, свържете се с нас на телефон {settings.CONTACT_PHONE}.'
                )
            else:
                messages.success(request, 'Благодарим! Съобщението ви беше изпратено. Ще се свържем с вас в най-кратък срок.')
                return redirect('core:contact')
    else:
        form = ContactForm()
    
    return render(request, 'core/contact.html', {'form': form})


def privacy_policy(request):
    return render(request, 'core/privacy.html')


def cookie_policy(request):
    return render(request, 'core/cookies.html')


def terms(request):
    return render(request, 'core/terms.html')


def _back(request):
    """Redirect to the previous page if it is on this site, otherwise home"""
    referer = request.META.get('HTTP_REFERER', '')
    if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(referer)
    return redirect('core:home')


def _send_newsletter_confirmation(newsletter):
    base = settings.SITE_URL.rstrip('/')
    confirm_url = base + reverse('core:newsletter_confirm', args=[newsletter.token])
    unsubscribe_url = base + reverse('core:newsletter_unsubscribe', args=[newsletter.token])
    body = (
        'Здравейте!\n\n'
        'Получихме заявка за абониране на този имейл за бюлетина на Norelia Beauty.\n'
        'За да потвърдите абонамента си, последвайте връзката:\n'
        f'{confirm_url}\n\n'
        'Ако не сте подавали такава заявка, просто игнорирайте това съобщение. '
        'Няма да получавате бюлетини, докато не потвърдите.\n\n'
        f'Отписване по всяко време: {unsubscribe_url}\n\n'
        f'Поздрави,\nNorelia Beauty\n{base}\n'
    )
    try:
        send_mail(
            'Norelia Beauty - потвърдете абонамента си за бюлетина',
            body,
            settings.DEFAULT_FROM_EMAIL,
            [newsletter.email],
        )
    except Exception:
        logger.exception('Newsletter confirmation email failed')
        return False
    return True


def newsletter_subscribe(request):
    """Newsletter subscription with explicit consent and double opt-in"""
    if request.method != 'POST':
        return redirect('core:home')

    email = request.POST.get('email', '').strip()
    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, 'Моля, въведете валиден имейл адрес.')
        return _back(request)

    if not request.POST.get('consent'):
        messages.error(request, 'За абониране трябва да дадете съгласие за получаване на бюлетина.')
        return _back(request)

    newsletter, created = Newsletter.objects.get_or_create(email=email)
    if not created and newsletter.is_confirmed and newsletter.is_active:
        messages.info(request, 'Вече сте абонирани за нашия бюлетин.')
        return redirect('core:home')

    # (Re)start the opt-in flow; consent is only valid after confirmation
    newsletter.is_active = True
    newsletter.is_confirmed = False
    newsletter.confirmed_at = None
    newsletter.save()
    if _send_newsletter_confirmation(newsletter):
        messages.success(request, 'Изпратихме Ви имейл. Моля, потвърдете абонамента си чрез връзката в него.')
    else:
        messages.error(request, 'Не успяхме да изпратим имейл за потвърждение. Моля, опитайте отново по-късно.')
    return redirect('core:home')


def newsletter_confirm(request, token):
    newsletter = Newsletter.objects.filter(token=token).first()
    if not newsletter:
        messages.error(request, 'Невалидна или изтекла връзка за потвърждение.')
    else:
        if not newsletter.is_confirmed:
            newsletter.is_confirmed = True
            newsletter.is_active = True
            newsletter.confirmed_at = timezone.now()
            newsletter.save()
        messages.success(request, 'Абонаментът Ви за бюлетина е потвърден. Благодарим!')
    return redirect('core:home')


def newsletter_unsubscribe(request, token):
    newsletter = Newsletter.objects.filter(token=token).first()
    if not newsletter:
        messages.error(request, 'Невалидна връзка за отписване.')
    else:
        newsletter.is_active = False
        newsletter.save()
        messages.success(request, 'Отписахте се от бюлетина. Няма да получавате повече съобщения.')
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
