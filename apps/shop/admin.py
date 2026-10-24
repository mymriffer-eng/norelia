from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'order', 'products_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'order']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'image')
        }),
        ('SEO', {
            'fields': ('seo_title', 'seo_description')
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def products_count(self, obj):
        return obj.get_products_count()
    products_count.short_description = 'Products'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ['image', 'order', 'image_preview']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px;" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Preview'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'image_preview', 
        'name', 
        'sku', 
        'category', 
        'price_display',
        'stock_status',
        'is_featured',
        'is_active', 
        'created_at'
    ]
    list_filter = ['is_active', 'is_featured', 'category', 'created_at']
    search_fields = ['name', 'sku', 'brand', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'is_featured']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    inlines = [ProductImageInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'brand', 'category')
        }),
        ('Description', {
            'fields': ('short_description', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'old_price')
        }),
        ('Stock', {
            'fields': ('stock_quantity',)
        }),
        ('Images', {
            'fields': ('image', 'image_preview')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 200px;" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Image Preview'
    
    def price_display(self, obj):
        if obj.old_price:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} лв.</span> '
                '<span style="text-decoration: line-through;">{} лв.</span>',
                obj.price, obj.old_price
            )
        return f'{obj.price} лв.'
    price_display.short_description = 'Price'
    
    def stock_status(self, obj):
        if obj.stock_quantity == 0:
            color = 'red'
            status = 'Out of Stock'
        elif obj.stock_quantity < 10:
            color = 'orange'
            status = f'Low Stock ({obj.stock_quantity})'
        else:
            color = 'green'
            status = f'In Stock ({obj.stock_quantity})'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    stock_status.short_description = 'Stock Status'
    
    # Custom actions
    actions = ['make_active', 'make_inactive', 'make_featured']
    
    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Mark selected products as active"
    
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Mark selected products as inactive"
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
    make_featured.short_description = "Mark selected products as featured"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview', 'order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__name']
    readonly_fields = ['image_preview', 'created_at']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Preview'
