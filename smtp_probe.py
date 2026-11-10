"""
Probes every realistic SMTP host/port combination from the machine it runs on
and prints which ones connect and authenticate, plus the .env lines to use.

Run on the hosting account:  python smtp_probe.py
The password is read from .env and is never printed.
"""
import os
import smtplib
import socket
import ssl
from pathlib import Path


def load_env(path: Path):
    if not path.exists():
        return
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = [p.strip() for p in line.split('=', 1)]
        if key:
            os.environ[key] = value.strip('"').strip("'")


load_env(Path(__file__).resolve().parent / '.env')

USER = os.getenv('EMAIL_HOST_USER', '').strip()
PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '').strip()
CONF_HOST = os.getenv('EMAIL_HOST', 'mail.norelia.bg').strip() or 'mail.norelia.bg'

if PASSWORD.startswith('PASTE_') or PASSWORD == 'your-app-password':
    PASSWORD = ''

hosts = ['localhost', '127.0.0.1', CONF_HOST, 'norelia.bg']
try:
    fqdn = socket.getfqdn()
    if fqdn and fqdn not in hosts:
        hosts.append(fqdn)
except Exception:
    pass

# (port, mode) -> mode: plain | ssl | starttls
ports = [(25, 'plain'), (26, 'plain'), (465, 'ssl'), (587, 'starttls')]

# Diagnostic only: certificate checks are skipped so connectivity can be
# separated from certificate-name problems (e.g. connecting to localhost).
ctx = ssl._create_unverified_context()

print('=== SMTP PROBE ===')
print(f'USER={USER or "(empty)"}  PASSWORD_SET={bool(PASSWORD)}')
print(f'Local hostname: {socket.gethostname()}\n')

working = []

for host in hosts:
    for port, mode in ports:
        label = f'{host}:{port} ({mode})'
        try:
            socket.create_connection((host, port), timeout=5).close()
        except Exception as e:
            print(f'[closed ] {label} -> {type(e).__name__}: {e}')
            continue

        status = 'connected'
        try:
            if mode == 'ssl':
                srv = smtplib.SMTP_SSL(host, port, timeout=10, context=ctx)
            else:
                srv = smtplib.SMTP(host, port, timeout=10)
            srv.ehlo()
            if mode in ('plain', 'starttls') and srv.has_extn('starttls'):
                srv.starttls(context=ctx)
                srv.ehlo()
            if USER and PASSWORD:
                srv.login(USER, PASSWORD)
                status = 'AUTH OK'
                working.append((host, port, mode))
            else:
                status = 'connected (no password in .env, auth skipped)'
            srv.quit()
        except smtplib.SMTPAuthenticationError as e:
            status = f'AUTH FAILED {e.smtp_code}'
        except Exception as e:
            status = f'connected, SMTP error {type(e).__name__}: {e}'
        print(f'[open   ] {label} -> {status}')

print()
if working:
    host, port, mode = working[0]
    print('RESULT: use these values in .env')
    print(f'EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend')
    print(f'EMAIL_HOST={host}')
    print(f'EMAIL_PORT={port}')
    print(f'EMAIL_USE_SSL={mode == "ssl"}')
    print(f'EMAIL_USE_TLS={mode == "starttls"}')
    print(f'EMAIL_HOST_USER={USER}')
    print('EMAIL_HOST_PASSWORD=<the mailbox password>')
else:
    print('RESULT: no combination authenticated.')
    print('- Every line "closed": outbound SMTP is blocked, ask hosting support.')
    print('- Any line "AUTH FAILED": that route works, fix the mailbox password.')
    print('- Any line "open" with auth skipped: put the real password in .env and rerun.')
