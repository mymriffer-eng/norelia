from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extended user profile for customer information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Contact info
    phone = models.CharField(max_length=20, blank=True)
    
    # Default shipping address
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Additional info
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Preferences
    receive_newsletter = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f'{self.user.get_full_name() or self.user.email}'
    
    def get_full_name(self):
        """Return full name or email"""
        return self.user.get_full_name() or self.user.email


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
