from django.contrib.auth.forms import AuthenticationForm
from django import forms
from AuroraMart.models import Admin, Product, Customer, Order, Category

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

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['sku','product_name', 'description', 'unit_price', 'product_rating', 'quantity_on_hand', 'reorder_quantity', 'category']

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields  = ['customer_id','username', 'age','gender','employment_status','occupation','education','household_size','has_children','monthly_income_sgd','preferred_category']

    

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_id','customer','status']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_id','name','parent_category']