from django.conf import settings

from .models import SiteSettings


def company_info(site):
    """Legal entity details shown on the site (footer, policies, contact page)."""
    return {
        'name': (site.company_name if site and site.company_name else '') or 'Norelia',
        'vat': site.company_vat if site else '',
        'vat_number': site.vat_number if site else '',
        'address': ((site.company_address or site.address) if site else ''),
    }


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
        'company': company_info(settings_obj),
        'contact_phone': settings.CONTACT_PHONE,
        'contact_email': settings.CONTACT_EMAIL,
        'free_shipping_threshold': settings.FREE_SHIPPING_THRESHOLD,
        'google_site_verification': settings.GOOGLE_SITE_VERIFICATION,
        'google_analytics_id': settings.GOOGLE_ANALYTICS_ID,
    }
