import re
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from admin_panel.models import Admin,Category,Product,Order,OrderItem, Coupon, CouponUsage
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
        
        if self.instance.pk:
            self.fields['sku'].disabled = True
        
        self.fields['category'].queryset = Category.objects.filter(parent_category__isnull=True)
        self.fields['category'].empty_label = "Select a main category"
        self.fields['category'].widget.attrs.update({
            'id': 'id_category',
            'class': 'form-control category-selector',
            'onchange': 'categoryChanged(this.value)'
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
        fields  = ['username', 'age','gender','employment_status','occupation','education','household_size','number_of_children','monthly_income_sgd','preferred_category']


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

class CouponForm(forms.ModelForm):
    APPLICABLE_CHOICES = [
        ('', 'All Categories'),
    ]
    
    applicable_categories = forms.ChoiceField(
        choices=APPLICABLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        help_text="Select a main category or choose 'All Categories'"
    )
    
    assigned_customers = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        help_text="Select 'All Customers' or choose a specific customer to assign this coupon to"
    )
    
    class Meta:
        model = Coupon
        fields = ['code', 'description', 'discount_percentage', 'minimum_order_value', 
                 'maximum_discount', 'valid_from', 'valid_until', 'usage_limit', 'is_active', 
                 'applicable_categories']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., SAVE20, WELCOME10'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description of the coupon'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'minimum_order_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'maximum_discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'valid_from': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'valid_until': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'usage_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'is_active': forms.Select(
                choices=[(True, 'Yes'), (False, 'No')],
                attrs={'class': 'form-control'}
            )
        }
        labels = {
            'code': 'Coupon Code',
            'discount_percentage': 'Discount Percentage (%)',
            'minimum_order_value': 'Minimum Order Value',
            'maximum_discount': 'Maximum Discount Amount',
            'valid_from': 'Valid From (Date)',
            'valid_until': 'Valid Until (Date)',
            'usage_limit': 'Usage Limit (0 = unlimited)',
            'is_active': 'Active',
            'applicable_categories': 'Applicable Main Category'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [('', 'All Categories')]
        for category in Category.objects.filter(parent_category__isnull=True):
            choices.append((str(category.pk), category.name))
        self.fields['applicable_categories'].choices = choices
        
        # Set up assigned_customers choices
        customer_choices = [('', 'All Customers')]
        for customer in Customer.objects.all():
            customer_choices.append((str(customer.customer_id), customer.username))
        self.fields['assigned_customers'].choices = customer_choices
        
        # Set initial value for applicable_categories
        if self.instance and self.instance.pk:
            if self.instance.applicable_categories.exists():
                # If coupon has specific categories, show the first one
                # (Since we're changing to single category, we'll take the first)
                first_category = self.instance.applicable_categories.first()
                if first_category:
                    self.fields['applicable_categories'].initial = str(first_category.pk)
            else:
                # No specific categories means "All Categories"
                self.fields['applicable_categories'].initial = ''
            
            # Set initial value for assigned_customers
            assigned_customers = self.instance.assigned_customers.all()
            if assigned_customers.exists():
                # If coupon has specific customers assigned, show the first one
                # (Since we're changing to single customer, we'll take the first)
                first_customer = assigned_customers.first()
                if first_customer:
                    self.fields['assigned_customers'].initial = str(first_customer.customer_id)
            else:
                # No specific customers means "All Customers"
                self.fields['assigned_customers'].initial = ''

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            # Check for existing coupons with the same code, excluding current instance if updating
            queryset = Coupon.objects.filter(code__iexact=code)
            if self.instance and self.instance.pk:
                # Exclude current instance when updating
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError("A coupon with this code already exists. Please choose a different code.")
        return code

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Save the instance first to ensure it has a primary key for many-to-many relationships
        if commit:
            instance.save()
        
        category_choice = self.cleaned_data.get('applicable_categories')
        if category_choice:  # Specific category selected
            try:
                category = Category.objects.get(pk=category_choice)
                instance.applicable_categories.set([category])
            except Category.DoesNotExist:
                instance.applicable_categories.clear()
        else:  
            instance.applicable_categories.clear()
    
        customer_choice = self.cleaned_data.get('assigned_customers')
        if customer_choice:
            try:
                customer = Customer.objects.get(customer_id=customer_choice)
                instance.assigned_customers.set([customer])
            except Customer.DoesNotExist:
                instance.assigned_customers.clear()
        else: 
            instance.assigned_customers.clear()
        
        return instance

class CouponUsageForm(forms.ModelForm):
    class Meta:
        model = CouponUsage
        fields = ['coupon', 'customer', 'order', 'discount_amount']
        widgets = {
            'coupon': forms.Select(attrs={
                'class': 'form-control'
            }),
            'customer': forms.Select(attrs={
                'class': 'form-control'
            }),
            'order': forms.Select(attrs={
                'class': 'form-control'
            }),
            'discount_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            })
        }
        labels = {
            'coupon': 'Coupon',
            'customer': 'Customer',
            'order': 'Order',
            'discount_amount': 'Discount Amount'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['coupon'].queryset = Coupon.objects.filter(is_active=True)
        self.fields['order'].queryset = Order.objects.filter(coupon__isnull=False).exclude(coupon='')
        self.fields['customer'].queryset = Customer.objects.filter(coupon_usages__isnull=False).distinct()
    