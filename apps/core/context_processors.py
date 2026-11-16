from django.conf import settings

from .models import SiteSettings


def site_settings(request):
    """
    Add site settings to all templates context
    """
    try:
        settings_obj = SiteSettings.objects.first()
    except SiteSettings.DoesNotExist:
        settings_obj = None
    
    return {
        'site_settings': settings_obj,
        'contact_phone': settings.CONTACT_PHONE,
        'contact_email': settings.CONTACT_EMAIL,
    }
