from .models import ProductInventory, StockMovement
from apps.shop.models import Product


class InventoryService:
    """Service for managing inventory operations"""
    
    @staticmethod
    def get_or_create_inventory(product):
        """Get or create inventory for product"""
        inventory, created = ProductInventory.objects.get_or_create(
            product=product,
            defaults={
                'current_quantity': product.stock_quantity,
                'minimum_quantity': 10
            }
        )
        return inventory
    
    @staticmethod
    def adjust_stock(product, quantity, movement_type='adjustment', reference='', notes='', user=None):
        """
        Adjust stock for a product
        quantity: positive to add, negative to subtract
        """
        inventory = InventoryService.get_or_create_inventory(product)
        
        # Update quantity
        inventory.current_quantity += quantity
        if inventory.current_quantity < 0:
            inventory.current_quantity = 0
        inventory.save()
        
        # Create stock movement
        StockMovement.objects.create(
            product=product,
            movement_type=movement_type,
            quantity=quantity,
            reference=reference,
            notes=notes,
            created_by=user
        )
        
        return inventory
    
    @staticmethod
    def reserve_stock(product, quantity):
        """Reserve stock for order"""
        inventory = InventoryService.get_or_create_inventory(product)
        
        if inventory.available_quantity() >= quantity:
            inventory.reserved_quantity += quantity
            inventory.save()
            return True
        return False
    
    @staticmethod
    def release_reserved_stock(product, quantity):
        """Release reserved stock (e.g., order cancelled)"""
        inventory = InventoryService.get_or_create_inventory(product)
        inventory.reserved_quantity -= quantity
        if inventory.reserved_quantity < 0:
            inventory.reserved_quantity = 0
        inventory.save()
    
    @staticmethod
    def confirm_sale(product, quantity, reference='', user=None):
        """
        Confirm sale - subtract from current and reserved
        """
        inventory = InventoryService.get_or_create_inventory(product)
        
        # Subtract from current stock
        inventory.current_quantity -= quantity
        if inventory.current_quantity < 0:
            inventory.current_quantity = 0
        
        # Subtract from reserved
        inventory.reserved_quantity -= quantity
        if inventory.reserved_quantity < 0:
            inventory.reserved_quantity = 0
        
        inventory.save()
        
        # Create stock movement
        StockMovement.objects.create(
            product=product,
            movement_type='sale',
            quantity=-quantity,  # Negative for outgoing
            reference=reference,
            notes=f'Sale confirmed',
            created_by=user
        )
        
        return inventory
    
    @staticmethod
    def get_low_stock_products(threshold=None):
        """Get products with stock below minimum"""
        if threshold is None:
            from django.conf import settings
            threshold = getattr(settings, 'MINIMUM_STOCK_LEVEL', 10)
        
        return ProductInventory.objects.filter(
            current_quantity__lte=threshold
        ).select_related('product')
    
    @staticmethod
    def get_out_of_stock_products():
        """Get products with zero stock"""
        return ProductInventory.objects.filter(
            current_quantity=0
        ).select_related('product')
