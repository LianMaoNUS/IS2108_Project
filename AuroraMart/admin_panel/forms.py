from django.contrib.auth.forms import AuthenticationForm
from django import forms
from AuroraMart.models import Admin

class AdminLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(
        attrs={
            'class': 'login_form', 
            'placeholder': 'Enter your username' 
        }
    ))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'login_form',
            'placeholder': 'Enter your password'
        }
    ))

class AdminSignupForm(forms.ModelForm):
    password_check = forms.CharField(
        label="Re-enter password", 
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Re-enter your password',
            'class': 'login_form'
        })
    )
    class Meta:
        model = Admin
        fields = ['username', 'password', 'role']
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Enter a unique username',
                'class': 'login_form'
            }),
            'password': forms.PasswordInput(attrs={
                'placeholder': 'Create a strong password',
                'class': 'login_form'
            }),
            'role': forms.Select(attrs={
                'class': 'login_form'
            }),
        }