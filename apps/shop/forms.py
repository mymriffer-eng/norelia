from django import forms


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
        label='Адрес',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 3,
            'placeholder': 'ул. Example 123, бл. 4, ап. 10'
        })
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
