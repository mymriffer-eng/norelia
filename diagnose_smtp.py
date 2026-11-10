import os
import socket
import ssl
from pathlib import Path


def load_env(path: Path):
    if not path.exists():
        return

    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue

        key, value = [part.strip() for part in line.split('=', 1)]
        if not key:
            continue

        os.environ[key] = value.strip().strip('"').strip("'")


def bool_env(name, default=False):
    val = str(os.getenv(name, str(default))).strip().lower()
    return val in {'1', 'true', 'yes', 'y', 'on'}


load_env(Path(__file__).resolve().parent / '.env')

host = os.getenv('EMAIL_HOST', '').strip()
port = int(os.getenv('EMAIL_PORT', '465') or 465)
user = os.getenv('EMAIL_HOST_USER', '').strip()
password = os.getenv('EMAIL_HOST_PASSWORD', '').strip()
use_ssl = bool_env('EMAIL_USE_SSL', True)
use_tls = bool_env('EMAIL_USE_TLS', False)

print('=== SMTP DIAG ===')
print(f'EMAIL_HOST={host}')
print(f'EMAIL_PORT={port}')
print(f'EMAIL_USE_SSL={use_ssl}')
print(f'EMAIL_USE_TLS={use_tls}')
print(f'EMAIL_HOST_USER={user}')
print(f'PASSWORD_SET={bool(password)}')

if not host:
    print('ERROR: missing EMAIL_HOST')
    raise SystemExit(1)

print('\n[1] TCP connect test')
try:
    sock = socket.create_connection((host, port), timeout=10)
    print(f'OK: TCP connection to {host}:{port} succeeded')
    sock.close()
except Exception as e:
    print(f'FAIL: TCP connection to {host}:{port} failed')
    print(f'ERROR: {type(e).__name__}: {e}')
    raise SystemExit(1)

print('\n[2] SSL handshake test')
try:
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=10) as raw_sock:
        with context.wrap_socket(raw_sock, server_hostname=host) as ssock:
            print(f'OK: SSL handshake succeeded with {host}:{port}')
            print(f'SSL_VERSION={ssock.version()}')
except Exception as e:
    print(f'FAIL: SSL handshake failed for {host}:{port}')
    print(f'ERROR: {type(e).__name__}: {e}')
    raise SystemExit(1)

print('\n[3] SMTP banner / greeting test')
try:
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=10) as raw_sock:
        with context.wrap_socket(raw_sock, server_hostname=host) as ssock:
            banner = ssock.recv(4096)
            print(f'BANNER={banner.decode(errors="replace").strip()}')
except Exception as e:
    print(f'FAIL: SMTP banner read failed')
    print(f'ERROR: {type(e).__name__}: {e}')
    raise SystemExit(1)

print('\n[4] SMTP AUTH test')
try:
    import smtplib
    server = smtplib.SMTP_SSL(host, port, timeout=15)
    server.ehlo()
    server.login(user, password)
    print('OK: SMTP AUTH succeeded')
    server.quit()
except Exception as e:
    print('FAIL: SMTP AUTH failed')
    print(f'ERROR: {type(e).__name__}: {e}')
    raise SystemExit(1)

print('\nRESULT: SMTP server is reachable and credentials are accepted.')
