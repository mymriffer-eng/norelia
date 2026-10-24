from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'product_sku', 'quantity', 'price', 'subtotal']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number',
        'get_customer_name',
        'phone',
        'status_badge',
        'total_display',
        'payment_method',
        'created_at',
        'invoice_link'
    ]
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = [
        'order_number',
        'first_name',
        'last_name',
        'email',
        'phone',
        'user__email'
    ]
    readonly_fields = [
        'order_number',
        'user',
        'first_name',
        'last_name',
        'email',
        'phone',
        'city',
        'address',
        'notes',
        'payment_method',
        'subtotal',
        'shipping_cost',
        'total',
        'created_at',
        'updated_at'
    ]
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'status', 'user')
        }),
        ('Customer Details', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Delivery Address', {
            'fields': ('city', 'address')
        }),
        ('Order Details', {
            'fields': ('notes', 'payment_method')
        }),
        ('Totals', {
            'fields': ('subtotal', 'shipping_cost', 'total')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_customer_name(self, obj):
        return obj.get_full_name()
    get_customer_name.short_description = 'Customer'
    
    def status_badge(self, obj):
        color = obj.get_status_display_color()
        colors_map = {
            'info': '#17a2b8',
            'primary': '#007bff',
            'warning': '#ffc107',
            'success': '#28a745',
            'danger': '#dc3545',
            'secondary': '#6c757d',
        }
        bg_color = colors_map.get(color, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            bg_color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def total_display(self, obj):
        return format_html(
            '<strong>{} лв.</strong>',
            obj.total
        )
    total_display.short_description = 'Total'
    
    def invoice_link(self, obj):
        if obj.status in ['confirmed', 'shipped', 'delivered']:
            try:
                invoice = obj.invoice
                url = reverse('admin:invoices_invoice_change', args=[invoice.id])
                return format_html(
                    '<a href="{}" target="_blank">View Invoice</a>',
                    url
                )
            except:
                return '-'
        return '-'
    invoice_link.short_description = 'Invoice'
    
    def has_add_permission(self, request):
        # Orders are created through website, not admin
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion for audit trail
        return False
    
    # Custom actions
    actions = ['mark_as_confirmed', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']
    
    def mark_as_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
        self.message_user(request, f'{queryset.count()} orders marked as confirmed.')
    mark_as_confirmed.short_description = "Mark as Confirmed"
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
        self.message_user(request, f'{queryset.count()} orders marked as shipped.')
    mark_as_shipped.short_description = "Mark as Shipped"
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
        self.message_user(request, f'{queryset.count()} orders marked as delivered.')
    mark_as_delivered.short_description = "Mark as Delivered"
    
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f'{queryset.count()} orders marked as cancelled.')
    mark_as_cancelled.short_description = "Mark as Cancelled"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'price', 'subtotal']
    list_filter = ['order__created_at']
    search_fields = ['order__order_number', 'product_name', 'product_sku']
    readonly_fields = ['order', 'product', 'product_name', 'product_sku', 'quantity', 'price', 'subtotal']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
