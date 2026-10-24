from django.contrib import admin
from .models import SiteSettings, Newsletter, Testimonial


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Site Information', {
            'fields': ('site_name', 'site_description')
        }),
        ('Contact Details', {
            'fields': ('phone', 'email', 'address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'instagram_url')
        }),
        ('Business Information', {
            'fields': ('company_name', 'company_vat', 'company_address')
        }),
        ('SEO', {
            'fields': ('meta_keywords',)
        }),
        ('Shop Settings', {
            'fields': ('free_shipping_threshold',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion
        return False


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'subscribed_at', 'is_active']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email']
    date_hierarchy = 'subscribed_at'
    readonly_fields = ['subscribed_at']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'rating', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'rating']
    search_fields = ['name', 'text']
    list_editable = ['is_active', 'order']
    date_hierarchy = 'created_at'
