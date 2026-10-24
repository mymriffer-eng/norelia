from django import forms
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile"""
    
    # User fields
    first_name = forms.CharField(max_length=30, required=False, label='Име')
    last_name = forms.CharField(max_length=30, required=False, label='Фамилия')
    email = forms.EmailField(required=True, label='Имейл')
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'city', 'address', 'postal_code', 'date_of_birth', 'receive_newsletter']
        labels = {
            'phone': 'Телефон',
            'city': 'Град',
            'address': 'Адрес',
            'postal_code': 'Пощенски код',
            'date_of_birth': 'Дата на раждане',
            'receive_newsletter': 'Абонирай се за bulletin',
        }
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'receive_newsletter': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
        
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            if field_name not in ['receive_newsletter']:
                field.widget.attrs['class'] = 'form-control'
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
        
        if commit:
            profile.save()
        
        return profile
