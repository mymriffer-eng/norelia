from django.db import models
from django.utils.crypto import get_random_string


def _newsletter_token():
    return get_random_string(40)


class SiteSettings(models.Model):
    """
    Site-wide settings for Norelia shop.
    Only one instance should exist.
    """
    site_name = models.CharField(max_length=100, default='Norelia')
    site_description = models.TextField(default='Korean Cosmetics Shop')
    
    # Contact info
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    
    # Social media
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    
    # SEO
    meta_keywords = models.TextField(blank=True, help_text='Comma separated keywords')
    
    # Business info
    company_name = models.CharField(max_length=200, blank=True)
    company_vat = models.CharField(max_length=50, blank=True, verbose_name='ЕИК/БУЛСТАТ')
    company_address = models.TextField(blank=True)
    
    # Settings
    free_shipping_threshold = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=100,
        help_text='Order total for free shipping'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteSettings.objects.exists():
            raise ValueError('Only one SiteSettings instance is allowed')
        return super().save(*args, **kwargs)


class Newsletter(models.Model):
    """
    Newsletter subscriptions (double opt-in).
    Only send to rows with is_active=True AND is_confirmed=True.
    """
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_confirmed = models.BooleanField(default=False, verbose_name='Потвърден абонамент')
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата на съгласието')
    token = models.CharField(max_length=40, default=_newsletter_token, editable=False, db_index=True)
    
    class Meta:
        verbose_name = 'Newsletter Subscription'
        verbose_name_plural = 'Newsletter Subscriptions'
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return self.email


class Testimonial(models.Model):
    """Customer testimonials"""
    name = models.CharField(max_length=100)
    text = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0, help_text='Display order')
    
    class Meta:
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f'{self.name} - {self.rating} stars'


class HeroSlide(models.Model):
    """Slide shown in the carousel in the hero section of the homepage"""
    image = models.ImageField(upload_to='hero/', verbose_name='Снимка', help_text='Препоръчително: хоризонтална снимка, поне 1200x800 px')
    alt_text = models.CharField(max_length=200, blank=True, verbose_name='Описание на снимката')
    link_url = models.CharField(max_length=300, blank=True, verbose_name='Връзка (по избор)', help_text='Напр. /categories/ или пълен адрес')
    order = models.IntegerField(default=0, verbose_name='Ред', help_text='По-малкото число се показва първо')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Слайд на началната страница'
        verbose_name_plural = 'Слайдове на началната страница'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.alt_text or f'Слайд {self.pk}'
