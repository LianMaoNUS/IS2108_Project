from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Customer
from admin_panel.models import Product, Category
from django.views import View
from .forms import CustomerLoginForm, CustomerSignupForm,CustomerForm
from django.contrib.auth.hashers import check_password
import pandas as pd
import joblib
import os
from decimal import Decimal

def error_check(check):
    return [msg for err_list in check for msg in err_list]


def convert_product_prices(products, currency_info):
    for product in products:
        converted_price = product.unit_price * currency_info['rate']
        product.unit_price = converted_price.quantize(Decimal('0.01'))
    return products


def predict_preferred_category(customer_data):
    model_path = os.path.join(os.path.dirname(__file__), 'prediction_data', 'b2c_customers_100.joblib')
    loaded_model = joblib.load(model_path)
    columns = {
        'age':'int64', 'household_size':'int64', 'has_children':'int64', 'monthly_income_sgd':'float64',
        'gender_Female':'bool', 'gender_Male':'bool', 'employment_status_Full-time':'bool',
        'employment_status_Part-time':'bool', 'employment_status_Retired':'bool',
        'employment_status_Self-employed':'bool', 'employment_status_Student':'bool',
        'occupation_Admin':'bool', 'occupation_Education':'bool', 'occupation_Sales':'bool',
        'occupation_Service':'bool', 'occupation_Skilled Trades':'bool', 'occupation_Tech':'bool',
        'education_Bachelor':'bool', 'education_Diploma':'bool', 'education_Doctorate':'bool',
        'education_Master':'bool', 'education_Secondary':'bool'
    }

    df = pd.DataFrame({col: pd.Series(dtype=dtype) for col, dtype in columns.items()})
    customer_df = pd.DataFrame([customer_data])
    customer_encoded = pd.get_dummies(customer_df, columns=['gender', 'employment_status', 'occupation', 'education'])    

    for col in df.columns:

        if col not in customer_encoded.columns:

            # Use False for bool columns, 0 for numeric
            if df[col].dtype == bool:
                df[col] = False
            else:
                df[col] = 0
        
        else:

            df[col] = customer_encoded[col]
    
    # Now input_encoded can be used for prediction
    prediction = loaded_model.predict(df)    

    return prediction

def get_recommendations( items, metric='confidence', top_n=5):
    model_path = os.path.join(os.path.dirname(__file__), 'prediction_data', 'b2c_customers_100.joblib')
    loaded_rules = joblib.load(model_path)
    recommendations = set()
    for item in items:

        # Find rules where the item is in the antecedents
        matched_rules = loaded_rules[loaded_rules['antecedents'].apply(lambda x: item in x)]
        # Sort by the specified metric and get the top N
        top_rules = matched_rules.sort_values(by=metric, ascending=False).head(top_n)

        for _, row in top_rules.iterrows():

            recommendations.update(row['consequents'])

    # Remove items that are already in the input list
    recommendations.difference_update(items)
    
    return list(recommendations)[:top_n]

def main_page(request):
    if request.GET.get('logout') == 'true':
        request.session.flush()
        return redirect('login')
    
    # Get selected currency from URL parameter
    selected_currency = request.GET.get('currency', 'SGD')
    
    # Currency conversion rates (base: SGD)
    currency_rates = {
        'SGD': {'rate': Decimal('1.0'), 'symbol': 'S$'},
        'USD': {'rate': Decimal('0.74'), 'symbol': '$'},
        'EUR': {'rate': Decimal('0.68'), 'symbol': '€'},
        'JPY': {'rate': Decimal('110.5'), 'symbol': '¥'},
        'GBP': {'rate': Decimal('0.58'), 'symbol': '£'}
    }
    
    # Get currency info
    currency_info = currency_rates.get(selected_currency, currency_rates['SGD'])
    
    categories = Category.objects.all()[:6]  # Show first 6 categories
    featured_products = Product.objects.all()[:8]  # Show first 8 products
    
    # Convert prices for each product
    convert_product_prices(featured_products, currency_info)
    
    return render(request, 'customer_website/main_page.html', {
        'categories': categories,
        'featured_products': featured_products,
        'selected_currency': selected_currency,
        'currency_symbol': currency_info['symbol'],
        'currency_rates': currency_rates
    })

class loginview(View):
    form_class = CustomerLoginForm
    template_name = 'customer_website/login.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                customer = Customer.objects.get(username=username)
                if check_password(password, customer.password):
                    request.session['hasLogin'] = True
                    request.session['username'] = username
                    request.session['profile_picture'] = customer.profile_picture
                    return redirect('customer_home')
                else:
                    form.add_error(None, "Incorrect password")
            except Customer.DoesNotExist:
                form.add_error(None, "User not found")
    
        return render(request, self.template_name, {"form": form, "error_message": error_check(form.errors.values())})
    

class signupview(View):
    form_class = CustomerSignupForm
    template_name = 'customer_website/signup.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            customer_username = form.cleaned_data.get('username')
            check_password = form.cleaned_data.get('password_check')
            if check_password == form.cleaned_data.get('password'):
                request.session['new_user'] = True
                request.session['new_user_username'] = customer_username
                request.session['new_user_password'] = form.cleaned_data.get('password')
                return redirect('new_user')
            else:
                form.add_error('password_check', "Passwords do not match")

        return render(request, self.template_name, {
                "form": form, 
                "error_message": error_check(form.errors.values())
            })


class new_userview(View):
    template_name = 'customer_website/new_user.html'
    customer_details_form_class = CustomerForm

    def get(self, request, *args, **kwargs):
        # Pre-populate username from session
        username = request.session.get('new_user_username')
        initial_data = {'username': username} if username else {}
        form = self.customer_details_form_class(initial=initial_data)
        return render(request, self.template_name, {"form": form})
    
    def post(self, request, *args, **kwargs):
        username = request.session.get('new_user_username')
        password = request.session.get('new_user_password')
        
        if not username or not password:
            return redirect('signup')
            
        form = self.customer_details_form_class(request.POST)
        
        if form.is_valid():
            customer_data = form.cleaned_data  
            customer_preferred = {
                'age': customer_data.get('age'),
                'gender': customer_data.get('gender'),
                'employment_status': customer_data.get('employment_status'),
                'occupation': customer_data.get('occupation'),
                'education': customer_data.get('education'),
                'household_size': customer_data.get('household_size'),
                'has_children': True if customer_data['has_children'] else False,
                'monthly_income_sgd': customer_data.get('monthly_income_sgd'),
            }
            preferred_category = predict_preferred_category(customer_preferred)
            
            # Create the customer instance manually
            customer = Customer(
                username=username,
                password=password,
                age=customer_data.get('age'),
                gender=customer_data.get('gender'),
                employment_status=customer_data.get('employment_status'),
                occupation=customer_data.get('occupation'),
                education=customer_data.get('education'),
                household_size=customer_data.get('household_size'),
                has_children= True if customer_data['has_children'] else False,
                monthly_income_sgd=customer_data.get('monthly_income_sgd'),
                preferred_category=preferred_category[0] if preferred_category else 'General'
            )
            
            # Save the customer
            customer.save()
            print(f"Predicted category: {preferred_category}")
            
            # Set up login session
            request.session['hasLogin'] = True
            request.session['username'] = username
            request.session['profile_picture'] = customer.profile_picture
            
            # Clear the signup session data
            request.session.pop('new_user', None)
            request.session.pop('new_user_username', None)
            request.session.pop('new_user_password', None)
            
            return redirect('customer_home')
        else:
            return render(request, self.template_name, {
                "form": form, 
                "error_message": error_check(form.errors.values())
            })       
        
class mainpageview(View):
    template_name = 'customer_website/main_page.html'

    def get(self, request, *args, **kwargs):
        if request.GET.get('logout') == 'true':
            request.session.flush()
            return redirect('login')
        user = Customer.objects.get(username=request.session.get('username'))
        main_category = Category.objects.filter(name=user.preferred_category)
        more_categories = Category.objects.exclude(name=user.preferred_category)[:5]
        products = Product.objects.filter(category__in=main_category).distinct()[:12]
        selected_currency = request.GET.get('currency', 'SGD')
        currency_rates = {
            'SGD': {'rate': Decimal('1.0'), 'symbol': 'S$'},
            'USD': {'rate': Decimal('0.74'), 'symbol': '$'},
            'EUR': {'rate': Decimal('0.68'), 'symbol': '€'},
            'JPY': {'rate': Decimal('110.5'), 'symbol': '¥'},
            'GBP': {'rate': Decimal('0.58'), 'symbol': '£'}
        }
        currency_info = currency_rates.get(selected_currency, currency_rates['SGD'])
        top_products = Product.objects.order_by('-reorder_quantity')[:10]

        convert_product_prices(products, currency_info)
        convert_product_prices(top_products, currency_info)

        return render(request, self.template_name, {
            'username': request.session.get('username'),
            'profile_picture': request.session.get('profile_picture'),
            'main_category': main_category,
            'more_categories': more_categories,
            'products': products,
            'selected_currency': selected_currency,
            'currency_symbol': currency_info['symbol'],
            'top_products': top_products,
        })


def cart_page(request):
    """Shopping cart page - placeholder for now"""
    return render(request, 'customer_website/cart.html', {
        'cart_items': [],  # Empty for now
        'subtotal': 0,
        'shipping': 0,
        'total': 0
    })

def checkout_page(request):
    """Checkout page - placeholder for now"""
    return render(request, 'customer_website/checkout.html', {
        'cart_items': [],
        'total': 0
    })

def profile_page(request):
    """Customer profile page"""
    if request.user.is_authenticated and hasattr(request.user, 'customer'):
        customer = request.user.customer
        # Get orders for this customer (you'll need to implement this)
        orders = []  # Placeholder
        return render(request, 'customer_website/profile.html', {
            'customer': customer,
            'orders': orders
        })
    else:
        messages.error(request, "Please log in to view your profile.")
        return redirect('login')

def product_detail(request, sku):
    """Product details page"""
    try:
        from admin_panel.models import Product
        product = Product.objects.get(sku=sku)
        # Placeholder for recommended products (AI integration later)
        recommended_products = Product.objects.exclude(sku=sku)[:4]
        return render(request, 'customer_website/product_detail.html', {
            'product': product,
            'recommended_products': recommended_products
        })
    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
        return redirect('all_products')

def about_page(request):
    """About us page"""
    return render(request, 'customer_website/about.html')

def all_products(request):
    """All products page"""
    from admin_panel.models import Product
    products = Product.objects.all()
    return render(request, 'customer_website/products.html', {
        'products': products
    })