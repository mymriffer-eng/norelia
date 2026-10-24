from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order


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
