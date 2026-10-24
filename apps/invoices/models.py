from django.db import models
from apps.orders.models import Order


class Invoice(models.Model):
    """Invoices for orders"""
    
    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name='invoice',
        verbose_name='Поръчка',
        null=True,
        blank=True,
        help_text='Свържете с поръчка или оставете празно за ръчна фактура'
    )
    
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name='Номер на фактура')
    invoice_date = models.DateField(verbose_name='Дата на фактура')
    
    # Customer type
    is_company = models.BooleanField(default=False, verbose_name='Фирмен клиент')
    
    # Customer details (manual entry)
    customer_name = models.CharField(max_length=200, verbose_name='Име на клиент / Фирма')
    customer_email = models.EmailField(verbose_name='Имейл', blank=True)
    customer_phone = models.CharField(max_length=20, verbose_name='Телефон')
    customer_address = models.TextField(verbose_name='Адрес')
    
    # Company specific fields
    company_vat = models.CharField(max_length=50, blank=True, verbose_name='ЕИК/Булстат', help_text='За фирмени клиенти')
    company_vat_number = models.CharField(max_length=50, blank=True, verbose_name='ДДС номер', help_text='За регистрирани по ДДС')
    company_mol = models.CharField(max_length=200, blank=True, verbose_name='МОЛ', help_text='Материално отговорно лице')
    
    # Invoice amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Междинна сума')
    trade_discount_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        verbose_name='Търговска отстъпка (%)',
        help_text='Процент отстъпка за фирми'
    )
    trade_discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name='Сума отстъпка (лв.)'
    )
    subtotal_after_discount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name='Сума след отстъпка'
    )
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Доставка')
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Обща сума')
    
    # Notes
    notes = models.TextField(blank=True, verbose_name='Бележки')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Фактура'
        verbose_name_plural = 'Фактури'
        ordering = ['-invoice_date', '-invoice_number']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['-invoice_date']),
        ]
    
    def __str__(self):
        return f'Фактура {self.invoice_number}'
    
    def calculate_discount(self):
        """Calculate trade discount amount"""
        if self.trade_discount_percent > 0:
            self.trade_discount_amount = (self.subtotal * self.trade_discount_percent) / 100
            self.subtotal_after_discount = self.subtotal - self.trade_discount_amount
        else:
            self.trade_discount_amount = 0
            self.subtotal_after_discount = self.subtotal
        
        # Calculate total
        self.total = self.subtotal_after_discount + self.shipping_cost
    
    def update_subtotal(self):
        """Update subtotal from items"""
        from django.db.models import Sum
        items_total = self.items.aggregate(total=Sum('subtotal'))['total'] or 0
        self.subtotal = items_total
        self.calculate_discount()
        self.save()
    
    def save(self, *args, **kwargs):
        """Override save to calculate discount and total"""
        # Generate invoice number if not set
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        # Calculate discount and total
        self.calculate_discount()
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_invoice_number():
        """Generate invoice number in format: YYYY-NNNNNN"""
        from django.utils import timezone
        from django.conf import settings
        
        year = timezone.now().year
        prefix = getattr(settings, 'INVOICE_NUMBER_PREFIX', str(year))
        
        # Get last invoice number for this year
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=f'{prefix}-'
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            # Extract number part
            try:
                last_number = int(last_invoice.invoice_number.split('-')[1])
                next_number = last_number + 1
            except (IndexError, ValueError):
                next_number = getattr(settings, 'INVOICE_START_NUMBER', 1)
        else:
            next_number = getattr(settings, 'INVOICE_START_NUMBER', 1)
        
        return f'{prefix}-{next_number:06d}'


class InvoiceItem(models.Model):
    """Items in invoice - for manual invoicing"""
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Фактура'
    )
    
    product_name = models.CharField(max_length=200, verbose_name='Име на продукт')
    product_sku = models.CharField(max_length=50, blank=True, verbose_name='SKU')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена (лв.)')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сума (лв.)', editable=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Артикул във фактура'
        verbose_name_plural = 'Артикули във фактури'
        ordering = ['id']
    
    def __str__(self):
        return f'{self.product_name} x {self.quantity}'
    
    def save(self, *args, **kwargs):
        """Calculate subtotal before saving"""
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)
        
        # Update invoice subtotal
        self.invoice.update_subtotal()
    
    def delete(self, *args, **kwargs):
        """Update invoice subtotal after deleting"""
        invoice = self.invoice
        super().delete(*args, **kwargs)
        invoice.update_subtotal()
