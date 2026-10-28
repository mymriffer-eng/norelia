"""
Diagnostic script for cPanel deployment.
Run from the project root:  python diagnose.py
Prints environment, dependency, .env, settings, database and migration status.
Secrets are never printed (values are masked).
"""
import importlib
import os
import platform
import sys
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

SECRET_HINTS = ("SECRET", "PASSWORD", "KEY", "TOKEN")


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def run(title, func):
    section(title)
    try:
        func()
    except Exception:
        print("FAILED:")
        traceback.print_exc(file=sys.stdout)


def mask(key, value):
    if any(h in key.upper() for h in SECRET_HINTS):
        return f"<set, {len(value)} chars>" if value else "<EMPTY>"
    return value


def python_info():
    print("Python version  :", sys.version.replace("\n", " "))
    print("Executable      :", sys.executable)
    print("Platform        :", platform.platform())
    print("Project dir     :", BASE_DIR)
    print("CWD             :", os.getcwd())
    print("VIRTUAL_ENV     :", os.environ.get("VIRTUAL_ENV"))
    print("sys.prefix      :", sys.prefix)


def packages_info():
    mods = [
        "django", "environ", "allauth", "requests", "PIL", "whitenoise",
        "reportlab", "crispy_forms", "crispy_bootstrap5", "corsheaders",
        "slugify", "gunicorn", "MySQLdb", "pymysql", "psycopg2",
    ]
    for name in mods:
        try:
            mod = importlib.import_module(name)
            version = getattr(mod, "__version__", None) or getattr(mod, "VERSION", "")
            print(f"OK       {name:20} {version}  ({getattr(mod, '__file__', '')})")
        except Exception as exc:
            print(f"MISSING  {name:20} {type(exc).__name__}: {exc}")


def env_file_info():
    env_path = BASE_DIR / ".env"
    print(".env path   :", env_path)
    print(".env exists :", env_path.exists())
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if "=" not in line:
            print(f"BAD LINE (no '='): {line[:40]}")
            continue
        key, value = line.split("=", 1)
        print(f"{key.strip():28} = {mask(key.strip(), value.strip())}")


def settings_info():
    from django.conf import settings

    db = settings.DATABASES["default"]
    print("DEBUG           :", settings.DEBUG)
    print("ALLOWED_HOSTS   :", settings.ALLOWED_HOSTS)
    print("CSRF_TRUSTED    :", settings.CSRF_TRUSTED_ORIGINS)
    print("DB ENGINE       :", db["ENGINE"])
    print("DB NAME         :", db["NAME"])
    print("DB USER         :", db["USER"])
    print("DB PASSWORD     :", "<set>" if db["PASSWORD"] else "<EMPTY>")
    print("DB HOST         :", db["HOST"])
    print("DB PORT         :", db["PORT"])
    print("STATIC_ROOT     :", settings.STATIC_ROOT)
    print("STATIC_ROOT ok  :", Path(settings.STATIC_ROOT).exists())
    print("MEDIA_ROOT      :", settings.MEDIA_ROOT)
    print("SECURE_SSL_REDIR:", getattr(settings, "SECURE_SSL_REDIRECT", False))


def django_setup():
    import django

    django.setup()
    print("django.setup() OK, version", django.get_version())


def django_check():
    from django.core.management import call_command

    call_command("check")


def db_connection():
    from django.db import connection

    connection.ensure_connection()
    print("Connection OK, vendor:", connection.vendor)
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("SELECT 1 ->", cursor.fetchone())
        if connection.vendor == "mysql":
            cursor.execute("SELECT VERSION()")
            print("Server version:", cursor.fetchone()[0])
            cursor.execute("SELECT DATABASE()")
            print("Current DB    :", cursor.fetchone()[0])
    tables = connection.introspection.table_names()
    print(f"Tables in DB: {len(tables)}")
    for t in sorted(tables)[:60]:
        print("  -", t)


def migrations_info():
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    if not plan:
        print("All migrations applied.")
    else:
        print(f"{len(plan)} unapplied migration(s):")
        for migration, _ in plan:
            print("  -", migration)


def urls_info():
    from django.urls import get_resolver

    resolver = get_resolver()
    print("URL conf loaded OK, top-level patterns:", len(resolver.url_patterns))


def superuser_info():
    from django.contrib.auth import get_user_model

    User = get_user_model()
    print("Users total     :", User.objects.count())
    print("Superusers      :", User.objects.filter(is_superuser=True).count())


def wsgi_info():
    importlib.import_module("config.wsgi")
    print("config.wsgi imported OK")


def passenger_info():
    for name in ("passenger_wsgi.py", "wsgi.py"):
        path = BASE_DIR / name
        print(f"{name:20} exists: {path.exists()}")
    path = BASE_DIR / "passenger_wsgi.py"
    if path.exists():
        print("--- passenger_wsgi.py content ---")
        print(path.read_text(encoding="utf-8", errors="replace"))
        print("--- end ---")
    for log in ("stderr.log", "logs/passenger.log", "logs/django_errors.log", "tmp/restart.txt"):
        p = BASE_DIR / log
        print(f"{log:20} exists: {p.exists()}")
        if p.exists() and p.suffix == ".log":
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            print("\n".join(lines[-40:]))


def http_requests():
    from django.conf import settings
    from django.test import Client

    host = settings.ALLOWED_HOSTS[0]
    client = Client(SERVER_NAME=host, raise_request_exception=True)
    admin = "/" + settings.ADMIN_URL if hasattr(settings, "ADMIN_URL") else "/admin/"
    paths = ["/", "/accounts/login/", "/sitemap.xml", "/static/css/main.css"]
    try:
        import environ
        paths.append("/" + environ.Env()("ADMIN_URL", default="admin/"))
    except Exception:
        paths.append(admin)
    for path in paths:
        try:
            resp = client.get(path, secure=True)
            location = resp.headers.get("Location", "")
            print(f"GET {path:30} -> {resp.status_code} {location}")
        except Exception as exc:
            print(f"GET {path:30} -> EXCEPTION: {type(exc).__name__}: {exc}")
            tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
            print("".join(tb[-6:]))
            if exc.__cause__ or exc.__context__:
                cause = exc.__cause__ or exc.__context__
                print(f"  caused by: {type(cause).__name__}: {cause}")


if __name__ == "__main__":
    run("1. PYTHON / ENVIRONMENT", python_info)
    run("2. INSTALLED PACKAGES", packages_info)
    run("3. .ENV FILE (secrets masked)", env_file_info)
    run("4. DJANGO SETUP (imports settings + all apps)", django_setup)
    run("5. EFFECTIVE SETTINGS", settings_info)
    run("6. DATABASE CONNECTION", db_connection)
    run("7. MIGRATIONS", migrations_info)
    run("8. USERS", superuser_info)
    run("9. DJANGO CHECK", django_check)
    run("10. URL CONF", urls_info)
    run("11. WSGI IMPORT", wsgi_info)
    run("12. PASSENGER FILES / LOGS", passenger_info)
    run("13. HTTP REQUESTS (Django test client)", http_requests)
    print("\nDone.")
