# 🚀 Norelia - Quick Start Guide

Бърз старт за локално development.

---

## ⚡ Express Setup (5 минути)

### 1. Предпоставки

- Python 3.12
- PostgreSQL 15+
- Git

### 2. Clone & Setup

```powershell
# Navigate to project
cd c:\norelia

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database

```sql
-- PostgreSQL
CREATE DATABASE norelia_db;
```

### 4. Environment

```powershell
# Copy env file
Copy-Item .env.example .env

# Edit .env with your settings
notepad .env
```

Минимални настройки:
```env
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
DB_NAME=norelia_db
DB_USER=postgres
DB_PASSWORD=your-password
```

### 5. Migrations

```powershell
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

```powershell
python manage.py createsuperuser
```

### 7. Run Server

```powershell
python manage.py runserver
```

Visit: http://127.0.0.1:8000

Admin: http://127.0.0.1:8000/admin

---

## 📝 First Steps

### Add Site Settings

1. Go to Admin → Core → Site Settings → Add
2. Fill in:
   - Site Name: Norelia
   - Description: Korean Cosmetics Shop
   - Phone, Email, etc.

### Add Categories

Admin → Shop → Categories → Add

Примери:
- Sheet Masks
- Eye Patches
- Serums
- Face Creams
- Cleansers
- Toners
- Sunscreens
- Gift Sets

### Add Products

Admin → Shop → Products → Add

За всеки продукт:
- Name, SKU, Brand
- Category
- Price
- Description
- Image
- Stock quantity

---

## 🎯 Testing Features

### Test Order Flow

1. Visit homepage
2. Browse products
3. Add to cart
4. Checkout
5. Complete order
6. Check admin for order
7. Change status to "Confirmed"
8. Invoice auto-generated

### Test Inventory

1. Admin → Inventory → Purchase Deliveries
2. Add new delivery
3. Add items
4. Mark as received
5. Stock auto-updated

---

## 🐛 Common Issues

**Issue:** ModuleNotFoundError
```powershell
pip install -r requirements.txt
```

**Issue:** Database error
```powershell
# Check PostgreSQL is running
# Verify .env database settings
```

**Issue:** Static files not loading
```powershell
python manage.py collectstatic
```

---

## 📚 Next Steps

- Read [README.md](README.md) for detailed docs
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- Customize templates in `templates/`
- Modify styles in `static/css/main.css`

---

**Happy Coding! 🌸**
