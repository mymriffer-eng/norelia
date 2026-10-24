# Norelia - Korean Cosmetics E-commerce Platform

🌸 **Production-ready Django 5+ онлайн магазин за корейска козметика**

---

## 📋 Съдържание

- [Характеристики](#характеристики)
- [Технологии](#технологии)
- [Структура на проекта](#структура-на-проекта)
- [Инсталация](#инсталация)
- [Настройка](#настройка)
- [Първоначална настройка](#първоначална-настройка)
- [Стартиране](#стартиране)
- [Deployment](#deployment)
- [Администрация](#администрация)

---

## ✨ Характеристики

### MVP Функционалности

**Публична част:**
- ✅ Начална страница с Hero банер, категории, нови продукти, промоции
- ✅ Каталог с категории и продукти
- ✅ Детайлна страница на продукт
- ✅ Количка за пазаруване
- ✅ Checkout и създаване на поръчка
- ✅ Търсене на продукти
- ✅ Newsletter абонамент

**Потребителски профил:**
- ✅ Регистрация и вход (Email + Google OAuth)
- ✅ Управление на профил
- ✅ История на поръчките
- ✅ Преглед на поръчки

**Администрация:**
- ✅ Управление на категории (с изображения и SEO)
- ✅ Управление на продукти (множество снимки, наличност)
- ✅ Управление на поръчки (статуси)
- ✅ Складова система (PurchaseDelivery, StockMovement)
- ✅ Автоматично фактуриране
- ✅ PDF генериране на фактури
- ✅ Dashboard с статистики
- ✅ Оповестяване за ниски наличности

**SEO:**
- ✅ SEO полета за категории и продукти
- ✅ Автоматично генериране на sitemap.xml
- ✅ robots.txt

**Сигурност:**
- ✅ CSRF защита
- ✅ Security Headers
- ✅ HTTPS ready
- ✅ Login attempt limiting

---

## 🛠 Технологии

- **Backend:** Django 5.0+
- **Database:** PostgreSQL
- **Frontend:** Bootstrap 5, JavaScript
- **Authentication:** Django Allauth (Email, Google)
- **Styling:** Custom CSS with Montserrat font
- **PDF Generation:** ReportLab
- **Static Files:** WhiteNoise
- **Image Handling:** Pillow
- **Environment:** django-environ

---

## 📁 Структура на проекта

```
norelia/
├── config/                 # Django настройки
├── apps/
│   ├── core/              # Основно приложение
│   ├── accounts/          # Потребителски профили
│   ├── shop/              # Магазин
│   ├── inventory/         # Складова система
│   ├── orders/            # Поръчки
│   └── invoices/          # Фактури
├── templates/             # HTML templates
├── static/                # Static файлове (CSS, JS)
├── media/                 # User uploads
├── requirements.txt       # Python dependencies
├── manage.py             # Django management
└── README.md             # Тази документация
```

---

## 🚀 Инсталация

### 1. Клониране на проекта

```powershell
cd c:\norelia
```

### 2. Създаване на virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Инсталиране на dependencies

```powershell
pip install -r requirements.txt
```

---

## ⚙️ Настройка

### 1. Създаване на .env файл

Копирайте `.env.example` към `.env`:

```powershell
Copy-Item .env.example .env
```

### 2. Редактиране на .env

Редактирайте `.env` файла с вашите настройки:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here

DB_NAME=norelia_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_SECRET=your-google-secret
```

### 3. Създаване на PostgreSQL база данни

```sql
CREATE DATABASE norelia_db;
CREATE USER norelia_user WITH PASSWORD 'your-password';
ALTER ROLE norelia_user SET client_encoding TO 'utf8';
ALTER ROLE norelia_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE norelia_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE norelia_db TO norelia_user;
```

---

## 🎬 Първоначална настройка

### 1. Миграции

```powershell
python manage.py makemigrations
python manage.py migrate
```

### 2. Създаване на superuser

```powershell
python manage.py createsuperuser
```

### 3. Създаване на Site Settings

```powershell
python manage.py shell
```

```python
from apps.core.models import SiteSettings
SiteSettings.objects.create(
    site_name='Norelia',
    site_description='Korean Cosmetics Shop',
    phone='+359 88 000 0000',
    email='info@norelia.com',
    company_name='Norelia Ltd.',
    company_vat='BG123456789',
    free_shipping_threshold=100
)
exit()
```

### 4. Collect Static Files

```powershell
python manage.py collectstatic --noinput
```

---

## 🏃 Стартиране

### Development Server

```powershell
python manage.py runserver
```

Отворете браузър на: http://127.0.0.1:8000

**Admin Panel:** http://127.0.0.1:8000/admin

---

## 📦 Deployment

### Подготовка за Production

1. **Актуализирайте .env за production:**

```env
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

2. **Collect static files:**

```powershell
python manage.py collectstatic --noinput
```

3. **Миграции:**

```powershell
python manage.py migrate
```

### Deployment с Gunicorn

```powershell
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Deployment на Heroku

```powershell
# Инсталирайте Heroku CLI
heroku login
heroku create norelia-app

# Добавете PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Set config vars
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

### Deployment на DigitalOcean/AWS

1. Настройте Ubuntu сървър
2. Инсталирайте PostgreSQL, Nginx, Gunicorn
3. Конфигурирайте Nginx като reverse proxy
4. Настройте SSL с Let's Encrypt
5. Използвайте systemd за Gunicorn service

---

## 👨‍💼 Администрация

### Admin Dashboard

Влезте в админ панела: `/admin`

**Основни секции:**

1. **Core**
   - Site Settings - Общи настройки на сайта
   - Newsletter - Абонаменти
   - Testimonials - Отзиви

2. **Shop**
   - Categories - Управление на категории
   - Products - Управление на продукти
   - Product Images - Допълнителни снимки

3. **Inventory**
   - Suppliers - Доставчици
   - Product Inventory - Складови наличности
   - Purchase Deliveries - Входящи доставки
   - Stock Movements - История на движенията

4. **Orders**
   - Orders - Управление на поръчки
   - Order Items - Детайли на поръчки

5. **Invoices**
   - Invoices - Фактури (с PDF download)

### Често използвани операции

**Добавяне на продукт:**
1. Shop → Products → Add Product
2. Попълнете данни (име, SKU, цена, категория)
3. Качете изображение
4. Задайте наличност
5. Запазете

**Приемане на доставка:**
1. Inventory → Purchase Deliveries → Add
2. Добавете артикули
3. Отбележете като получена
4. Наличностите се актуализират автоматично

**Обработка на поръчка:**
1. Orders → Orders
2. Изберете поръчка
3. Променете статус на "Confirmed"
4. Фактура се генерира автоматично
5. Download PDF фактура

---

## 🎨 Персонализация

### Промяна на цветове

Редактирайте `static/css/main.css`:

```css
:root {
    --primary-color: #C59D5F;  /* Основен цвят */
    --light-pink: #FFE4E9;     /* Розово */
    --gold-accent: #D4AF37;    /* Златно */
}
```

### Добавяне на categorii

От admin панела: Shop → Categories → Add

### Настройка на email

Използвайте Gmail App Password:
1. Google Account → Security → 2-Step Verification
2. App passwords → Generate
3. Копирайте в `.env`

---

## 🔐 Сигурност

- ✅ CSRF tokens на всички форми
- ✅ XSS защита
- ✅ SQL Injection защита (Django ORM)
- ✅ Secure cookies в production
- ✅ HTTPS redirect в production
- ✅ Security headers

---

## 📝 Лиценз

Proprietary - All rights reserved.

---

## 📧 Контакти

За въпроси и поддръжка: info@norelia.com

---

**Built with ❤️ by Senior Django Architect**

**Tech Stack:** Django 5 | PostgreSQL | Bootstrap 5 | ReportLab
