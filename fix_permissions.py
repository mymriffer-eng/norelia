"""
Fixes file permissions so Apache/Passenger can read the application files.
Run from the project root (cPanel "Execute python script"):  python fix_permissions.py
Directories -> 755, files -> 644, .env stays private (600), executables keep +x.
"""
import os
import stat
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SKIP_DIRS = {".git"}
PRIVATE_FILES = {".env"}


def mode_of(path):
    return stat.S_IMODE(os.stat(path).st_mode)


def chmod(path, mode):
    before = mode_of(path)
    if before != mode:
        os.chmod(path, mode)
        print(f"{oct(before)} -> {oct(mode)}  {path}")


# Parent folder (e.g. ~/repositories) must be traversable
if BASE_DIR.parent.name == "repositories":
    chmod(BASE_DIR.parent, 0o755)

chmod(BASE_DIR, 0o755)

for root, dirs, files in os.walk(BASE_DIR):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for d in dirs:
        chmod(os.path.join(root, d), 0o755)
    for f in files:
        path = os.path.join(root, f)
        if os.path.islink(path):
            continue
        if f in PRIVATE_FILES and root == str(BASE_DIR):
            chmod(path, 0o600)
        elif mode_of(path) & stat.S_IXUSR:
            chmod(path, 0o755)
        else:
            chmod(path, 0o644)

passengerfile = BASE_DIR / "Passengerfile.json"
print("Passengerfile.json exists:", passengerfile.exists())
if passengerfile.exists():
    print("Passengerfile.json mode  :", oct(mode_of(passengerfile)))
print("Done.")
