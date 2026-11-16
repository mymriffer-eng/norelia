from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label='Име',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Вашето име'})
    )
    email = forms.EmailField(
        label='Имейл',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'})
    )
    phone = forms.CharField(
        max_length=30,
        required=False,
        label='Телефон (по желание)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0899...'})
    )
    message = forms.CharField(
        max_length=3000,
        label='Съобщение',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Как можем да ви помогнем?'})
    )
    # Honeypot: hidden from people, bots tend to fill it in
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'})
    )

    def clean_website(self):
        if self.cleaned_data.get('website'):
            raise forms.ValidationError('Spam detected.')
        return ''
