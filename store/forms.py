import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Order


class UserRegisterForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'First Name (Optional)', 'class': 'form-input'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Last Name (Optional)', 'class': 'form-input'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address', 'class': 'form-input'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password (min 6 characters)', 'class': 'form-input'}),
        min_length=6
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-input'}),
        min_length=6
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Choose a Username', 'class': 'form-input'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise ValidationError("Please enter an email address.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email address is already registered. Please log in or use another email.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise ValidationError("Please enter a username.")
        if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            raise ValidationError("Username can only contain letters, numbers, dots, hyphens, and underscores.")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please choose another username.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                self.add_error('password_confirm', "Passwords do not match.")
            else:
                try:
                    validate_password(password)
                except ValidationError as e:
                    self.add_error('password', e)
        return cleaned_data

    def save(self, commit=True):
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        first_name = self.cleaned_data.get('first_name', '')
        last_name = self.cleaned_data.get('last_name', '')

        if commit:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            return user
        else:
            user = super().save(commit=False)
            user.set_password(password)
            return user


class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Username or Email', 'class': 'form-input', 'autocomplete': 'username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-input', 'autocomplete': 'current-password'})
    )


class CheckoutForm(forms.ModelForm):
    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery (Pay upon arrival)'),
        ('simulated', 'Simulated Online Payment / UPI / Card (Instant Confirmation)'),
    ]

    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'payment-radio'}),
        initial='cod'
    )

    class Meta:
        model = Order
        fields = [
            'full_name',
            'email',
            'phone',
            'address',
            'city',
            'state',
            'postal_code',
            'payment_method',
            'notes',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Full Name', 'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address', 'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'placeholder': '10-digit Mobile Number', 'class': 'form-input'}),
            'address': forms.Textarea(attrs={'placeholder': 'Flat/House no., Building, Street Address, Landmark', 'rows': 3, 'class': 'form-input'}),
            'city': forms.TextInput(attrs={'placeholder': 'City', 'class': 'form-input'}),
            'state': forms.TextInput(attrs={'placeholder': 'State', 'class': 'form-input'}),
            'postal_code': forms.TextInput(attrs={'placeholder': '6-digit PIN Code', 'class': 'form-input'}),
            'notes': forms.Textarea(attrs={'placeholder': 'Optional delivery instructions or notes', 'rows': 2, 'class': 'form-input'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        # Clean out common separators like spaces or dashes
        digits_only = re.sub(r'[\s\-+()]', '', phone)
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise ValidationError("Please enter a valid 10 to 15-digit contact number.")
        return phone

    def clean_postal_code(self):
        postal_code = self.cleaned_data.get('postal_code', '').strip()
        if len(postal_code) < 4 or len(postal_code) > 10:
            raise ValidationError("Please enter a valid postal / PIN code.")
        return postal_code
