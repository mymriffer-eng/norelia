import logging

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

logger = logging.getLogger(__name__)

SHIPPING_TEXT = 'Според тарифата на куриера'

STATUS_MESSAGES = {
    'confirmed': 'Вашата поръчка беше потвърдена и се подготвя за изпращане.',
    'shipped': 'Вашата поръчка беше изпратена към куриер. Очаквайте доставка в най-кратък срок.',
    'delivered': 'Вашата поръчка беше доставена. Благодарим, че пазарувахте при нас!',
    'cancelled': 'Вашата поръчка беше отказана. При въпроси се свържете с нас.',
    'new': 'Статусът на вашата поръчка беше променен на "Нова".',
}


def _order_url(order):
    path = reverse('orders:order_detail', kwargs={'order_number': order.order_number})
    return f"{settings.SITE_URL.rstrip('/')}{path}"


def _items_text(order):
    lines = []
    for item in order.items.all():
        lines.append(f'- {item.product_name} x {item.quantity} = {item.subtotal} €')
    return '\n'.join(lines)


def _send(order, subject, intro):
    body = (
        f'Здравейте, {order.get_full_name()}!\n\n'
        f'{intro}\n\n'
        f'Номер на поръчка: {order.order_number}\n'
        f'Статус: {order.get_status_display()}\n\n'
        f'Продукти:\n{_items_text(order)}\n\n'
        f'Междинна сума: {order.subtotal} €\n'
        f'Доставка: {SHIPPING_TEXT}\n'
        f'Обща сума: {order.total} €\n'
        f'Начин на плащане: {order.get_payment_method_display()}\n\n'
        f'Адрес за доставка: {order.city}, {order.address}\n'
        f'Телефон: {order.phone}\n\n'
        f'Преглед на поръчката: {_order_url(order)}\n\n'
        f'Поздрави,\nNorelia Beauty\n{settings.SITE_URL}\n'
    )
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [order.email])
    except Exception:
        # Never break checkout or admin because of an email problem
        logger.exception('Failed to send order email for %s', order.order_number)


def send_order_received_email(order):
    _send(
        order,
        f'Norelia Beauty - получихме вашата поръчка {order.order_number}',
        'Благодарим ви за поръчката! Получихме я и скоро ще се свържем с вас за потвърждение.',
    )


def send_order_status_email(order):
    message = STATUS_MESSAGES.get(order.status, f'Статус на поръчката: {order.get_status_display()}.')
    _send(
        order,
        f'Norelia Beauty - поръчка {order.order_number}: {order.get_status_display()}',
        message,
    )
