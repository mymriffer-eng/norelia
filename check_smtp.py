import os
import socket
import smtplib
from pathlib import Path


def _read_env_file(env_path: Path):
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue

        key, value = [part.strip() for part in line.split('=', 1)]
        if not key or key in os.environ:
            continue

        os.environ[key] = value.strip().strip('"').strip("'")


def _as_bool(value):
    return str(value).strip().lower() in {'1', 'true', 'yes', 'y', 'on'}


_read_env_file(Path(__file__).resolve().parent / '.env')

host = os.getenv('EMAIL_HOST', '').strip()
port_value = os.getenv('EMAIL_PORT', '465').strip() or '465'
try:
    port = int(port_value)
except ValueError:
    port = 465

user = os.getenv('EMAIL_HOST_USER', '').strip()
password = os.getenv('EMAIL_HOST_PASSWORD', '').strip()
use_ssl = _as_bool(os.getenv('EMAIL_USE_SSL', 'False'))
use_tls = _as_bool(os.getenv('EMAIL_USE_TLS', 'False'))

if not use_ssl and host and port == 465:
    use_ssl = True

print('=== SMTP Check ===')
print(f'HOST={host}')
print(f'PORT={port}')
print(f'USE_SSL={use_ssl}')
print(f'USE_TLS={use_tls}')
print(f'USER={user}')
print(f'PASSWORD_SET={bool(password)}')

if not host:
    print('ERROR: EMAIL_HOST is empty')
    raise SystemExit(1)

try:
    sock = socket.create_connection((host, port), timeout=10)
    print(f'OPEN TCP: SUCCESS to {host}:{port}')
    sock.close()
except Exception as e:
    print(f'OPEN TCP: FAILED to {host}:{port}')
    print(f'ERROR: {type(e).__name__}: {e}')
    raise SystemExit(1)

try:
    if use_ssl:
        server = smtplib.SMTP_SSL(host, port, timeout=15)
    else:
        server = smtplib.SMTP(host, port, timeout=15)
        if use_tls:
            server.starttls()

    if user and password:
        server.login(user, password)
        print('SMTP AUTH: SUCCESS')
    else:
        print('SMTP AUTH: SKIPPED (missing user/password)')
    server.quit()
except Exception as e:
    print('SMTP AUTH: FAILED')
    print(f'ERROR: {type(e).__name__}: {e}')
    raise SystemExit(1)

print('RESULT: SMTP configuration appears to be valid from this server.')
