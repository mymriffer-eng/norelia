from urllib.parse import urlparse

from django.apps import AppConfig
from django.db.models.signals import post_migrate


def sync_site_domain(sender, **kwargs):
    """Keep django_site (used in allauth emails) in sync with SITE_URL."""
    from django.conf import settings
    from django.contrib.sites.models import Site

    domain = urlparse(settings.SITE_URL).netloc
    if not domain:
        return
    Site.objects.update_or_create(
        pk=settings.SITE_ID, defaults={'domain': domain, 'name': 'Norelia'}
    )


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core'

    def ready(self):
        post_migrate.connect(sync_site_domain, sender=self)
