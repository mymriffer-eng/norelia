from django.db import transaction
from .models import Order, OrderItem
from apps.inventory.services import InventoryService


class OrderService:
    """Service for handling order operations"""
    
    @transaction.atomic
    def create_order(self, order_data):
        """
        Create order from cart
        order_data should contain:
        - user (optional)
        - first_name, last_name, email, phone
        - city, address
        - notes (optional)
        - payment_method
        - cart_items (list of dicts with product, quantity, subtotal)
        - total
        """
        
        # Extract data
        user = order_data.get('user')
        cart_items = order_data.pop('cart_items')
        shipping_cost = self.calculate_shipping(order_data.get('total', 0))
        
        # Create order
        order = Order.objects.create(
            user=user,
            first_name=order_data['first_name'],
            last_name=order_data['last_name'],
            email=order_data['email'],
            phone=order_data['phone'],
            city=order_data['city'],
            address=order_data['address'],
            notes=order_data.get('notes', ''),
            payment_method=order_data.get('payment_method', 'cod'),
            subtotal=order_data['total'],
            shipping_cost=shipping_cost,
            total=order_data['total'] + shipping_cost,
            status='new'
        )
        
        # Create order items and reserve stock
        for item in cart_items:
            product = item['product']
            quantity = item['quantity']
            
            # Check stock availability
            if not product.is_in_stock() or product.stock_quantity < quantity:
                # Rollback transaction
                raise ValueError(f'Insufficient stock for {product.name}')
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_sku=product.sku,
                quantity=quantity,
                price=product.price,
                subtotal=item['subtotal']
            )
            
            # Reserve stock
            InventoryService.reserve_stock(product, quantity)
        
        return order
    
    def calculate_shipping(self, subtotal):
        """Calculate shipping cost"""
        from django.conf import settings
        
        # Free shipping threshold from settings
        free_shipping_threshold = getattr(settings, 'FREE_SHIPPING_THRESHOLD', 100)
        
        if subtotal >= free_shipping_threshold:
            return 0
        
        # Default shipping cost
        return 5.00
    
    @transaction.atomic
    def confirm_order(self, order):
        """
        Confirm order and update inventory
        """
        if order.status != 'new':
            return False
        
        # Update order status
        order.status = 'confirmed'
        order.save()
        
        # Update inventory for each item
        for item in order.items.all():
            InventoryService.confirm_sale(
                product=item.product,
                quantity=item.quantity,
                reference=f'Order #{order.order_number}'
            )
        
        # Generate invoice
        from apps.invoices.services import InvoiceService
        invoice_service = InvoiceService()
        invoice_service.create_invoice_for_order(order)
        
        return True
    
    @transaction.atomic
    def cancel_order(self, order):
        """
        Cancel order and release reserved stock
        """
        if order.status in ['delivered', 'cancelled']:
            return False
        
        # Update order status
        order.status = 'cancelled'
        order.save()
        
        # Release reserved stock
        for item in order.items.all():
            if order.status == 'new':
                # Only release if not yet confirmed
                InventoryService.release_reserved_stock(item.product, item.quantity)
        
        return True
    
    def get_order_statistics(self, date_from=None, date_to=None):
        """Get order statistics"""
        from django.db.models import Sum, Count, Avg
        from django.utils import timezone
        
        queryset = Order.objects.all()
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        stats = queryset.aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total'),
            average_order_value=Avg('total')
        )
        
        return stats
