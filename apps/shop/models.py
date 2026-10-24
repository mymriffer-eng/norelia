from django.db import models
from django.utils.text import slugify
from django.urls import reverse


class Category(models.Model):
    """Product categories"""
    name = models.CharField(max_length=200, unique=True, verbose_name='Име')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='URL')
    description = models.TextField(blank=True, verbose_name='Описание')
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='Изображение')
    
    # SEO fields
    seo_title = models.CharField(max_length=200, blank=True, verbose_name='SEO Title')
    seo_description = models.TextField(blank=True, verbose_name='SEO Description')
    
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    order = models.IntegerField(default=0, verbose_name='Подредба')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('shop:category_detail', kwargs={'slug': self.slug})
    
    def get_products_count(self):
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    """Product model"""
    name = models.CharField(max_length=200, verbose_name='Име на продукт')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='URL')
    sku = models.CharField(max_length=50, unique=True, verbose_name='SKU')
    brand = models.CharField(max_length=100, blank=True, verbose_name='Марка')
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='products',
        verbose_name='Категория'
    )
    
    short_description = models.CharField(max_length=500, blank=True, verbose_name='Кратко описание')
    description = models.TextField(blank=True, verbose_name='Описание')
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    old_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name='Стара цена'
    )
    
    # Stock (managed by inventory app)
    stock_quantity = models.IntegerField(default=0, verbose_name='Налична наличност')
    
    # Main image
    image = models.ImageField(upload_to='products/', verbose_name='Главно изображение')
    
    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True, verbose_name='Meta Title')
    meta_description = models.TextField(blank=True, verbose_name='Meta Description')
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_featured = models.BooleanField(default=False, verbose_name='Препоръчан')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукти'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Auto-generate meta fields if not provided
        if not self.meta_title:
            self.meta_title = self.name
        if not self.meta_description and self.short_description:
            self.meta_description = self.short_description
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('shop:product_detail', kwargs={'slug': self.slug})
    
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0
    
    def get_discount_percentage(self):
        """Calculate discount percentage"""
        if self.old_price and self.old_price > self.price:
            discount = ((self.old_price - self.price) / self.old_price) * 100
            return int(discount)
        return 0
    
    def get_related_products(self, limit=4):
        """Get related products from same category"""
        return Product.objects.filter(
            category=self.category,
            is_active=True
        ).exclude(id=self.id)[:limit]


class ProductImage(models.Model):
    """Additional product images"""
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='images',
        verbose_name='Продукт'
    )
    image = models.ImageField(upload_to='products/', verbose_name='Изображение')
    order = models.IntegerField(default=0, verbose_name='Подредба')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Изображение на продукт'
        verbose_name_plural = 'Изображения на продукти'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f'{self.product.name} - Image {self.id}'
