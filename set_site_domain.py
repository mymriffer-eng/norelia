"""
Sets the Django Sites domain (django_site table) from SITE_URL in .env.
Run once after changing the domain:  python set_site_domain.py
"""
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

import environ  # noqa: E402
from django.conf import settings  # noqa: E402
from django.contrib.sites.models import Site  # noqa: E402

site_url = environ.Env()("SITE_URL")
domain = urlparse(site_url).netloc
site, _ = Site.objects.get_or_create(pk=settings.SITE_ID, defaults={"domain": domain, "name": "Norelia"})
site.domain = domain
site.name = "Norelia"
site.save()
print(f"Site {site.pk} set to domain: {site.domain}")
