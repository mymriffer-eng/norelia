from .models import SiteSettings


def site_settings(request):
    """
    Add site settings to all templates context
    """
    try:
        settings = SiteSettings.objects.first()
    except SiteSettings.DoesNotExist:
        settings = None
    
    return {
        'site_settings': settings,
    }
