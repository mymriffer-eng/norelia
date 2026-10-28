"""
Creates (or updates) a superuser from .env variables, then you remove them.

Add temporarily to the server .env:
    ADMIN_EMAIL=you@example.com
    ADMIN_PASSWORD=a-strong-password
Run once:  python create_admin.py
Afterwards delete ADMIN_PASSWORD from .env.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

import environ  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402

env = environ.Env()
email = env("ADMIN_EMAIL", default="").strip().lower()
password = env("ADMIN_PASSWORD", default="")
username = env("ADMIN_USERNAME", default="admin").strip()

if not email or not password:
    sys.exit("ERROR: set ADMIN_EMAIL and ADMIN_PASSWORD in .env first.")
if len(password) < 8:
    sys.exit("ERROR: ADMIN_PASSWORD must be at least 8 characters.")

User = get_user_model()
user = User.objects.filter(email__iexact=email).first() or User.objects.filter(username=username).first()
created = user is None
if created:
    user = User(username=username, email=email)

user.email = email
user.is_staff = True
user.is_superuser = True
user.is_active = True
user.set_password(password)
user.save()

try:
    from allauth.account.models import EmailAddress

    EmailAddress.objects.update_or_create(
        user=user, email=email, defaults={"verified": True, "primary": True}
    )
except Exception as exc:  # allauth optional
    print(f"Note: could not register EmailAddress: {exc}")

print(f"Superuser {'created' if created else 'updated'}: username={user.username} email={user.email}")
print("Now REMOVE ADMIN_PASSWORD from .env.")
