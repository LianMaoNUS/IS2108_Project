import re
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from admin_panel.models import Admin,Category,Product,Order,OrderItem
from customer_website.models import Customer
from AuroraMart.models import User
from .models import Review

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

class AdminUpdateForm(forms.ModelForm):
    password_check = forms.CharField(
        label="Re-enter password (leave blank to keep current)", 
        required=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Re-enter your password',
            'class': 'login_form'
        })
    )
    
    class Meta:
        model = Admin
        fields = ['username', 'password', 'password_check', 'role']
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Enter a unique username',
                'class': 'login_form'
            }),
            'password': forms.PasswordInput(attrs={
                'placeholder': 'Leave blank to keep current password',
                'class': 'login_form'
            }),
            'role': forms.Select(attrs={
                'class': 'login_form'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].required = False
        self.fields['password'].required = False
        self.fields['role'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        password_check = cleaned_data.get('password_check')

        if username and 'username' in self.changed_data:
            username_status = check_username(username)
            if username_status != "Valid":
                self.add_error('username', username_status)

        if password:
            password_status = check_password(password, password_check)
            if password_status != "Valid":
                self.add_error('password_check', password_status)
        else:
            cleaned_data.pop('password', None)
            cleaned_data.pop('password_check', None)
        
        return cleaned_data

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['sku','product_name', 'description', 'unit_price', 'product_rating', 'quantity_on_hand', 'reorder_quantity', 'category','subcategory']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['category'].queryset = Category.objects.filter(parent_category__isnull=True)
        self.fields['category'].empty_label = "Select a main category"
        self.fields['category'].widget.attrs.update({
            'id': 'id_category',
            'class': 'form-control category-selector'
        })

        if self.data and self.data.get('category'):
            try:
                category_id = self.data.get('category')
                selected_category = Category.objects.get(pk=category_id)
                self.fields['subcategory'].queryset = Category.objects.filter(parent_category=selected_category)
            except (ValueError, Category.DoesNotExist):
                self.fields['subcategory'].queryset = Category.objects.none()
        elif self.instance.pk and self.instance.category:
            self.fields['subcategory'].queryset = Category.objects.filter(
                parent_category=self.instance.category
            )
        else:
            self.fields['subcategory'].queryset = Category.objects.none()
        
        self.fields['subcategory'].empty_label = "Select a subcategory (optional)"
        self.fields['subcategory'].widget.attrs.update({
            'id': 'id_subcategory',
            'class': 'form-control subcategory-selector'
        })
        
        # Override the label_from_instance for subcategory to show only the name
        self.fields['subcategory'].label_from_instance = lambda obj: obj.name if obj else ""
    
    def clean_subcategory(self):
        """Custom validation for subcategory field"""
        category = self.cleaned_data.get('category')
        subcategory = self.cleaned_data.get('subcategory')
        
        if subcategory:
            # Validate that the subcategory belongs to the selected category
            if category and subcategory.parent_category != category:
                raise forms.ValidationError("Selected subcategory must belong to the selected main category.")
            
            # Validate that the subcategory is indeed a subcategory (has a parent)
            if not subcategory.parent_category:
                raise forms.ValidationError("Selected option is not a valid subcategory.")
        
        return subcategory

class CustomerForm(forms.ModelForm):
    password = forms.CharField(
        label="New Password (leave blank to keep current)",
        required=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter new password (optional)',
            'class': 'form-control'
        })
    )
    password_check = forms.CharField(
        label="Re-enter New Password",
        required=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Re-enter new password',
            'class': 'form-control'
        })
    )
    preferred_category = forms.ModelChoiceField(
        queryset=Category.objects.filter(parent_category__isnull=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_preferred_category'
        })
    )

    class Meta:
        model = Customer
        fields  = ['username', 'password', 'password_check', 'age','gender','employment_status','occupation','education','household_size','has_children','monthly_income_sgd','email','preferred_category']
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_check = cleaned_data.get('password_check')

        # Only validate password if a new one is provided
        if password:
            password_status = check_password(password, password_check)
            if password_status != "Valid":
                self.add_error('password_check', password_status)
        else:
            # If no password provided, remove it from cleaned_data to prevent overwriting
            cleaned_data.pop('password', None)
            cleaned_data.pop('password_check', None)
        
        return cleaned_data


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer','status','shipping_address','order_notes']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name','parent_category']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter parent_category to only show main categories (where parent_category is null)
        self.fields['parent_category'].queryset = Category.objects.filter(parent_category__isnull=True)
        self.fields['parent_category'].empty_label = "Select a main category (leave blank for main category)"

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['order_id','product','quantity','price_at_purchase']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['review_title', 'review_content', 'rating']
        widgets = {
            'review_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter review title'
            }),
            'review_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your experience with this product'
            }),
            'rating': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'review_title': 'Review Title',
            'review_content': 'Your Review',
            'rating': 'Rating'
        }