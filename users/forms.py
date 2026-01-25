# users/forms.py
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User


class SignupForm(forms.ModelForm):
    """Django form for user registration with validation"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
            'class': 'form-input'
        }),
        validators=[validate_password],
        label=''
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm Password',
            'class': 'form-input'
        }),
        label=''
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'Email',
                'class': 'form-input'
            }),
            'first_name': forms.TextInput(attrs={
                'placeholder': 'First Name',
                'class': 'form-input'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Last Name',
                'class': 'form-input'
            }),
        }
        labels = {
            'email': '',
            'first_name': '',
            'last_name': '',
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise ValidationError({
                'confirm_password': 'Passwords do not match'
            })

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Email already registered')
        return email


class LoginForm(forms.Form):
    """Django form for user login"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email',
            'class': 'form-input'
        }),
        label=''
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
            'class': 'form-input'
        }),
        label=''
    )


class ProfileUpdateForm(forms.ModelForm):
    """Django form for profile updates"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Last Name'
            }),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name or not first_name.strip():
            raise ValidationError('First name cannot be empty')
        return first_name.strip()

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name or not last_name.strip():
            raise ValidationError('Last name cannot be empty')
        return last_name.strip()
    




class ForgotPasswordForm(forms.Form):
    """Form for requesting password reset"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email',
            'class': 'form-input'
        }),
        label=''
    )


class ResetPasswordForm(forms.Form):
    """Form for resetting password"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'New Password',
            'class': 'form-input'
        }),
        validators=[validate_password],
        label=''
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm Password',
            'class': 'form-input'
        }),
        label=''
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise ValidationError({
                'confirm_password': 'Passwords do not match'
            })

        return cleaned_data
    



