"""
URL configuration for Norelia project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from apps.shop.sitemaps import ProductSitemap, CategorySitemap

# Sitemaps
sitemaps = {
    'products': ProductSitemap,
    'categories': CategorySitemap,
}

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Apps
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('', include('apps.shop.urls')),
    path('orders/', include('apps.orders.urls')),
    path('invoices/', include('apps.invoices.urls')),
    
    # Django Allauth
    path('accounts/', include('allauth.urls')),
    
    # Sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

# Admin site customization
admin.site.site_header = "Norelia Administration"
admin.site.site_title = "Norelia Admin"
admin.site.index_title = "Welcome to Norelia Admin Panel"

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
