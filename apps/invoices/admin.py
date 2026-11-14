from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse, path
from django.http import HttpResponse, JsonResponse
from .models import Invoice, InvoiceItem, CatalogService, lookup_catalog_item
from .services import InvoiceService


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 3
    fields = [
        'product_sku', 'product_name', 'quantity', 'price',
        'unit_price_net_display', 'subtotal_net_display', 'subtotal',
    ]
    readonly_fields = ['unit_price_net_display', 'subtotal_net_display', 'subtotal']
    verbose_name = 'Артикул'
    verbose_name_plural = 'Артикули (въведете код на продукт или услуга и наименованието и цената се попълват сами)'
    
    def unit_price_net_display(self, obj):
        if obj.pk and obj.price is not None:
            return f'{obj.unit_price_net:.2f} €'
        return '-'
    unit_price_net_display.short_description = 'Ед. цена без ДДС (€)'
    
    def subtotal_net_display(self, obj):
        if obj.pk:
            return f'{obj.subtotal_net:.2f} €'
        return '-'
    subtotal_net_display.short_description = 'Сума без ДДС (€)'


@admin.register(CatalogService)
class CatalogServiceAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'price', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceItemInline]
    
    class Media:
        js = ('js/invoice_admin.js',)
    
    list_display = [
        'invoice_number',
        'invoice_date',
        'customer_name',
        'is_company_badge',
        'discount_display',
        'total_display',
        'order_link',
        'created_at',
        'actions_column'
    ]
    list_filter = ['invoice_date', 'is_company', 'created_at']
    search_fields = [
        'invoice_number',
        'customer_name',
        'customer_email',
        'company_vat',
        'order__order_number'
    ]
    readonly_fields = [
        'subtotal',
        'trade_discount_amount',
        'subtotal_after_discount',
        'total',
        'total_net_display',
        'total_vat_display',
        'created_at',
        'updated_at'
    ]
    date_hierarchy = 'invoice_date'
    
    fieldsets = (
        ('Информация за фактура', {
            'fields': ('invoice_number', 'invoice_date', 'order')
        }),
        ('Тип клиент', {
            'fields': ('is_company',)
        }),
        ('Данни на клиент', {
            'fields': (
                'customer_name', 
                'customer_email', 
                'customer_phone', 
                'customer_address'
            )
        }),
        ('Фирмени данни', {
            'fields': ('company_vat', 'company_vat_number', 'company_mol'),
            'classes': ('collapse',),
            'description': 'Попълнете само за фирмени клиенти'
        }),
        ('Суми (се пресмятат автоматично след запазване)', {
            'fields': (
                'subtotal', 
                'trade_discount_percent',
                'trade_discount_amount',
                'subtotal_after_discount',
                'shipping_cost', 
                'total_net_display',
                'total_vat_display',
                'total'
            )
        }),
        ('Бележки', {
            'fields': ('notes',)
        }),
        ('Системна информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_link(self, obj):
        if obj.order:
            url = reverse('admin:orders_order_change', args=[obj.order.id])
            return format_html(
                '<a href="{}">{}</a>',
                url, obj.order.order_number
            )
        return '-'
    order_link.short_description = 'Поръчка'
    
    def is_company_badge(self, obj):
        if obj.is_company:
            return mark_safe(
                '<span style="background-color: #007bff; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">ФИРМА</span>'
            )
        return mark_safe(
            '<span style="background-color: #6c757d; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">ЧАСТНО ЛИЦЕ</span>'
        )
    is_company_badge.short_description = 'Тип клиент'
    
    def discount_display(self, obj):
        if obj.trade_discount_percent > 0:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">{}% (-{} €)</span>',
                obj.trade_discount_percent,
                obj.trade_discount_amount
            )
        return '-'
    discount_display.short_description = 'Отстъпка'
    
    def total_display(self, obj):
        return format_html('<strong>{} €</strong>', obj.total)
    total_display.short_description = 'Обща сума'
    
    def total_net_display(self, obj):
        return f'{obj.total_net:.2f} €' if obj.pk else '-'
    total_net_display.short_description = 'Данъчна основа (без ДДС)'
    
    def total_vat_display(self, obj):
        return f'{obj.total_vat:.2f} €' if obj.pk else '-'
    total_vat_display.short_description = 'ДДС'
    
    def actions_column(self, obj):
        return format_html(
            '<a class="button" href="{}">Свали PDF</a>',
            reverse('admin:download_invoice_pdf', args=[obj.id])
        )
    actions_column.short_description = 'Действия'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'lookup-item/',
                self.admin_site.admin_view(self.lookup_item),
                name='invoice_lookup_item'
            ),
            path(
                '<int:invoice_id>/download-pdf/',
                self.admin_site.admin_view(self.download_pdf),
                name='download_invoice_pdf'
            ),
        ]
        return custom_urls + urls
    
    def lookup_item(self, request):
        """Return product/service name and price (with VAT) for a code"""
        found = lookup_catalog_item(request.GET.get('code', ''))
        if not found:
            return JsonResponse({'found': False})
        name, price = found
        return JsonResponse({'found': True, 'name': name, 'price': f'{price:.2f}'})
    
    def download_pdf(self, request, invoice_id):
        """Download invoice as PDF"""
        invoice = Invoice.objects.get(id=invoice_id)
        invoice_service = InvoiceService()
        
        pdf_buffer = invoice_service.generate_pdf(invoice)
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice-{invoice.invoice_number}.pdf"'
        
        return response
