from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order


@receiver(pre_save, sender=Order)
def remember_previous_status(sender, instance, **kwargs):
    """Store the old status so post_save can detect a status change."""
    instance._previous_status = None
    if instance.pk:
        instance._previous_status = (
            Order.objects.filter(pk=instance.pk).values_list('status', flat=True).first()
        )


@receiver(post_save, sender=Order)
def send_order_emails(sender, instance, created, **kwargs):
    """Email the customer when an order is received and when its status changes."""
    from .emails import send_order_received_email, send_order_status_email

    if created:
        # on_commit: order items are created after the order inside the same transaction
        transaction.on_commit(lambda: send_order_received_email(instance))
    elif getattr(instance, '_previous_status', None) not in (None, instance.status):
        transaction.on_commit(lambda: send_order_status_email(instance))


@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, created, **kwargs):
    """
    Handle order status changes
    """
    if not created:
        # Check if status changed to confirmed
        if instance.status == 'confirmed':
            # Check if invoice already exists
            if not hasattr(instance, 'invoice'):
                # Create invoice
                from apps.invoices.services import InvoiceService
                invoice_service = InvoiceService()
                try:
                    invoice_service.create_invoice_for_order(instance)
                except Exception as e:
                    print(f'Error creating invoice: {e}')
