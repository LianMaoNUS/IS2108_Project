import re
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from admin_panel.models import Admin,Category,Product,Order
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

class AdminLoginForm(forms.Form):
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
        fields = ['username', 'password','password_check', 'role']
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

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['sku','product_name', 'description', 'unit_price', 'product_rating', 'quantity_on_hand', 'reorder_quantity', 'category']

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields  = ['username', 'age','gender','employment_status','occupation','education','household_size','has_children','monthly_income_sgd','preferred_category']


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer','status']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name','parent_category']

