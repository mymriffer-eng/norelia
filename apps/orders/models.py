from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from apps.shop.models import Product


def generate_order_number():
    """Generate unique order number"""
    from django.utils import timezone
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    random_str = get_random_string(4, '0123456789')
    return f'ORD-{timestamp}-{random_str}'


class Order(models.Model):
    """Customer orders"""
    STATUS_CHOICES = [
        ('new', 'Нова'),
        ('confirmed', 'Потвърдена'),
        ('shipped', 'Изпратена'),
        ('delivered', 'Доставена'),
        ('cancelled', 'Отказана'),
    ]
    
    PAYMENT_CHOICES = [
        ('cod', 'Наложен платеж'),
    ]
    
    # Order info
    order_number = models.CharField(max_length=50, unique=True, editable=False, verbose_name='Номер')
    
    # Customer info (can be guest or registered user)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='orders',
        verbose_name='Потребител'
    )
    
    # Contact details
    first_name = models.CharField(max_length=50, verbose_name='Име')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    email = models.EmailField(verbose_name='Имейл')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    
    # Delivery address
    city = models.CharField(max_length=100, verbose_name='Град')
    address = models.TextField(verbose_name='Адрес')
    
    # Order details
    notes = models.TextField(blank=True, verbose_name='Бележки')
    
    # Payment
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_CHOICES,
        default='cod',
        verbose_name='Метод на плащане'
    )
    
    # Totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Междинна сума')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Доставка')
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Обща сума')
    
    # Status
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Статус'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Създадена')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Актуализирана')
    
    class Meta:
        verbose_name = 'Поръчка'
        verbose_name_plural = 'Поръчки'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f'Поръчка #{self.order_number}'
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_order_number()
        super().save(*args, **kwargs)
    
    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def get_status_display_color(self):
        """Get color for status badge"""
        colors = {
            'new': 'info',
            'confirmed': 'primary',
            'shipped': 'warning',
            'delivered': 'success',
            'cancelled': 'danger',
        }
        return colors.get(self.status, 'secondary')


class OrderItem(models.Model):
    """Items in an order"""
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name='Поръчка'
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT,
        verbose_name='Продукт'
    )
    
    # Store product details at time of order
    product_name = models.CharField(max_length=200, verbose_name='Име на продукт')
    product_sku = models.CharField(max_length=50, verbose_name='SKU')
    
    quantity = models.IntegerField(verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Междинна сума')
    
    class Meta:
        verbose_name = 'Артикул в поръчка'
        verbose_name_plural = 'Артикули в поръчки'
    
    def __str__(self):
        return f'{self.product_name} x {self.quantity}'
    
    def save(self, *args, **kwargs):
        # Auto-calculate subtotal
        self.subtotal = self.quantity * self.price
        super().save(*args, **kwargs)
