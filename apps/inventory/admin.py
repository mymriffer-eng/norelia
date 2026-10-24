from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Supplier, ProductInventory, PurchaseDelivery, PurchaseDeliveryItem, StockMovement


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'email', 'phone']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProductInventory)
class ProductInventoryAdmin(admin.ModelAdmin):
    list_display = [
        'product',
        'current_quantity',
        'reserved_quantity',
        'available_display',
        'minimum_quantity',
        'stock_status',
        'updated_at'
    ]
    list_filter = ['updated_at']
    search_fields = ['product__name', 'product__sku']
    readonly_fields = ['updated_at']
    
    def available_display(self, obj):
        return obj.available_quantity()
    available_display.short_description = 'Available'
    
    def stock_status(self, obj):
        if obj.current_quantity == 0:
            color = 'red'
            status = 'OUT OF STOCK'
        elif obj.needs_restock():
            color = 'orange'
            status = 'LOW STOCK'
        else:
            color = 'green'
            status = 'IN STOCK'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    stock_status.short_description = 'Status'


class PurchaseDeliveryItemInline(admin.TabularInline):
    model = PurchaseDeliveryItem
    extra = 1
    fields = ['product', 'quantity', 'purchase_price', 'total_display']
    readonly_fields = ['total_display']
    
    def total_display(self, obj):
        if obj.id:
            return f'{obj.get_total()} лв.'
        return '-'
    total_display.short_description = 'Total'


@admin.register(PurchaseDelivery)
class PurchaseDeliveryAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number',
        'supplier',
        'delivery_date',
        'total_cost',
        'is_received',
        'received_at',
        'created_at'
    ]
    list_filter = ['is_received', 'delivery_date', 'supplier']
    search_fields = ['invoice_number', 'supplier__name']
    readonly_fields = ['is_received', 'received_at', 'created_at', 'updated_at', 'total_cost']
    inlines = [PurchaseDeliveryItemInline]
    date_hierarchy = 'delivery_date'
    
    fieldsets = (
        ('Delivery Information', {
            'fields': ('supplier', 'invoice_number', 'delivery_date', 'notes')
        }),
        ('Status', {
            'fields': ('is_received', 'received_at')
        }),
        ('Summary', {
            'fields': ('total_cost',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['receive_deliveries']
    
    def total_cost(self, obj):
        if obj.id:
            return f'{obj.get_total_cost()} лв.'
        return '-'
    total_cost.short_description = 'Total Cost'
    
    def receive_deliveries(self, request, queryset):
        """Action to receive selected deliveries"""
        received_count = 0
        for delivery in queryset:
            if not delivery.is_received:
                try:
                    delivery.receive_delivery()
                    received_count += 1
                except Exception as e:
                    self.message_user(request, f'Error receiving {delivery}: {str(e)}', level='error')
        
        if received_count:
            self.message_user(request, f'Successfully received {received_count} deliveries.')
    
    receive_deliveries.short_description = "Receive selected deliveries"


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        'product',
        'movement_type',
        'quantity_display',
        'reference',
        'created_at',
        'created_by'
    ]
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'product__sku', 'reference']
    readonly_fields = ['created_at', 'created_by']
    date_hierarchy = 'created_at'
    
    def quantity_display(self, obj):
        color = 'green' if obj.quantity > 0 else 'red'
        sign = '+' if obj.quantity > 0 else ''
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}</span>',
            color, sign, obj.quantity
        )
    quantity_display.short_description = 'Quantity'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of stock movements for audit trail
        return False
