import os
import socket
import smtplib
from pathlib import Path

# Load .env if it exists
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / '.env')
except Exception:
    pass

host = os.getenv('EMAIL_HOST', '').strip()
port = int(os.getenv('EMAIL_PORT', '465'))
user = os.getenv('EMAIL_HOST_USER', '').strip()
password = os.getenv('EMAIL_HOST_PASSWORD', '').strip()
use_ssl = os.getenv('EMAIL_USE_SSL', 'False').lower() in ('1', 'true', 'yes')
use_tls = os.getenv('EMAIL_USE_TLS', 'False').lower() in ('1', 'true', 'yes')

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

    server.login(user, password)
    print('SMTP AUTH: SUCCESS')
    server.quit()
except Exception as e:
    print('SMTP AUTH: FAILED')
    print(f'ERROR: {type(e).__name__}: {e}')
    raise SystemExit(1)

print('RESULT: SMTP configuration appears to be valid from this server.')
