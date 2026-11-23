import re

from django import forms

from apps.core.models import format_vat_number


class CheckoutForm(forms.Form):
    """Checkout form for order creation"""
    
    first_name = forms.CharField(
        max_length=50,
        label='Име',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Име'})
    )
    
    last_name = forms.CharField(
        max_length=50,
        label='Фамилия',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'})
    )
    
    email = forms.EmailField(
        label='Имейл',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'})
    )
    
    phone = forms.CharField(
        max_length=20,
        label='Телефон',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+359...'})
    )
    
    city = forms.CharField(
        max_length=100,
        label='Град',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'София'})
    )
    
    address = forms.CharField(
        label='Адрес за доставка',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 3,
            'placeholder': 'ул. Example 123, бл. 4, ап. 10 или офис на куриер'
        })
    )
    
    is_company = forms.BooleanField(
        required=False,
        label='Покупката е на фирма (искам фактура към фирма)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    company_name = forms.CharField(
        required=False,
        max_length=200,
        label='Фирма',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Наименование на фирмата'})
    )
    
    company_eik = forms.CharField(
        required=False,
        max_length=20,
        label='ЕИК',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ЕИК / БУЛСТАТ'})
    )
    
    company_vat_number = forms.CharField(
        required=False,
        max_length=20,
        label='ДДС номер (ако е регистрирана по ЗДДС)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'BG123456789'})
    )
    
    company_mol = forms.CharField(
        required=False,
        max_length=200,
        label='МОЛ',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Материално отговорно лице (по желание)'})
    )
    
    company_address = forms.CharField(
        required=False,
        label='Адрес на фирмата (по регистрация)',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Адрес за фактура'})
    )
    
    notes = forms.CharField(
        required=False,
        label='Бележки към поръчката',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Допълнителна информация (по желание)'
        })
    )
    
    payment_method = forms.ChoiceField(
        choices=[('cod', 'Наложен платеж')],
        initial='cod',
        label='Метод на плащане',
        widget=forms.RadioSelect()
    )
    
    def clean(self):
        cleaned = super().clean()
        company_fields = ['company_name', 'company_eik', 'company_vat_number', 'company_mol', 'company_address']
        
        if not cleaned.get('is_company'):
            for field in company_fields:
                cleaned[field] = ''
            return cleaned
        
        for field in ('company_name', 'company_eik', 'company_address'):
            if not (cleaned.get(field) or '').strip():
                self.add_error(field, 'Полето е задължително за фирми.')
        
        eik = re.sub(r'\s', '', cleaned.get('company_eik') or '')
        if eik and not re.fullmatch(r'\d{9}|\d{13}', eik):
            self.add_error('company_eik', 'ЕИК трябва да съдържа 9 или 13 цифри.')
        cleaned['company_eik'] = eik
        
        vat = format_vat_number(cleaned.get('company_vat_number'))
        if vat and not re.fullmatch(r'BG\d{9,10}', vat):
            self.add_error('company_vat_number', 'ДДС номерът трябва да е във формат BG и 9-10 цифри.')
        cleaned['company_vat_number'] = vat
        
        return cleaned
