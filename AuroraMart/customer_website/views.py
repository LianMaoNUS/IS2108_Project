import os
import uuid
import joblib
from datetime import datetime, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.contrib.auth.hashers import check_password
from django.db.models import Case, When, Value, IntegerField, Sum, Q
from django.conf import settings

import pandas as pd

from admin_panel.models import Product, Category, Order, OrderItem, Review, Coupon, CouponUsage
from admin_panel.forms import ReviewForm as AdminReviewForm # Renamed to avoid conflict

from .models import Customer
from .forms import (
    CustomerLoginForm, CustomerSignupForm, CustomerForm,
    CheckoutForm, ForgotPasswordForm, ResetPasswordForm, ReviewForm
)

def error_check(check):
    return [msg for err_list in check for msg in err_list]


def get_currency_context(request):
    url_currency = request.GET.get('currency')
    if url_currency:
        request.session['selected_currency'] = url_currency
        request.session.modified = True
        selected_currency = url_currency
    else:
        selected_currency = request.session.get('selected_currency', 'SGD')
    
    currency_rates = {
        'SGD': {'rate': Decimal('1.0'), 'symbol': 'S$'},
        'USD': {'rate': Decimal('0.74'), 'symbol': '$'},
        'EUR': {'rate': Decimal('0.68'), 'symbol': '€'},
        'JPY': {'rate': Decimal('110.5'), 'symbol': '¥'},
        'GBP': {'rate': Decimal('0.58'), 'symbol': '£'}
    }
    
    currency_info = currency_rates.get(selected_currency, currency_rates['SGD'])
    return {
        'selected_currency': selected_currency,
        'currency_info': currency_info,
        'currency_symbol': currency_info['symbol'],
        'currency_rates': currency_rates
    }


def convert_product_prices(products, currency_info):
    for product in products:
        converted_price = product.unit_price * currency_info['rate']
        product.unit_price = converted_price.quantize(Decimal('0.01'))
    return products

def convert_cart_prices(product, currency_info):
    converted_price = Decimal(str(product)) * currency_info['rate']
    return converted_price.quantize(Decimal('0.01'))
 
def get_cart_count(request):
    cart = request.session.get('cart', {})
    return len(cart)


class BaseView(View):
    def get_base_context(self, request):
        base_context = {
            'username': request.session.get('customer_username'),
            'profile_picture': request.session.get('customer_profile_picture'),
            'cart_count': get_cart_count(request),
        }
        try:
            currency_context = get_currency_context(request)
            base_context.update(currency_context)
        except Exception:
            pass
        return base_context
    
    def render_with_base(self, request, template_name, context=None, status=None):
        context = context or {}
        base = self.get_base_context(request)
        merged = {**base, **context}
        if status is not None:
            return render(request, template_name, merged, status=status)
        return render(request, template_name, merged)


def make_coupon_code(prefix, customer=None, coupon_cat=None, length=4):
    base = str(prefix)
    if customer:
        try:
            base += customer.customer_id[10:15].upper()
        except Exception:
            pass
    elif coupon_cat:
        base += coupon_cat[:3].upper()

    for _ in range(5):
        suffix = uuid.uuid4().hex[:length].upper()
        candidate = f"{base}{suffix}"
        if not Coupon.objects.filter(code=candidate).exists():
            return candidate

    return f"{base}{int(datetime.now().timestamp()) % (10 ** length):0{length}d}"

model_path = os.path.join(os.path.dirname(__file__), 'prediction_data', 'b2c_customers_100.joblib')
try:
    preferred_model = joblib.load(model_path)
except Exception as e:
    preferred_model = None
    print(f"Could not load preferred category model: {e}")


def predict_preferred_category(customer_data):
    if preferred_model is None:
        return []
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

            if df[col].dtype == bool:
                df[col] = False
            else:
                df[col] = 0
        
        else:

            df[col] = customer_encoded[col]
    
    prediction = preferred_model.predict(df)

    return prediction

loaded_path = os.path.join(os.path.dirname(__file__), 'prediction_data', 'b2c_products_500_transactions_50k.joblib')
loaded_rules = joblib.load(loaded_path)
def get_recommendations(items, metric='confidence', top_n=5):
    mask = loaded_rules['antecedents'].apply(lambda x: any(item in x for item in items))
    relevant_rules = loaded_rules[mask]
    if len(relevant_rules) == 0:
        return []
    
    sorted_rules = relevant_rules.sort_values(by=metric, ascending=False)
    
    recommendations = set()
    for _, row in sorted_rules.head(top_n * 3).iterrows(): 
        recommendations.update(row['consequents'])
    
    recommendations.difference_update(items)
    return list(recommendations)[:top_n]


def get_next_best_action(request, current_category=None):
    actions = []
    
    try:
        preferred_category = request.session.get('preferred_category')
        browsing_history = request.session.get('browsing_history', [])
        
        cart = request.session.get('cart', {})
        cart_categories = set()
        
        for sku in cart.keys():
            try:
                product = Product.objects.get(sku=sku)
                if product.category:
                    cart_categories.add(product.category.name)
            except Product.DoesNotExist:
                pass
        
        all_categories = Category.objects.filter(parent_category__isnull=True)
        
        # Action 1: If viewing a category different from preferred, suggest preferred category
        if current_category and preferred_category and current_category != preferred_category:
            try:
                pref_cat = Category.objects.get(name=preferred_category)
                product_count = Product.objects.filter(category=pref_cat).count()
                if product_count > 0:
                    actions.append({
                        'type': 'explore_preferred',
                        'title': f'Explore Your Favorite: {preferred_category}',
                        'description': f'Discover {product_count} products in your preferred category',
                        'category_id': pref_cat.category_id,
                        'category_name': preferred_category,
                        'icon': 'fa-heart',
                        'color': '#f093fb'
                    })
            except Category.DoesNotExist:
                pass
        
        # Action 2: If cart has items, suggest complementary categories using recommendations
        if cart:
            cart_skus = list(cart.keys())
            recommended_skus = get_recommendations(cart_skus, top_n=5)
            print("Recommended SKUs:", recommended_skus)
            
            if recommended_skus:
                # Get categories from recommended products
                recommended_products = Product.objects.filter(sku__in=recommended_skus)
                recommended_categories = set()
                
                for product in recommended_products:
                    if product.category and product.category.name not in cart_categories:
                        if current_category is None or product.category.name != current_category:
                            recommended_categories.add(product.category)
                
                # Pick the first recommended category
                if recommended_categories:
                    rec_cat = list(recommended_categories)[0]
                    product_count = Product.objects.filter(category=rec_cat).count()
                    if product_count > 0:
                        actions.append({
                            'type': 'complementary',
                            'title': f'Complete Your Order with {rec_cat.name}',
                            'description': f'Based on your cart: Browse {product_count} complementary items',
                            'category_id': rec_cat.category_id,
                            'category_name': rec_cat.name,
                            'icon': 'fa-plus-circle',
                            'color': '#667eea'
                        })
            else:
                # Fallback: If no recommendations, suggest random category not in cart
                related_cats = all_categories.exclude(name__in=cart_categories)
                if current_category:
                    related_cats = related_cats.exclude(name=current_category)
                
                if related_cats.exists():
                    fallback_cat = related_cats.order_by('?').first()
                    product_count = Product.objects.filter(category=fallback_cat).count()
                    if product_count > 0:
                        actions.append({
                            'type': 'complementary',
                            'title': f'Complete Your Order with {fallback_cat.name}',
                            'description': f'Browse {product_count} complementary items',
                            'category_id': fallback_cat.category_id,
                            'category_name': fallback_cat.name,
                            'icon': 'fa-plus-circle',
                            'color': '#667eea'
                        }) 
        
        # Action 3: Suggest unexplored categories
        explored_categories = set(browsing_history) if browsing_history else set()
        if current_category:
            explored_categories.add(current_category)
        
        unexplored = all_categories.exclude(name__in=explored_categories)
        if unexplored.exists():
            unexplored_cat = unexplored.order_by('?').first() 
            product_count = Product.objects.filter(category=unexplored_cat).count()
            if product_count > 0:
                actions.append({
                    'type': 'discover',
                    'title': f'Discover {unexplored_cat.name}',
                    'description': f'New to you! Check out {product_count} products',
                    'category_id': unexplored_cat.category_id,
                    'category_name': unexplored_cat.name,
                    'icon': 'fa-compass',
                    'color': '#10b981'
                })
        
        # Action 4: Popular/trending category (based on product reorder quantity)
        popular_categories = Category.objects.filter(
            parent_category__isnull=True
        ).annotate(
            total_reorders=Sum('products__reorder_quantity')
        ).exclude(name=current_category).order_by('-total_reorders')[:1]
        
        if popular_categories.exists():
            pop_cat = popular_categories.first()
            product_count = Product.objects.filter(category=pop_cat).count()
            if product_count > 0:
                actions.append({
                    'type': 'trending',
                    'title': f'🔥 Trending: {pop_cat.name}',
                    'description': f'Hot picks! Explore {product_count} popular items',
                    'category_id': pop_cat.category_id,
                    'category_name': pop_cat.name,
                    'icon': 'fa-fire',
                    'color': '#f59e0b'
                })
        
        # Return up to 2 best actions
        return actions[:2]
        
    except Exception as e:
        print(f"Error in get_next_best_action: {str(e)}")
        return []


class loginview(BaseView):
    form_class = CustomerLoginForm
    template_name = 'customer_website/login.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return self.render_with_base(request, self.template_name, {"form": form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                customer = Customer.objects.get(username=username)
                if check_password(password, customer.password):
                    request.session['customer_hasLogin'] = True
                    request.session['customer_username'] = username
                    request.session['customer_profile_picture'] = customer.profile_picture
                    return redirect('customer_home')
                else:
                    form.add_error(None, "Incorrect password")
            except Customer.DoesNotExist:
                form.add_error(None, "User not found")
    
        return self.render_with_base(request, self.template_name, {"form": form, "error_message": error_check(form.errors.values())})
    

class signupview(BaseView):
    form_class = CustomerSignupForm
    template_name = 'customer_website/signup.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return self.render_with_base(request, self.template_name, {"form": form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            customer_username = form.cleaned_data.get('username')
            check_password = form.cleaned_data.get('password_check')
            if check_password == form.cleaned_data.get('password'):
                request.session['new_user'] = True
                request.session['new_user_username'] = customer_username
                request.session['new_user_password'] = form.cleaned_data.get('password')
                request.session['updating_profile'] = False
                return redirect('new_user')
            else:
                form.add_error('password_check', "Passwords do not match")

        return self.render_with_base(request, self.template_name, {
                "form": form, 
                "error_message": error_check(form.errors.values())
            })


class check_username_view(BaseView):
    def get(self, request, *args, **kwargs):
        username = request.GET.get('username', '').strip()
        
        if not username:
            return JsonResponse({'available': False, 'message': 'Username is required'})
        
        exists = Customer.objects.filter(username=username).exists()
        
        if exists:
            return JsonResponse({'available': False, 'message': 'Username already exists'})
        else:
            return JsonResponse({'available': True, 'message': 'Username is available'})


class new_userview(BaseView):
    template_name = 'customer_website/new_user.html'

    customer_details_form_class = CustomerForm

    def get(self, request, *args, **kwargs):
        logged_in_username = request.session.get('customer_username')
        if logged_in_username and not request.session.get('new_user_username'):
            try:
                customer = Customer.objects.get(username=logged_in_username)
                # Set sessions for profile update
                request.session['new_user_username'] = customer.username
                request.session['new_user_password'] = customer.password
                request.session['updating_profile'] = True
            except Customer.DoesNotExist:
                pass
        
        username = request.session.get('new_user_username')
        initial_data = {'username': username} if username else {}
        
        # Pre-populate form with existing customer data if updating profile
        if request.session.get('updating_profile') and logged_in_username:
            try:
                customer = Customer.objects.get(username=logged_in_username)
                initial_data.update({
                    'age': customer.age,
                    'gender': customer.gender,
                    'employment_status': customer.employment_status,
                    'occupation': customer.occupation,
                    'education': customer.education,
                    'household_size': customer.household_size,
                    'number_of_children': customer.number_of_children,
                    'monthly_income_sgd': customer.monthly_income_sgd,
                })
            except Customer.DoesNotExist:
                pass
        
        form = self.customer_details_form_class(initial=initial_data)
        context = {
            "form": form,
            "is_profile_update": request.session.get('updating_profile', False)
        }
        return self.render_with_base(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        is_updating_profile = request.session.get('updating_profile', False)
        if is_updating_profile:
            username = request.session.get('customer_username')
        else:
            username = request.session.get('new_user_username')
            password = request.session.get('new_user_password')
        if not username:
            return self.render_with_base(request, 'customer_website/signup.html', {
                "form": CustomerSignupForm(),
                "error_message": ["Session expired. Please sign up / log in again."]
            })
            
        if request.POST.get('action') == 'skip':
            if is_updating_profile:
                try:
                    customer = Customer.objects.get(username=username)
                    customer.preferred_category = 'none'
                    customer.save()
                    request.session['preferred_category'] = 'none'
                except Customer.DoesNotExist:
                    pass
            else:
                customer = Customer(
                    username=username,
                    password=password,
                    preferred_category='none'
                )
                customer.save()
                Coupon.objects.create(
                    code=make_coupon_code('WELCOME10', customer=customer),
                    discount_percentage=10,
                    description='Welcome bonus! 10% discount (Up till S$50) for updating customer information. Max 1 time use, min spend S$50',
                    valid_from=timezone.localdate(),
                    valid_until=timezone.localdate() + timedelta(days=365),  # Valid for 1 year
                    usage_limit=1,
                    minimum_order_value=Decimal('50.00'),
                    maximum_discount=Decimal('50.00'),
                    is_active=True
                ).assigned_customers.add(customer)
                
                
                request.session['customer_hasLogin'] = True
                request.session['customer_username'] = username
                request.session['customer_profile_picture'] = customer.profile_picture
            
            request.session.pop('new_user', None)
            request.session.pop('new_user_username', None)
            request.session.pop('new_user_password', None)
            request.session.pop('updating_profile', None)
            
            return redirect('customer_home')
            
        form = self.customer_details_form_class(request.POST)
        
        if is_updating_profile:
            try:
                customer = Customer.objects.get(username=username)
                form = self.customer_details_form_class(request.POST, instance=customer)
            except Customer.DoesNotExist:
                pass
        
        if form.is_valid():
            print("Form is valid")
            customer_data = form.cleaned_data  
            customer_preferred = {
                'age': customer_data.get('age'),
                'gender': customer_data.get('gender'),
                'employment_status': customer_data.get('employment_status'),
                'occupation': customer_data.get('occupation'),
                'education': customer_data.get('education'),
                'household_size': customer_data.get('household_size'),
                'number_of_children': customer_data.get('number_of_children'),
                'monthly_income_sgd': customer_data.get('monthly_income_sgd'),
            }
            preferred_category = predict_preferred_category(customer_preferred)

            if is_updating_profile:
                try:
                    customer = Customer.objects.get(username=username)
                    customer.age = customer_data.get('age')
                    customer.gender = customer_data.get('gender')
                    customer.employment_status = customer_data.get('employment_status')
                    customer.occupation = customer_data.get('occupation')
                    customer.education = customer_data.get('education')
                    customer.household_size = customer_data.get('household_size')
                    customer.number_of_children = customer_data.get('number_of_children')
                    customer.monthly_income_sgd = customer_data.get('monthly_income_sgd')
                    customer.preferred_category = preferred_category[0] if preferred_category else 'General'
                    customer.save()

                    Coupon.objects.create(
                    code=make_coupon_code('DETAILS40', customer=customer),
                    discount_percentage=40,
                    description='40% discount (Up till S$50) for updating customer information. Max 1 time use, min spend S$50',
                    valid_from=timezone.localdate(),
                    valid_until=timezone.localdate() + timedelta(days=365),  # Valid for 1 year
                    usage_limit=1,
                    minimum_order_value=Decimal('50.00'),
                    maximum_discount=Decimal('50.00'),
                    is_active=True
                    ).assigned_customers.add(customer)

                    request.session['preferred_category'] = customer.preferred_category
                    
                except Customer.DoesNotExist:
                    customer = Customer(
                        username=username,
                        password=password,
                        age=customer_data.get('age'),
                        gender=customer_data.get('gender'),
                        employment_status=customer_data.get('employment_status'),
                        occupation=customer_data.get('occupation'),
                        education=customer_data.get('education'),
                        household_size=customer_data.get('household_size'),
                        number_of_children=customer_data.get('number_of_children'),
                        monthly_income_sgd=customer_data.get('monthly_income_sgd'),
                        preferred_category=preferred_category[0] if preferred_category else 'General'
                    )
                    customer.save()
            else:
                # Create new customer
                customer = Customer(
                    username=username,
                    password=password,
                    age=customer_data.get('age'),
                    gender=customer_data.get('gender'),
                    employment_status=customer_data.get('employment_status'),
                    occupation=customer_data.get('occupation'),
                    education=customer_data.get('education'),
                    household_size=customer_data.get('household_size'),
                    number_of_children=customer_data.get('number_of_children'),
                    monthly_income_sgd=customer_data.get('monthly_income_sgd'),
                    preferred_category=preferred_category[0] if preferred_category else 'General'
                )
                
                customer.save()
    
                Coupon.objects.create(
                    code=make_coupon_code('WELCOME10', customer=customer),
                    discount_percentage=10,
                    description='Welcome bonus! 10% discount (Up till S$50) for updating customer information. Max 1 time use, min spend S$50',
                    valid_from=timezone.localdate(),
                    valid_until=timezone.localdate() + timedelta(days=365),  # Valid for 1 year
                    usage_limit=1,
                    minimum_order_value=Decimal('50.00'),
                    maximum_discount=Decimal('50.00'),
                    is_active=True
                ).assigned_customers.add(customer)
                
                request.session['customer_hasLogin'] = True
                request.session['customer_username'] = username
                request.session['customer_profile_picture'] = customer.profile_picture
            
            # Clean up sessions
            request.session.pop('new_user', None)
            request.session.pop('new_user_username', None)
            request.session.pop('new_user_password', None)
            request.session.pop('updating_profile', None)
            request.session.pop('udating_profile', None)
            
            return redirect('customer_home')
        else:
            return self.render_with_base(request, self.template_name, {
                "form": form, 
                "error_message": error_check(form.errors.values())
            })       
        
class mainpageview(BaseView):
    template_name = 'customer_website/main_page.html'

    def get(self, request, *args, **kwargs):
        user = Customer.objects.get(username=request.session.get('customer_username'))
        pref = getattr(user, 'preferred_category', None)
        request.session['preferred_category'] = pref

        if pref and isinstance(pref, str) and pref.lower() != 'none':
            # main_category: the single preferred category
            main_category = Category.objects.filter(name=pref)
            # more_categories: up to 11 other top-level categories
            more_categories = Category.objects.filter(parent_category__isnull=True).exclude(name=pref)[:11]
            products = Product.objects.filter(category__in=main_category).distinct()[:12]
            recommendation_reason = f"you selected '{pref}' as your interest during onboarding"
        else:
            # No preferred category: present 12 categories total in the
            # `more_categories` slot so the template shows them all.
            main_category = Category.objects.none()
            more_categories = Category.objects.filter(parent_category__isnull=True)[:12]
            products = Product.objects.filter(category__in=more_categories).distinct()[:12]
            recommendation_reason = 'Explore popular categories and products'

        top_products = Product.objects.order_by('-reorder_quantity')[:10]
        currency_context = get_currency_context(request)
        convert_product_prices(products, currency_context['currency_info'])
        convert_product_prices(top_products, currency_context['currency_info'])

        context = {
            'main_category': main_category,
            'more_categories': more_categories,
            'products': products,
            'top_products': top_products,
            'preferred_category': user.preferred_category,
            'recommendation_reason': recommendation_reason,
        }
        context.update(currency_context)
        return self.render_with_base(request, self.template_name, context)
    
class product_detailview(BaseView):
    template_name = 'customer_website/product_detail.html'

    def get(self, request, sku, *args, **kwargs):
        try:     
            product = Product.objects.get(sku=sku)
            currency_context = get_currency_context(request)
            
            if request.GET.get('added') == 'true':
                quantity = int(request.GET.get('quantity', 1))
                currency_context = get_currency_context(request)
                
                if 'cart' not in request.session:
                    request.session['cart'] = {}
                
                cart = request.session['cart']
                if sku in cart:
                    cart[sku]['quantity'] += quantity
                else:
                    cart[sku] = {
                        'product_name': product.product_name,
                        'unit_price': float(product.unit_price),
                        'quantity': quantity,
                        'product_image': product.product_image if product.product_image else None
                    }
                
                request.session['cart'] = cart
                request.session.modified = True
                
                redirect_url = f"{request.path}?cart_added=true"
                currency = request.GET.get('currency') or request.session.get('selected_currency')
                if currency:
                    redirect_url += f"&currency={currency}"
                
                return redirect(redirect_url)
            
            recommended_products_sku = get_recommendations([sku], top_n=4)
            recommended_products = Product.objects.filter(sku__in=recommended_products_sku)
            if recommended_products_sku == []:
                preferred_category = request.session.get('preferred_category', None)
                if preferred_category and preferred_category != 'none':
                    recommended_products = Product.objects.filter(
                        category__name=preferred_category
                    ).exclude(sku=sku)[:4]
                    recommended_title = 'Here are some popular products in your preferred category'
                else:
                    recommended_products = Product.objects.order_by('-reorder_quantity').exclude(sku=sku)[:4]
                    recommended_title = 'Here are some popular products'
            else:
                recommended_title = 'Frequently Bought Together'


            convert_product_prices([product] + list(recommended_products), currency_context['currency_info'])
            
            cart = request.session.get('cart', {})
            is_in_cart = sku in cart
            
            cart_added = request.GET.get('cart_added') == 'true' or is_in_cart
            other_products = Product.objects.none()
            try:
                if product.category:
                    other_products = product.category.products.exclude(sku=sku).order_by('?')[:4]
            except Exception:
                other_products = Product.objects.none()

            context = {
                'product': product,
                'recommended_products': recommended_products,
                'other_products': other_products,
                'cart_added': cart_added,
                'recommended_title': recommended_title if 'recommended_title' in locals() else False,
            }
            context.update(currency_context)
            
            return self.render_with_base(request, self.template_name, context)
        except Product.DoesNotExist:
            currency_context = get_currency_context(request)
            context = {
                'product': None,  
                'recommended_products': [],
            }
            context.update(currency_context)
            
            return self.render_with_base(request, self.template_name, context)
    

class cartview(BaseView):   
    template_name = 'customer_website/cart.html'

    def get(self, request, *args, **kwargs):
        if request.GET.get('clear') == 'true':
            request.session['cart'] = {}
            request.session.modified = True
            return redirect('cart')
            
        if request.GET.get('remove_sku'):
            sku_to_remove = request.GET.get('remove_sku')
            cart = request.session.get('cart', {})
            if sku_to_remove in cart:
                del cart[sku_to_remove]
                request.session['cart'] = cart
                request.session.modified = True
            return redirect('cart')
        
        if request.GET.get('update_sku') and request.GET.get('action'):
            sku_to_update = request.GET.get('update_sku')
            action = request.GET.get('action')
            cart = request.session.get('cart', {})
            
            if sku_to_update in cart:
                if action == 'increase':
                    cart[sku_to_update]['quantity'] += 1
                elif action == 'decrease':
                    cart[sku_to_update]['quantity'] -= 1
                    if cart[sku_to_update]['quantity'] <= 0:
                        del cart[sku_to_update]
                
                request.session['cart'] = cart
                request.session.modified = True
            return redirect('cart')
        
        cart = request.session.get('cart', {})
        bulk_update_made = False
        
        for param_name, new_quantity in request.GET.items():
            if param_name.startswith('qty_'):
                sku = param_name[4:]  
                if sku in cart:
                    try:
                        new_qty = int(new_quantity)
                        if new_qty > 0:
                            cart[sku]['quantity'] = new_qty
                            bulk_update_made = True
                        elif new_qty == 0:
                            del cart[sku]
                            bulk_update_made = True
                    except ValueError:
                        pass  
        
        if bulk_update_made:
            request.session['cart'] = cart
            request.session.modified = True
            return redirect('cart')
        
        cart_items = []
        subtotal = 0
        
        currency_context = get_currency_context(request)

        for sku, item_data in cart.items():
            converted_unit_price = convert_cart_prices(item_data['unit_price'], currency_context['currency_info'])
            item_total = converted_unit_price * item_data['quantity']
            cart_items.append({
                'sku': sku,
                'product_name': item_data['product_name'],
                'unit_price': converted_unit_price,
                'quantity': item_data['quantity'],
                'total': item_total,
                'product_image': item_data.get('product_image')
            })
            subtotal += item_total
        
        shipping_base = 5.00 if subtotal > 0 else 0
        shipping = convert_cart_prices(shipping_base, currency_context['currency_info']) if shipping_base > 0 else 0
        total = subtotal + shipping

        item_list_sku = list(cart.keys())
        recommended_products_sku = get_recommendations(item_list_sku, metric='lift', top_n=5)
        recommended_products = Product.objects.filter(sku__in=recommended_products_sku)
        is_recommended = recommended_products.exists()
        if not is_recommended:
            preferred_category = request.session.get('preferred_category', None)
            recommended_products = Product.objects.filter(
                category__name=preferred_category
            ).exclude(sku__in=item_list_sku)[:4]

        recommended_products = convert_product_prices(recommended_products, currency_context['currency_info'])
        
        context = {
            'cart_items': cart_items,
            'subtotal': subtotal,
            'shipping': shipping,
            'total': total,
            'recommended_products': recommended_products,
            'is_recommended': is_recommended,
        }
        context.update(currency_context)
        
        return self.render_with_base(request, self.template_name, context)

class all_productsview(BaseView):
    template_name = 'customer_website/products.html'

    def get(self, request, *args, **kwargs):
        search_query = request.GET.get('search', '').strip()
        sort_by = request.GET.get('sort', 'name-asc')
        category_id = request.GET.get('category', '').strip()
        title_name = "All Products"
        
        products_list = Product.objects.all()
        
        if category_id and category_id != 'all':
            try:
                category = Category.objects.get(category_id=category_id)
                if category.subcategories.exists():
                    title_name = category.name
                    subcategory_ids = [subcat.category_id for subcat in category.subcategories.all()]
                    subcategory_ids.append(category_id) 
                    products_list = products_list.filter(category__in=subcategory_ids)
                else:
                    title_name = category.name
                    products_list = products_list.filter(category=category_id)
            except Category.DoesNotExist:
                pass
        
        if search_query:
            products_list = products_list.filter(product_name__icontains=search_query)
        
        if sort_by == 'name-asc':
            products_list = products_list.order_by('product_name')
        elif sort_by == 'name-desc':
            products_list = products_list.order_by('-product_name')
        elif sort_by == 'price-asc':
            products_list = products_list.order_by('unit_price')
        elif sort_by == 'price-desc':
            products_list = products_list.order_by('-unit_price')
        elif sort_by == 'rating-desc':
            products_list = products_list.order_by('-product_rating')
        elif sort_by == 'rating-asc':
            products_list = products_list.order_by('product_rating')
        
        main_categories = Category.objects.filter(parent_category__isnull=True).order_by('name')
        all_categories = Category.objects.all().order_by('name')
        
        paginator = Paginator(products_list, 20)
        page_number = request.GET.get('page', 1)
        
        try:
            products = paginator.page(page_number)
        except:
            products = paginator.page(1)
        
        currency_context = get_currency_context(request)
        convert_product_prices(products, currency_context['currency_info'])
        
        if category_id and category_id != 'all':
            try:
                category = Category.objects.get(category_id=category_id)
                browsing_history = request.session.get('browsing_history', [])
                if category.name not in browsing_history:
                    browsing_history.append(category.name)
                    request.session['browsing_history'] = browsing_history[-5:]
                    request.session.modified = True
            except Category.DoesNotExist:
                pass
        
        current_category_name = title_name if title_name != "All Products" else None
        next_best_actions = get_next_best_action(request, current_category_name)

        context = {
            'all_products': products_list,
            'products': products,
            'paginator': paginator,
            'page_obj': products,
            'is_paginated': paginator.num_pages > 1,
            'search_query': search_query,
            'sort_by': sort_by,
            'selected_category': category_id,
            'main_categories': main_categories,
            'all_categories': all_categories,
            'total_products': products_list.count(),
            'title_name': title_name,
            'next_best_actions': next_best_actions,
        }
        context.update(currency_context)

        return self.render_with_base(request, self.template_name, context)

class search_ajax_view(BaseView):
    def get(self, request, *args, **kwargs):
        search_query = request.GET.get('q', '').strip()
        products_list = Product.objects.none()
        
        if search_query and len(search_query) >= 1: 
            products_list = Product.objects.filter(product_name__icontains=search_query)
        
        currency_context = get_currency_context(request)
        convert_product_prices(products_list, currency_context['currency_info'])
        
        results = []
        for product in products_list:
            results.append({
                'sku': product.sku,
                'name': product.product_name,
                'description': product.description[:100] + '...' if len(product.description) > 100 else product.description,
                'price': str(product.unit_price),
                'currency_symbol': currency_context['currency_symbol'],
                'image_url': product.product_image if product.product_image else None,
                'category': product.category.name if product.category else None,
                'product_url': f"/product/{product.sku}/"
            })
        
        return JsonResponse({
            'results': results,
            'query': search_query,
            'total_count': len(results)
        })
    
class checkout_page(BaseView):
    template_name = 'customer_website/checkout.html'

    def get(self, request, *args, **kwargs):
        cart = request.session.get('cart', {})
        if not cart:
            return self.render_with_base(request, self.template_name, {
                'cart_items': [],
                'subtotal': Decimal('0.00'),
                'shipping_cost': Decimal('0.00'),
                'tax_amount': Decimal('0.00'),
                'total_amount': Decimal('0.00'),
                'checkout_form': None,
            })

        cart_items, totals = self._calculate_cart_totals(request, cart)
        
        checkout_form = CheckoutForm()
        
        currency_context = get_currency_context(request)
        
        # Get available coupons for this customer
        username = request.session.get('customer_username')
        customer = None
        if username:
            try:
                customer = Customer.objects.get(username=username)
                # Get coupons available to this customer
                general_coupons = Coupon.objects.filter(
                    is_active=True,
                    valid_from__lte=datetime.now(),
                    valid_until__gte=datetime.now(),
                    assigned_customers__isnull=True
                ).exclude(usages__customer=customer)
                
                assigned_coupons = Coupon.objects.filter(
                    is_active=True,
                    valid_from__lte=datetime.now(),
                    valid_until__gte=datetime.now(),
                    assigned_customers=customer
                ).exclude(usages__customer=customer)
                
                merged = (general_coupons | assigned_coupons).distinct().order_by('valid_until')
                currency_rate = currency_context['currency_info']['rate']
                try:
                    subtotal_in_sgd = (totals['subtotal'] / currency_rate).quantize(Decimal('0.01'))
                except Exception:
                    subtotal_in_sgd = None

                filtered = []
                for c in merged:
                    try:
                        if not c.is_valid():
                            continue
                        if not c.can_be_used_by(customer):
                            continue
                        if subtotal_in_sgd is not None and c.minimum_order_value and c.minimum_order_value > 0:
                            # only include if cart subtotal (SGD) meets coupon minimum
                            if subtotal_in_sgd < c.minimum_order_value:
                                continue
                        # If coupon restricts applicable categories, ensure cart has at least one eligible item
                        try:
                            if c.applicable_categories.exists():
                                eligible_cat_ids = set(c.applicable_categories.values_list('pk', flat=True))
                                has_eligible = False
                                for it in cart_items:
                                    try:
                                        prod = Product.objects.get(sku=it['sku'])
                                    except Product.DoesNotExist:
                                        continue
                                    if prod and prod.category and prod.category.pk in eligible_cat_ids:
                                        has_eligible = True
                                        break
                                if not has_eligible:
                                    continue
                        except Exception:

                            continue

                        filtered.append(c)
                    except Exception:
                        # If any coupon method raises, skip that coupon
                        continue

                available_coupons = filtered
            except Customer.DoesNotExist:
                available_coupons = Coupon.objects.none()
        else:
            available_coupons = Coupon.objects.none()

        # Handle coupon code from URL parameter
        discount_amount = Decimal('0.00')
        selected_coupon_code = request.GET.get('coupon_code', '').strip()
        coupon_error = None
        final_total = totals['total']
        
        if selected_coupon_code and customer:
            try:
                coupon = Coupon.objects.get(code=selected_coupon_code.upper())
                
                if not coupon.is_valid():
                    coupon_error = 'The coupon is not valid.'
                elif not coupon.can_be_used_by(customer):
                    coupon_error = 'You are not eligible to use this coupon.'
                elif CouponUsage.objects.filter(coupon=coupon, customer=customer).exists():
                    coupon_error = 'You have already used this coupon.'
                else:
                    # Determine eligible subtotal in SGD based on coupon applicable categories
                    subtotal_in_sgd = (totals['subtotal'] / currency_context['currency_info']['rate']).quantize(Decimal('0.01'))
                    eligible_subtotal_sgd = subtotal_in_sgd
                    try:
                        if coupon.applicable_categories.exists():
                            eligible_cat_ids = set(coupon.applicable_categories.values_list('pk', flat=True))
                            eligible_sum = Decimal('0.00')
                            for it in cart_items:
                                try:
                                    prod = Product.objects.get(sku=it['sku'])
                                except Product.DoesNotExist:
                                    continue
                                if prod and prod.category and prod.category.pk in eligible_cat_ids:
                                    # item['unit_price'] is in selected currency; convert to SGD
                                    item_unit_sgd = (it['unit_price'] / currency_context['currency_info']['rate']).quantize(Decimal('0.01'))
                                    eligible_sum += item_unit_sgd * it.get('quantity', 1)
                            eligible_subtotal_sgd = eligible_sum
                    except Exception:
                        # If something fails, fall back to full subtotal
                        eligible_subtotal_sgd = subtotal_in_sgd

                    # If no eligible items, coupon does not apply
                    if eligible_subtotal_sgd <= 0:
                        coupon_error = 'The coupon does not apply to items in your cart.'
                    else:
                        discount_amount = coupon.calculate_discount(eligible_subtotal_sgd)
                        if discount_amount <= 0:
                            coupon_error = 'The coupon does not apply to this order.'
                        else:
                            # convert discount back to display currency
                            discount_amount = discount_amount * currency_context['currency_info']['rate']
                            final_total = totals['total'] - discount_amount
                        
            except Coupon.DoesNotExist:
                coupon_error = 'Invalid coupon code.'
        
        if selected_coupon_code:
            checkout_form.initial['coupon_code'] = selected_coupon_code
            # persist selected coupon so it survives a full-page reload and form submit
            request.session['selected_coupon_code'] = selected_coupon_code

        context = {
            'cart_items': cart_items,
            'subtotal': totals['subtotal'],
            'shipping_cost': totals['shipping'],
            'tax_amount': totals['tax'],
            'total_amount': final_total,
            'discount_amount': discount_amount,
            'checkout_form': checkout_form,
            'available_coupons': available_coupons,
            'selected_coupon_code': selected_coupon_code,
            'coupon_error': coupon_error,
        }
        context.update(currency_context)
        
        return self.render_with_base(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        cart = request.session.get('cart', {})
        cart_items, totals = self._calculate_cart_totals(request, cart)
        
        checkout_form = CheckoutForm(request.POST)
        
        currency_context = get_currency_context(request)

        if checkout_form.is_valid():
            order_result = self._process_order(request, checkout_form.cleaned_data, cart_items, totals)
            
            if order_result['success']:
                request.session['cart'] = {}
                request.session.modified = True
                return redirect('order_confirmation', order_id=order_result['order_id'])
            else:
                print("Order processing error:", order_result['error'])
                context = {
                    'cart_items': cart_items,
                    'subtotal': totals['subtotal'],
                    'shipping_cost': totals['shipping'],
                    'tax_amount': totals['tax'],
                    'total_amount': totals['total'],
                    'discount_amount': Decimal('0.00'), 
                    'checkout_form': checkout_form,
                    'form_error': order_result['error'],
                }
                context.update(currency_context)
                
                return self.render_with_base(request, self.template_name, context)

        context = {
            'cart_items': cart_items,
            'subtotal': totals['subtotal'],
            'shipping_cost': totals['shipping'],
            'tax_amount': totals['tax'],
            'total_amount': totals['total'],
            'discount_amount': Decimal('0.00'), 
            'checkout_form': checkout_form,
        }
        context.update(currency_context)
        
        return self.render_with_base(request, self.template_name, context)

    def _calculate_cart_totals(self, request, cart):
        """Calculate cart items and totals"""
        cart_items = []
        subtotal = Decimal('0.00')
        
        currency_context = get_currency_context(request)

        for sku, item_data in cart.items():
            converted_unit_price = convert_cart_prices(item_data['unit_price'], currency_context['currency_info'])
            item_total = converted_unit_price * item_data['quantity']
            cart_items.append({
                'sku': sku,
                'product_name': item_data['product_name'],
                'unit_price': converted_unit_price,
                'quantity': item_data['quantity'],
                'total_price': item_total,
                'product_image': item_data.get('product_image')
            })
            subtotal += item_total
  
        shipping_base = Decimal('5.00') if subtotal > 0 else Decimal('0.00')
        shipping = convert_cart_prices(shipping_base, currency_context['currency_info']) if shipping_base > 0 else Decimal('0.00')
        tax_rate = Decimal('0.08')
        tax_amount = subtotal * tax_rate
        
        total = subtotal + shipping + tax_amount

        return cart_items, {
            'subtotal': subtotal,
            'shipping': shipping,
            'tax': tax_amount,
            'total': total
        }

    def _process_order(self, request, form_data, cart_items, totals):
        try:
            username = request.session.get('customer_username')
            customer = Customer.objects.get(username=username)

            currency_context = get_currency_context(request)
            currency_rate = currency_context['currency_info']['rate']
            
            subtotal_in_sgd = (totals['subtotal'] / currency_rate).quantize(Decimal('0.01'))
            total_in_sgd = (totals['total'] / currency_rate).quantize(Decimal('0.01'))

            coupon = None
            discount_amount = Decimal('0.00')
            coupon_code = form_data.get('coupon_code', '').strip()
            if not coupon_code:
                coupon_code = request.session.pop('selected_coupon_code', '').strip()
            
            has_available_coupons = False
            try:
                today = timezone.localdate()
                available_qs = (
                    Coupon.objects.filter(
                        is_active=True,
                        valid_from__lte=today,
                        valid_until__gte=today
                    )
                    .exclude(usages__customer=customer)
                    .filter(Q(assigned_customers__isnull=True) | Q(assigned_customers=customer))
                    .distinct()
                )
                has_available_coupons = available_qs.exists()
            except Exception:
                has_available_coupons = False

            # Only validate/apply coupon if user actually has coupons available.
            if coupon_code and has_available_coupons:
                
                try:
                    coupon = Coupon.objects.get(code=coupon_code.upper())
                    
                    if not coupon.is_valid():
                        return {
                            'success': False,
                            'error': 'The coupon is not valid.'
                        }
                    
                    if not coupon.can_be_used_by(customer):
                        return {
                            'success': False,
                            'error': 'You are not eligible to use this coupon.'
                        }
                    
                    if CouponUsage.objects.filter(coupon=coupon, customer=customer).exists():
                        return {
                            'success': False,
                            'error': 'You have already used this coupon.'
                        }
                    
                    eligible_subtotal_sgd = subtotal_in_sgd
                    try:
                        if coupon.applicable_categories.exists():
                            eligible_cat_ids = set(coupon.applicable_categories.values_list('pk', flat=True))
                            eligible_sum = Decimal('0.00')
                            for it in cart_items:
                                try:
                                    prod = Product.objects.get(sku=it['sku'])
                                except Product.DoesNotExist:
                                    continue
                                if prod and prod.category and prod.category.pk in eligible_cat_ids:
                                    item_unit_sgd = (it['unit_price'] / currency_rate).quantize(Decimal('0.01'))
                                    eligible_sum += item_unit_sgd * it.get('quantity', 1)
                            eligible_subtotal_sgd = eligible_sum
                    except Exception:
                        eligible_subtotal_sgd = subtotal_in_sgd

                    if eligible_subtotal_sgd <= 0:
                        return {
                            'success': False,
                            'error': 'The coupon does not apply to items in the cart.'
                        }

                    discount_amount = coupon.calculate_discount(eligible_subtotal_sgd)
                    if discount_amount <= 0:
                        return {
                            'success': False,
                            'error': 'The coupon does not apply to this order.'
                        }
                    
                except Coupon.DoesNotExist:
                    return {
                        'success': False,
                        'error': 'Invalid coupon code.'
                    }

            order = Order.objects.create(
                customer=customer,
                customer_email=form_data['email'],
                status='PENDING',
                shipping_address=f"{form_data['address']}, {form_data['city']}, {form_data['postal_code']}, {form_data['country']}",
                order_notes=form_data.get('order_notes', ''),
                subtotal_amount=subtotal_in_sgd,
                discount_amount=discount_amount,
                total_amount=total_in_sgd - discount_amount,
                coupon=coupon,
                coupon_code=coupon_code if coupon else None,
                order_date=datetime.now()
            )

            for item in cart_items:
                try:
                    product = Product.objects.get(sku=item['sku'])
                    price_in_sgd = (item['unit_price'] / currency_rate).quantize(Decimal('0.01'))
                    
                    OrderItem.objects.create(
                        order_id=order,
                        product=product,
                        quantity=item['quantity'],
                        price_at_purchase=price_in_sgd
                    )
                    try:
                        qty = int(item.get('quantity', 1) or 0)
                    except Exception:
                        qty = item.get('quantity', 0)
                    if hasattr(product, 'quantity_on_hand') and product.quantity_on_hand is not None:
                        try:
                            product.quantity_on_hand = max(0, int(product.quantity_on_hand) - int(qty))
                            product.save(update_fields=['quantity_on_hand'])
                        except Exception:
                            pass
                except Product.DoesNotExist:
                    return {
                        'success': False,
                        'error': f'Product {item["sku"]} not found.'
                    }
            print(f"coupon: {coupon}")
            if coupon:
                CouponUsage.objects.create(
                    coupon=coupon,
                    customer=customer,
                    order=order,
                    discount_amount=discount_amount
                )

                coupon.usage_count += 1
                coupon.save()
            
            order.save()
            recommended_list = get_recommendations([item['sku'] for item in cart_items], top_n=1)

            pref_cat = None
            cust_pref = getattr(customer, 'preferred_category', None)
            if isinstance(cust_pref, Category):
                pref_cat = cust_pref.name
            elif isinstance(cust_pref, str):
                cleaned = cust_pref.strip()
                if cleaned and cleaned.lower() != 'none':
                    pref_cat = cleaned

            coupon_cat = None
            if recommended_list:
                recommended_sku = recommended_list[0]
                try:
                    recommended_product = Product.objects.get(sku=recommended_sku)
                    if recommended_product.category and recommended_product.category.name:
                        coupon_cat = recommended_product.category.name
                except Product.DoesNotExist:
                    pass

            if not coupon_cat:
                try:
                    cat_qty = {}
                    for it in cart_items:
                        sku = it.get('sku')
                        try:
                            prod = Product.objects.get(sku=sku)
                        except Product.DoesNotExist:
                            continue
                        if prod and prod.category and prod.category.name:
                            name = prod.category.name
                            cat_qty.setdefault(name, 0)
                            cat_qty[name] += int(it.get('quantity', 0) or 0)

                    if cat_qty:
                        coupon_cat = min(cat_qty.items(), key=lambda kv: kv[1])[0]
                except Exception:
                    coupon_cat = None

            if not coupon_cat and pref_cat:
                coupon_cat = pref_cat

            if not coupon_cat:
                coupon_cat = 'General'

            prefix = f'REWARD{coupon_cat[0:3].upper()}'
            code = None
            for _ in range(10):
                suffix = uuid.uuid4().hex[:5].upper()
                candidate = f"{prefix}{suffix}"
                if not Coupon.objects.filter(code=candidate).exists():
                    code = candidate
                    break
            if code is None:
                code = f"{prefix}{int(datetime.now().timestamp()) % 100000:05d}"

            coupon = Coupon.objects.create(
                code=code,
                discount_percentage=5,
                description=f'Thank you for your purchase! Enjoy this reward coupon for {coupon_cat} category. 5% discount (Up till S$20). Max 1 time use, min spend S$30',
                valid_from=timezone.localdate(),
                valid_until=timezone.localdate() + timedelta(days=90), 
                usage_limit=1,
                minimum_order_value=Decimal('30.00'),
                maximum_discount=Decimal('20.00'),
                is_active=True
            )
            coupon.assigned_customers.add(customer)
            
            if coupon_cat != 'General':
                try:
                    category = Category.objects.get(name=coupon_cat)
                    coupon.applicable_categories.add(category)
                except Category.DoesNotExist:
                    pass  # Leave as all categories
            
            coupon.assigned_customers.add(customer)
            
            return {
                'success': True,
                'order_id': order.order_id
            }
                
        except Customer.DoesNotExist:
            return {
                'success': False,
                'error': 'Customer not found. Please log in again.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'An error occurred while processing your order: {str(e)}'
            }

class order_confirmation_page(BaseView):
    template_name = 'customer_website/order_confirmation.html'

    def get(self, request, order_id, *args, **kwargs):
        try:
            order = Order.objects.get(order_id=order_id)
            
            username = request.session.get('customer_username')
            if not username or order.customer.username != username:
                return self.render_with_base(request, 'customer_website/main_page.html')

            order_items = OrderItem.objects.filter(order_id=order)
            currency_context = get_currency_context(request)
            
            order_total = Decimal('0.00')
            for item in order_items:
                item.converted_price = convert_cart_prices(item.price_at_purchase, currency_context['currency_info'])
                item.item_total = item.converted_price * item.quantity
                order_total += item.item_total
            
            order.converted_total = convert_cart_prices(order.total_amount, currency_context['currency_info'])

            context = {
                'order': order,
                'order_items': order_items,
                'order_total': order_total,
                
            }
            context.update(currency_context)
            
            return self.render_with_base(request, self.template_name, context)
            
        except Order.DoesNotExist:
            return self.render_with_base(request, 'customer_website/main_page.html')

class profile_page(BaseView):
    template_name = 'customer_website/profile.html'

    def get_context_data(self, request, sort_by='date-desc', **kwargs):
        username = request.session.get('customer_username')
        customer = Customer.objects.get(username=username)
        customer_orders = Order.objects.filter(customer=customer)
        
        if sort_by == 'date-asc':
            customer_orders = customer_orders.order_by('order_date')
        elif sort_by == 'date-desc':
            customer_orders = customer_orders.order_by('-order_date')
        elif sort_by == 'status-pending':
            customer_orders = customer_orders.order_by('-order_date').filter(status='PENDING')
        elif sort_by == 'status-completed':
            customer_orders = customer_orders.order_by('-order_date').filter(status='COMPLETED')
        elif sort_by == 'status-cancelled':
            customer_orders = customer_orders.order_by('-order_date').filter(status='CANCELLED')
        elif sort_by == 'status-all':
            customer_orders = customer_orders.annotate(
                status_order=Case(
                    When(status='PENDING', then=Value(1)),
                    When(status='COMPLETED', then=Value(2)),
                    When(status='CANCELLED', then=Value(3)),
                    default=Value(4),
                    output_field=IntegerField(),
                )
            ).order_by('status_order', '-order_date')
        else:
            customer_orders = customer_orders.order_by('-order_date')

        currency_context = get_currency_context(request)
        
        for order in customer_orders:
            order_total = Decimal('0.00')
            order_items = list(order.items.all())
            for item in order_items:
                item.converted_price = convert_cart_prices(item.price_at_purchase, currency_context['currency_info'])
                item_total = item.converted_price * item.quantity
                order_total += item_total
                
                # Check if customer has already reviewed this product
                existing_review = Review.objects.filter(
                    product=item.product,
                    customer=customer
                ).first()
                
                if existing_review:
                    item.existing_review = existing_review
                else:
                    item.existing_review = None
                    
            order.converted_total = order_total
            order.processed_items = order_items
        
        review_form = ReviewForm()
        
        today = timezone.localdate()
        all_relevant = (
            Coupon.objects.filter(assigned_customers__isnull=True) |
            Coupon.objects.filter(assigned_customers=customer)
        ).distinct().exclude(usages__customer=customer)

        customer_coupons = all_relevant.filter(
            is_active=True,
            valid_from__lte=today,
            valid_until__gte=today,
        ).order_by('valid_until')

        expired_coupons = all_relevant.exclude(pk__in=customer_coupons.values_list('pk', flat=True)).order_by('-valid_until')

        for coupon in customer_coupons:
            if coupon.usage_limit > 0:
                coupon.uses_left = coupon.usage_limit - coupon.usage_count
            else:
                coupon.uses_left = 'Unlimited'

        for coupon in expired_coupons:
            if coupon.usage_limit > 0:
                coupon.uses_left = max(0, coupon.usage_limit - coupon.usage_count)
            else:
                coupon.uses_left = 'Unlimited'

        used_coupons = CouponUsage.objects.filter(customer=customer).order_by('used_at')
        context = {
            'customer': customer,
            'customer_orders': customer_orders,
            'current_sort': sort_by,
            'review_form': review_form,
            'customer_coupons': customer_coupons,
            'used_coupons': used_coupons,
            'expired_coupons': expired_coupons,
        }
        context.update(currency_context)
        context.update(kwargs) 
        return context

    def get(self, request, *args, **kwargs):
        sort_by = request.GET.get('sort', 'date-desc')

        if request.GET.get('logout') == 'true':
            request.session.pop('customer_hasLogin', None)
            request.session.pop('customer_username', None)
            request.session.pop('customer_profile_picture', None)
            request.session.pop('preferred_category', None)
            request.session.pop('browsing_history', None)
            request.session.pop('cart', None)
            request.session.pop('selected_currency', None)
            return redirect('login')
        
        context = self.get_context_data(request, sort_by)
        return self.render_with_base(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        username = request.session.get('customer_username')
        if not username:
            return self.render_with_base(request, 'customer_website/login.html', {
                "form": CustomerLoginForm(),
                "error_message": ["Please log in to submit a review."]
            })
        
        try:
            customer = Customer.objects.get(username=username)

            product_sku = request.POST.get('product_sku')
            if not product_sku:
                context = self.get_context_data(request, message=["Invalid product for review submission."])
                return self.render_with_base(request, self.template_name, context)
            
            product = Product.objects.get(sku=product_sku)
            
            has_purchased = OrderItem.objects.filter(
                order_id__customer=customer,
                order_id__status='COMPLETED',
                product=product
            ).exists()
            
            if not has_purchased:
                context = self.get_context_data(request, message=["You can only review products you have purchased."])
                return self.render_with_base(request, self.template_name, context)
            
            form = ReviewForm(request.POST)
            
            if form.is_valid():
                review = form.save(commit=False)
                review.product = product
                review.customer = customer
                
                existing_review = Review.objects.filter(
                    product=product,
                    customer=customer
                ).first()
                
                if existing_review:
                    existing_review.review_title = review.review_title
                    existing_review.review_content = review.review_content
                    existing_review.rating = review.rating
                    existing_review.save()
                else:
                    review.save()
                
                context = self.get_context_data(request, message="Your review has been submitted successfully.")
                return self.render_with_base(request, self.template_name, context)
            else:
                context = self.get_context_data(request, error_message=error_check(form.errors.values()))
                return self.render_with_base(request, self.template_name, context)
                
        except Customer.DoesNotExist:
            return self.render_with_base(request, 'customer_website/login.html', {
                "form": CustomerLoginForm(),
                "error_message": ["Please log in to submit a review."]
            })
        except Product.DoesNotExist:
            context = self.get_context_data(request, error_message=["Invalid product for review submission."])
            return self.render_with_base(request, self.template_name, context)
        except Exception as e:
            context = self.get_context_data(request, error_message=["An unexpected error occurred. Please try again later."])
            return self.render_with_base(request, self.template_name, context)


class about_us_view(BaseView):
    template_name = 'customer_website/about.html'

    def get(self, request, *args, **kwargs):
        return self.render_with_base(request, self.template_name, {})

class ForgotPasswordView(BaseView):
    template_name = 'customer_website/forgot_password.html'

    def get(self, request):
        form = ForgotPasswordForm()
        return self.render_with_base(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = ForgotPasswordForm(request.POST)
        
        username = request.POST.get('username')
        email = request.POST.get('email')
        
        if username and not email:
            temp_form = ForgotPasswordForm({'username': username})
            if temp_form.is_valid():
                form = ForgotPasswordForm({'username': username})
                return self.render_with_base(request, self.template_name, {
                    'form': form, 
                    'show_email': True,
                    'username': username
                })
            else:
                return self.render_with_base(request, self.template_name, {
                    'form': temp_form, 
                    'error_message': error_check(temp_form.errors.values())
                })
        
        if form.is_valid():
            username = form.cleaned_data['username']
            print("USERNAME:", username)
            email = form.cleaned_data['email']
            
            reset_url = request.build_absolute_uri(
                reverse('reset_password', kwargs={'username': username})
            )
            
            subject = 'AuroraMart Password Reset'
            message = f'''Hello {username},

You have requested to reset your password for your AuroraMart account.

Please click the link below to reset your password:
{reset_url}

If you did not request this password reset, please ignore this email.

Thank you,
AuroraMart Team'''
            
            try:
                request.session[f'password_reset_{username}'] = True
                request.session.set_expiry(3600) 
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'auroramart456@gmail.com'),
                    recipient_list=[email],
                    fail_silently=True, 
                )
                
                return self.render_with_base(request, self.template_name, {
                    'form': form,
                    'success_message': f'Password reset link has been sent to {email}'
                })
            
            except Exception as e:
                return self.render_with_base(request, self.template_name, {
                    'form': form, 
                    'error_message': [f'Error sending email: {str(e)}']
                })        
        
        return self.render_with_base(request, self.template_name, {
            'form': form, 
            'error_message': error_check(form.errors.values())
        })


class ResetPasswordView(BaseView):
    template_name = 'customer_website/reset_password.html'
    
    def get(self, request, username):
        if not request.session.get(f'password_reset_{username}'):
            return redirect('login')
        
        try:
            customer = Customer.objects.get(username=username)
            form = ResetPasswordForm()
            return self.render_with_base(request, self.template_name, {'form': form, 'username': username})
        except Customer.DoesNotExist:
            return redirect('login')
    
    def post(self, request, username):
        if not request.session.get(f'password_reset_{username}'):
            return redirect('login')        
        
        try:
            customer = Customer.objects.get(username=username)
            form = ResetPasswordForm(request.POST)
            
            if form.is_valid():
                new_password = form.cleaned_data['password']
                customer.password = new_password
                customer.save()
                
                request.session.pop(f'password_reset_{username}', None)
                
                return self.render_with_base(request, self.template_name, {
                    'form': form,
                    'username': username,
                    'success': True,
                    'success_message': 'Password has been reset successfully! Redirecting to login...'
                })
            
            return self.render_with_base(request, self.template_name, {
                'form': form, 
                'username': username,
                'error_message': error_check(form.errors.values())
            })
        except Customer.DoesNotExist:
            return redirect('login')
