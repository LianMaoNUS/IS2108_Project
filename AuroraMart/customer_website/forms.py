import re
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from admin_panel.models import Category,Product,Order,OrderItem
from customer_website.models import Customer
from AuroraMart.models import User

def check_username(username):
    if len(username) < 6:
        return "Username must be at least 6 characters long."
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return "Username can only contain letters, numbers, and underscores."
    return "Valid"
        
def check_password(password,check_password):
    if  password != check_password:
        return "Passwords do not match."
    elif len(password) < 8:
        return "Password must be at least 8 characters long."
    elif not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter."
    elif not re.search(r'[a-z]', password):
        return "Password must contain at least one lowercase letter."
    elif not re.search(r'[0-9]', password):
        return "Password must contain at least one digit."
    elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return "Password must contain at least one special character."
    else:
        return "Valid"

class CustomerLoginForm(forms.Form):
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

class CustomerSignupForm(forms.ModelForm):
    password_check = forms.CharField(
        label="Re-enter password", 
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Re-enter your password',
            'class': 'login_form'
        })
    )
    class Meta:
        model = Customer
        fields = ['username', 'password','password_check']
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

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        password_check = cleaned_data.get('password_check')

        if 'username' in self.changed_data:
            username_status = check_username(username)
            if username_status != "Valid":
                self.add_error('username', username_status)

        if password:
            password_status = check_password(password, password_check)
            if password_status != "Valid":
                self.add_error('password_check', password_status)
        
        return cleaned_data
    
class CustomerForm(forms.ModelForm):
<<<<<<< HEAD
    gender = forms.ChoiceField(
        choices=[('', 'Select Gender')] + Customer.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    employment_status = forms.ChoiceField(
        choices=[('', 'Select Employment Status')] + Customer.EMPLOYMENT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    education = forms.ChoiceField(
        choices=[('', 'Select Education Level')] + Customer.EDUCATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    occupation = forms.ChoiceField(
        choices=[('', 'Select Occupation')] + Customer.OCCUPATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    has_children = forms.ChoiceField(
        choices=[('', 'Select Option')] + Customer.HAS_CHILDREN_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            if field_name not in ['gender', 'employment_status', 'education', 'has_children']:
                field.widget.attrs.update({'class': 'form-control'})
                
        self.fields['age'].widget.attrs.update({'placeholder': 'Enter your age'})
        self.fields['occupation'].widget.attrs.update({'placeholder': 'Enter your occupation'})
        self.fields['household_size'].widget.attrs.update({'placeholder': 'Number of people in household'})
        self.fields['monthly_income_sgd'].widget.attrs.update({'placeholder': 'Enter monthly income in SGD'})

    class Meta:
        model = Customer
        fields = ['username', 'age', 'gender', 'employment_status', 'occupation', 'education', 
                 'household_size', 'has_children', 'monthly_income_sgd']
        widgets = {
            'username': forms.HiddenInput(),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '120'
            }),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'household_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'monthly_income_sgd': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
        }
=======
    class Meta:
        model = Customer
        fields  = ['username', 'age','gender','employment_status','occupation','education','household_size','has_children','monthly_income_sgd','preferred_category']
>>>>>>> 22aa262936ccb0cc0fa0b2c51c017d722aef8917
