"""
Post-deploy tasks for hosting without a terminal (cPanel "Execute python script").
Runs: migrate, collectstatic. Run from the project root:  python post_deploy.py
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402
from django.core.management import call_command  # noqa: E402

django.setup()

print("== migrate ==")
call_command("migrate", interactive=False)

print("== collectstatic ==")
call_command("collectstatic", interactive=False, verbosity=1)

print("Done.")
