from django.db import models
from django.core.exceptions import ValidationError
from apps.shop.models import Product


class Supplier(models.Model):
    """Suppliers/Vendors"""
    name = models.CharField(max_length=200, verbose_name='Име')
    contact_person = models.CharField(max_length=100, blank=True, verbose_name='Лице за контакт')
    email = models.EmailField(blank=True, verbose_name='Имейл')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    address = models.TextField(blank=True, verbose_name='Адрес')
    notes = models.TextField(blank=True, verbose_name='Бележки')
    
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ProductInventory(models.Model):
    """Track inventory levels for each product"""
    product = models.OneToOneField(
        Product, 
        on_delete=models.CASCADE, 
        related_name='inventory',
        verbose_name='Продукт'
    )
    
    # Stock levels
    current_quantity = models.IntegerField(default=0, verbose_name='Текуща наличност')
    minimum_quantity = models.IntegerField(default=10, verbose_name='Минимална наличност')
    reserved_quantity = models.IntegerField(default=0, verbose_name='Резервирана наличност')
    
    # Available = current - reserved
    def available_quantity(self):
        return max(0, self.current_quantity - self.reserved_quantity)
    
    def needs_restock(self):
        """Check if product needs restock"""
        return self.current_quantity <= self.minimum_quantity
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product Inventory'
        verbose_name_plural = 'Product Inventories'
    
    def __str__(self):
        return f'{self.product.name} - Stock: {self.current_quantity}'
    
    def save(self, *args, **kwargs):
        # Sync with Product model
        self.product.stock_quantity = self.current_quantity
        self.product.save()
        super().save(*args, **kwargs)


class PurchaseDelivery(models.Model):
    """Purchase deliveries from suppliers"""
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.PROTECT,
        verbose_name='Доставчик'
    )
    invoice_number = models.CharField(max_length=100, verbose_name='Номер на фактура')
    delivery_date = models.DateField(verbose_name='Дата на доставка')
    notes = models.TextField(blank=True, verbose_name='Бележки')
    
    is_received = models.BooleanField(default=False, verbose_name='Получена')
    received_at = models.DateTimeField(null=True, blank=True, verbose_name='Приета на')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Purchase Delivery'
        verbose_name_plural = 'Purchase Deliveries'
        ordering = ['-delivery_date']
    
    def __str__(self):
        return f'{self.supplier.name} - {self.invoice_number}'
    
    def get_total_cost(self):
        """Calculate total delivery cost"""
        return sum(item.get_total() for item in self.items.all())
    
    def receive_delivery(self):
        """Process delivery and update stock"""
        if self.is_received:
            raise ValidationError('Delivery already received')
        
        from django.utils import timezone
        
        # Update inventory for each item
        for item in self.items.all():
            inventory, created = ProductInventory.objects.get_or_create(
                product=item.product
            )
            inventory.current_quantity += item.quantity
            inventory.save()
            
            # Create stock movement
            StockMovement.objects.create(
                product=item.product,
                movement_type='delivery',
                quantity=item.quantity,
                reference=f'Purchase Delivery #{self.id}',
                notes=f'From {self.supplier.name}'
            )
        
        self.is_received = True
        self.received_at = timezone.now()
        self.save()


class PurchaseDeliveryItem(models.Model):
    """Items in a purchase delivery"""
    delivery = models.ForeignKey(
        PurchaseDelivery, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name='Доставка'
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT,
        verbose_name='Продукт'
    )
    quantity = models.IntegerField(verbose_name='Количество')
    purchase_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Доставна цена'
    )
    
    class Meta:
        verbose_name = 'Purchase Delivery Item'
        verbose_name_plural = 'Purchase Delivery Items'
    
    def __str__(self):
        return f'{self.product.name} x {self.quantity}'
    
    def get_total(self):
        """Calculate total cost for this item"""
        return self.quantity * self.purchase_price


class StockMovement(models.Model):
    """Track all stock movements"""
    MOVEMENT_TYPES = [
        ('delivery', 'Входяща доставка'),
        ('sale', 'Продажба'),
        ('adjustment', 'Корекция'),
        ('return', 'Връщане'),
    ]
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT,
        related_name='stock_movements',
        verbose_name='Продукт'
    )
    movement_type = models.CharField(
        max_length=20, 
        choices=MOVEMENT_TYPES,
        verbose_name='Тип движение'
    )
    quantity = models.IntegerField(verbose_name='Количество')  # Positive for IN, negative for OUT
    reference = models.CharField(max_length=200, blank=True, verbose_name='Референция')
    notes = models.TextField(blank=True, verbose_name='Бележки')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name='Създадено от'
    )
    
    class Meta:
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.product.name} - {self.get_movement_type_display()} ({self.quantity})'
