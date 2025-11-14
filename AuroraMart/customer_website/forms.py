import re
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from admin_panel.models import Category,Product,Order,OrderItem, Review
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

class CustomerSignupForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(
        attrs={
            'class': 'login_form', 
            'placeholder': 'Enter a unique username' 
        }
    ))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'login_form',
            'placeholder': 'Create a strong password'
        }
    ))
    password_check = forms.CharField(
        label="Re-enter password", 
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Re-enter your password',
            'class': 'login_form'
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check format first
            username_status = check_username(username)
            if username_status != "Valid":
                raise forms.ValidationError(username_status)
            
            # Check if username already exists
            if Customer.objects.filter(username=username).exists():
                raise forms.ValidationError("This username is already taken. Please choose a different one.")
        
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_check = cleaned_data.get('password_check')

        if password:
            password_status = check_password(password, password_check)
            if password_status != "Valid":
                self.add_error('password_check', password_status)
        
        return cleaned_data
    
class CustomerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            if field_name != 'username':
                field.required = True
            field.widget.attrs.update({'class': 'form-control'})
        
        if 'gender' in self.fields:
            self.fields['gender'].widget.choices = [('', 'Select Gender')] + list(self.fields['gender'].choices)[1:]
        if 'employment_status' in self.fields:
            self.fields['employment_status'].widget.choices = [('', 'Select Employment Status')] + list(self.fields['employment_status'].choices)[1:]
        if 'education' in self.fields:
            self.fields['education'].widget.choices = [('', 'Select Education Level')] + list(self.fields['education'].choices)[1:]
        if 'occupation' in self.fields:
            self.fields['occupation'].widget.choices = [('', 'Select Occupation')] + list(self.fields['occupation'].choices)[1:]
        if 'number_of_children' in self.fields:
            pass  # No choices needed for number input
                
        self.fields['age'].widget.attrs.update({'placeholder': 'Enter your age'})
        self.fields['household_size'].widget.attrs.update({'placeholder': 'Number of people in household'})
        self.fields['number_of_children'].widget.attrs.update({'placeholder': 'Number of children'})
        self.fields['monthly_income_sgd'].widget.attrs.update({'placeholder': 'Enter monthly income in SGD'})

    class Meta:
        model = Customer
        fields = ['username', 'age', 'gender', 'employment_status', 'occupation', 'education', 
                 'household_size', 'number_of_children', 'monthly_income_sgd']
        widgets = {
            'username': forms.HiddenInput(),
            'age': forms.NumberInput(attrs={
                'min': '1',
                'max': '120'
            }),
            'gender': forms.Select(),
            'employment_status': forms.Select(),
            'occupation': forms.Select(),
            'education': forms.Select(),
            'household_size': forms.NumberInput(attrs={
                'min': '1'
            }),
            'number_of_children': forms.NumberInput(attrs={
                'min': '0'
            }),
            'monthly_income_sgd': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0'
            }),
        }


class CheckoutForm(forms.Form):
    # Shipping Information
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
            'required': True
        })
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
            'required': True
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com',
            'required': True
        })
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+65 1234 5678',
            'required': True
        })
    )
    address = forms.CharField(
        max_length=255,
        min_length=5,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123 Main Street',
            'required': True
        })
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Singapore',
            'required': True
        })
    )
    postal_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123456',
            'required': True
        })
    )
    state = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'State/Province (Optional)'
        })
    )
    
    COUNTRY_CHOICES = [
        ('SG', 'Singapore'),
        ('US', 'United States'),
        ('GB', 'United Kingdom'),
        ('CA', 'Canada'),
        ('AU', 'Australia'),
        ('JP', 'Japan'),
        ('DE', 'Germany'),
        ('FR', 'France'),
    ]
    
    country = forms.ChoiceField(
        choices=[('', 'Select Country')] + COUNTRY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    
    # Payment Information
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'payment-method-radio'
        }),
        initial='credit_card'
    )
    
    # Credit Card Fields
    card_number = forms.CharField(
        max_length=19,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456',
            'maxlength': '19'
        })
    )
    card_holder = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'John Doe'
        })
    )
    expiry_date = forms.CharField(
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MM/YY',
            'maxlength': '5'
        })
    )
    cvv = forms.CharField(
        max_length=3,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123',
            'maxlength': '3'
        })
    )
    
    # Coupon Code
    coupon_code = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter coupon code (optional)',
            'id': 'coupon_code'
        })
    )
    
    # Order Notes
    order_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Any special delivery instructions...',
            'rows': 3
        })
    )
    
    # Terms and Conditions
    accept_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        error_messages={
            'required': 'You must accept the terms and conditions to proceed.'
        }
    )
    
    subscribe_newsletter = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove all non-digit characters for validation
            phone_digits = re.sub(r'\D', '', phone)
            if len(phone_digits) < 8:
                raise forms.ValidationError('Please enter a valid phone number.')
        return phone

    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number')
        payment_method = self.cleaned_data.get('payment_method')
        
        if payment_method == 'credit_card':
            if not card_number:
                raise forms.ValidationError('Card number is required for credit card payment.')
            
            # Remove spaces for validation
            card_digits = card_number.replace(' ', '')
            
            if not card_digits.isdigit():
                raise forms.ValidationError('Card number must contain only digits.')
            
            if len(card_digits) < 13 or len(card_digits) > 19:
                raise forms.ValidationError('Card number must be between 13 and 19 digits.')
            
            if not self._luhn_check(card_digits):
                raise forms.ValidationError('Please enter a valid card number.')
        
        return card_number

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get('expiry_date')
        payment_method = self.cleaned_data.get('payment_method')
        
        if payment_method == 'credit_card':
            if not expiry_date:
                raise forms.ValidationError('Expiry date is required for credit card payment.')
            
            if not re.match(r'^\d{2}/\d{2}$', expiry_date):
                raise forms.ValidationError('Expiry date must be in MM/YY format.')
            
            month, year = expiry_date.split('/')
            month = int(month)
            year = int('20' + year)
            
            if month < 1 or month > 12:
                raise forms.ValidationError('Please enter a valid month (01-12).')
            
            from datetime import datetime
            current_date = datetime.now()
            current_year = current_date.year
            current_month = current_date.month
            
            if year < current_year or (year == current_year and month < current_month):
                raise forms.ValidationError('Card has expired.')
        
        return expiry_date

    def clean_cvv(self):
        cvv = self.cleaned_data.get('cvv')
        payment_method = self.cleaned_data.get('payment_method')
        
        if payment_method == 'credit_card':
            if not cvv:
                raise forms.ValidationError('CVV is required for credit card payment.')
            
            if not cvv.isdigit() or len(cvv) < 3 or len(cvv) > 4:
                raise forms.ValidationError('CVV must be 3 or 4 digits.')
        
        return cvv

    def clean_card_holder(self):
        card_holder = self.cleaned_data.get('card_holder')
        payment_method = self.cleaned_data.get('payment_method')
        
        if payment_method == 'credit_card':
            if not card_holder:
                raise forms.ValidationError('Cardholder name is required for credit card payment.')
        
        return card_holder

    def clean_address(self):
        address = self.cleaned_data.get('address')
        if address:
            address = address.strip()

            if len(address) < 5:
                raise forms.ValidationError('Address must be at least 5 characters long.')
            
            if not re.search(r'[a-zA-Z]', address):
                raise forms.ValidationError('Address must contain at least one letter.')
            
            special_chars = re.findall(r'[^a-zA-Z0-9\s]', address)
            if len(special_chars) > len(address) * 0.5:
                raise forms.ValidationError('Address contains too many special characters.')
            
            if re.match(r'^\d+$', address):  
                raise forms.ValidationError('Address cannot be only numbers.')
            
            if re.match(r'^[^\w\s]+$', address): 
                raise forms.ValidationError('Address cannot be only special characters.')
        
        return address

    def clean_coupon_code(self):
        """Validate coupon code if provided"""
        coupon_code = self.cleaned_data.get('coupon_code')
        
        if coupon_code:
            coupon_code = coupon_code.upper().strip()
            from admin_panel.models import Coupon
            
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                if not coupon.is_active:
                    raise forms.ValidationError('This coupon is not active.')
                
                from django.utils import timezone
                # Use localdate() so validation compares dates in the project's timezone
                now = timezone.localdate()
                if not (coupon.valid_from <= now <= coupon.valid_until):
                    raise forms.ValidationError('This coupon is not valid at this time.')
                
                if coupon.usage_limit > 0 and coupon.usage_count >= coupon.usage_limit:
                    raise forms.ValidationError('This coupon has reached its usage limit.')
                
            except Coupon.DoesNotExist:
                raise forms.ValidationError('Invalid coupon code.')
        
        return coupon_code

    def _luhn_check(self, card_number):
        """Luhn algorithm for credit card validation"""
        total = 0
        reverse_digits = card_number[::-1]
        
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        
        return total % 10 == 0

class ForgotPasswordForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'login_form',
            'placeholder': 'Enter your username'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'login_form',
            'placeholder': 'Enter your email address'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email required if it's in the POST data
        if self.data and self.data.get('email'):
            self.fields['email'].required = True
            # Make username readonly
            self.fields['username'].widget.attrs['readonly'] = True
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        try:
            Customer.objects.get(username=username)
        except Customer.DoesNotExist:
            raise forms.ValidationError("Username not found.")
        return username

class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter new password',
            'class': 'login_form'
        })
    )
    password_check = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Re-enter new password',
            'class': 'login_form'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_check = cleaned_data.get('password_check')
        
        if password:
            password_status = check_password(password, password_check)
            if password_status != "Valid":
                self.add_error('password_check', password_status)
        
        return cleaned_data
    
class ForgotPasswordForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(
        attrs={
            'class': 'login_form', 
            'placeholder': 'Enter your username' 
        }
    ))
    email = forms.EmailField(required=False, widget=forms.EmailInput(
        attrs={
            'class': 'login_form',
            'placeholder': 'Enter your email address'
        }
    ))
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check if username exists
            if not Customer.objects.filter(username=username).exists():
                raise forms.ValidationError("No account found with this username.")
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        
        # Only validate email if it's provided
        if username and email:
            # Check if username and email match
            try:
                customer = Customer.objects.get(username=username)
            except Customer.DoesNotExist:
                raise forms.ValidationError("No account found with this username.")
        
        return cleaned_data
    
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['review_title', 'review_content', 'rating']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'form-control'
            }),
            'review_content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your review here...',
                'rows': 4
            }),
        }