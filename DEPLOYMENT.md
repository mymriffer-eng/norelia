# 🚀 Norelia - Deployment Guide

Подробни инструкции за deployment на Norelia онлайн магазин.

---

## 📋 Преди deployment

### Checklist

- [ ] PostgreSQL база данни е настроена
- [ ] Всички environment variables са конфигурирани
- [ ] DEBUG е FALSE
- [ ] SECRET_KEY е сменен за production
- [ ] ALLOWED_HOSTS е настроен правилно
- [ ] Static files са събрани
- [ ] Migrations са приложени

---

## 🌐 Deployment на Heroku

### 1. Подготовка

```powershell
# Влезте в Heroku
heroku login

# Създайте ново приложение
heroku create norelia-shop

# Добавете PostgreSQL
heroku addons:create heroku-postgresql:mini
```

### 2. Config Vars

```powershell
heroku config:set SECRET_KEY="your-production-secret-key"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=".herokuapp.com"
heroku config:set DJANGO_SETTINGS_MODULE=config.settings

# Email settings
heroku config:set EMAIL_HOST_USER="your-email@gmail.com"
heroku config:set EMAIL_HOST_PASSWORD="your-app-password"

# Google OAuth (optional)
heroku config:set GOOGLE_CLIENT_ID="your-google-client-id"
heroku config:set GOOGLE_SECRET="your-google-secret"
```

### 3. Deploy

```powershell
# Инициализирайте git repo (ако не е направено)
git init
git add .
git commit -m "Initial commit"

# Добавете Heroku remote
heroku git:remote -a norelia-shop

# Push към Heroku
git push heroku main
```

### 4. Post-deployment

```powershell
# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser

# Collect static files (automatic with Procfile, but manual if needed)
heroku run python manage.py collectstatic --noinput
```

### 5. Отваряне на приложението

```powershell
heroku open
```

---

## 💧 Deployment на DigitalOcean

### 1. Създайте Droplet

- Ubuntu 22.04 LTS
- Минимум 1GB RAM
- SSH access

### 2. Първоначална настройка

```bash
# SSH към сървъра
ssh root@your-server-ip

# Update система
apt update && apt upgrade -y

# Инсталирайте dependencies
apt install python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx curl -y
```

### 3. PostgreSQL Setup

```bash
# Влезте в PostgreSQL
sudo -u postgres psql

# Създайте database и user
CREATE DATABASE norelia_db;
CREATE USER norelia_user WITH PASSWORD 'strong-password';
ALTER ROLE norelia_user SET client_encoding TO 'utf8';
ALTER ROLE norelia_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE norelia_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE norelia_db TO norelia_user;
\q
```

### 4. Клонирайте проекта

```bash
# Създайте директория за приложения
mkdir -p /var/www
cd /var/www

# Clone git repo
git clone https://github.com/your-username/norelia.git
cd norelia

# Създайте virtual environment
python3 -m venv venv
source venv/bin/activate

# Инсталирайте dependencies
pip install -r requirements.txt
pip install gunicorn
```

### 5. Environment Variables

```bash
# Създайте .env файл
nano .env
```

Попълнете:
```env
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

DB_NAME=norelia_db
DB_USER=norelia_user
DB_PASSWORD=strong-password
DB_HOST=localhost
DB_PORT=5432
```

### 6. Django Setup

```bash
# Migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser
```

### 7. Gunicorn Setup

```bash
# Тестване на Gunicorn
gunicorn --bind 0.0.0.0:8000 config.wsgi

# Създайте systemd service
sudo nano /etc/systemd/system/gunicorn.service
```

gunicorn.service:
```ini
[Unit]
Description=Gunicorn daemon for Norelia
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/norelia
ExecStart=/var/www/norelia/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/var/www/norelia/norelia.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Enable и стартирайте service
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

### 8. Nginx Setup

```bash
sudo nano /etc/nginx/sites-available/norelia
```

norelia (Nginx config):
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/norelia/staticfiles/;
    }

    location /media/ {
        alias /var/www/norelia/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/norelia/norelia.sock;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/norelia /etc/nginx/sites-enabled

# Test Nginx config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### 9. SSL с Let's Encrypt

```bash
# Инсталирайте Certbot
sudo apt install certbot python3-certbot-nginx -y

# Получете SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal (cron job вече е настроен)
sudo certbot renew --dry-run
```

### 10. Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

---

## 🐳 Deployment с Docker (Bonus)

### docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=norelia_db
      - POSTGRES_USER=norelia_user
      - POSTGRES_PASSWORD=strong-password

  web:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

---

## 📊 Мониторинг и Maintenance

### Logs

```bash
# Heroku
heroku logs --tail

# DigitalOcean
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/error.log
```

### Backup на база данни

```bash
# Heroku
heroku pg:backups:capture
heroku pg:backups:download

# DigitalOcean
pg_dump norelia_db > backup_$(date +%Y%m%d).sql
```

### Update на приложение

```bash
# Pull changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

---

## 🔧 Troubleshooting

### Problem: Static files не се зареждат

**Solution:**
```bash
python manage.py collectstatic --noinput
sudo chown -R www-data:www-data staticfiles/
```

### Problem: 502 Bad Gateway

**Solution:**
```bash
# Check Gunicorn
sudo systemctl status gunicorn
sudo journalctl -u gunicorn

# Restart
sudo systemctl restart gunicorn
```

### Problem: Database connection error

**Solution:**
- Проверете .env файла
- Проверете PostgreSQL статус: `sudo systemctl status postgresql`
- Проверете permissions

---

## 📧 Email настройка (Gmail)

1. Google Account → Security → 2-Step Verification → Enable
2. App passwords → Generate
3. Copy password към .env:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=generated-app-password
```

---

## 🎯 Performance Optimization

### Enable caching

```python
# In settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### CDN за static files

Използвайте AWS S3 или Cloudflare за static и media files.

---

## ✅ Post-Deployment Checklist

- [ ] Site е достъпен на production URL
- [ ] SSL certificate работи
- [ ] Admin panel е достъпен
- [ ] Email notifications работят
- [ ] Static files се зареждат
- [ ] Media uploads работят
- [ ] Database backups са настроени
- [ ] Monitoring е активиран
- [ ] Error tracking (Sentry) е настроен

---

**Успех с deployment! 🎉**
