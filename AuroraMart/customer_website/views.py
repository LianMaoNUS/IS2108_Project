from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
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

model_path = os.path.join(os.path.dirname(__file__), 'prediction_data', 'b2c_customers_100.joblib')
def predict_preferred_category(customer_data):
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

loaded_rules = joblib.load(os.path.join(os.path.dirname(__file__), 'prediction_data', 'b2c_products_500_transactions_50k.joblib'))
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
        request.session['preferred_category'] = user.preferred_category
        more_categories = Category.objects.exclude(name=user.preferred_category)[:5]
        products = Product.objects.filter(category__in=main_category).distinct()[:12]
        top_products = Product.objects.order_by('-reorder_quantity')[:10]
        currency_context = get_currency_context(request)
        convert_product_prices(products, currency_context['currency_info'])
        convert_product_prices(top_products, currency_context['currency_info'])

        context = {
            'username': request.session.get('username'),
            'profile_picture': request.session.get('profile_picture'),
            'main_category': main_category,
            'more_categories': more_categories,
            'products': products,
            'top_products': top_products,
            'cart_count': get_cart_count(request),
        }
        context.update(currency_context)

        return render(request, self.template_name, context)
    
class product_detailview(View):
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
                
                # Add or update item in cart
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
            
            if not recommended_products.exists():
                preferred_category = request.session.get('preferred_category', None)
                recommended_products = Product.objects.filter(
                    category__name=preferred_category
                ).exclude(sku=sku)[:4]

            convert_product_prices([product] + list(recommended_products), currency_context['currency_info'])
            
            cart = request.session.get('cart', {})
            is_in_cart = sku in cart
            
            cart_added = request.GET.get('cart_added') == 'true' or is_in_cart
         
            context = {
                'product': product,
                'recommended_products': recommended_products,
                'username': request.session.get('username'),
                'profile_picture': request.session.get('profile_picture'),
                'cart_count': get_cart_count(request),
                'cart_added': cart_added,
                
            }
            context.update(currency_context)
            
            return render(request, self.template_name, context)
        except Product.DoesNotExist:
            currency_context = get_currency_context(request)
            context = {
                'product': None,  
                'recommended_products': [],
                'username': request.session.get('username'),
                'profile_picture': request.session.get('profile_picture'),
                'cart_count': get_cart_count(request),
            }
            context.update(currency_context)
            
            return render(request, self.template_name, context)

class cartview(View):   
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
        recommended_products_sku = get_recommendations(item_list_sku, top_n=4)
        recommended_products = Product.objects.filter(sku__in=recommended_products_sku)
            
        if not recommended_products.exists():
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
            'cart_count': get_cart_count(request),
            'username': request.session.get('username'),
            'profile_picture': request.session.get('profile_picture'),
            'recommended_products': recommended_products,
        }
        context.update(currency_context)
        
        return render(request, self.template_name, context)
    
class all_productsview(View):
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
                # Check if it's a parent category
                if category.subcategories.exists():
                    title_name = category.name
                    subcategory_ids = [subcat.category_id for subcat in category.subcategories.all()]
                    subcategory_ids.append(category_id)  # Include the parent category itself
                    products_list = products_list.filter(category__in=subcategory_ids)
                else:
                    title_name = category.name
                    products_list = products_list.filter(category=category_id)
            except Category.DoesNotExist:
                pass
        
        # Apply search filter if search query exists
        if search_query:
            products_list = products_list.filter(product_name__icontains=search_query)
        
        # Apply sorting
        if sort_by == 'name-asc':
            products_list = products_list.order_by('product_name')
        elif sort_by == 'name-desc':
            products_list = products_list.order_by('-product_name')
        elif sort_by == 'price-asc':
            products_list = products_list.order_by('unit_price')
        elif sort_by == 'price-desc':
            products_list = products_list.order_by('-unit_price')
        
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

        context = {
            'all_products': products_list,
            'products': products,
            'paginator': paginator,
            'page_obj': products,
            'is_paginated': paginator.num_pages > 1,
            'username': request.session.get('username'),
            'profile_picture': request.session.get('profile_picture'),
            'cart_count': get_cart_count(request),
            'search_query': search_query,
            'sort_by': sort_by,
            'selected_category': category_id,
            'main_categories': main_categories,
            'all_categories': all_categories,
            'total_products': products_list.count(),
            'title_name': title_name,
        }
        context.update(currency_context)

        return render(request, self.template_name, context)

class search_ajax_view(View):
    def get(self, request, *args, **kwargs):
        search_query = request.GET.get('q', '').strip()
        products_list = Product.objects.none()
        
        if search_query and len(search_query) >= 2:  # Only search if query is at least 2 characters
            products_list = Product.objects.filter(product_name__icontains=search_query)  # Show all results
        
        currency_context = get_currency_context(request)
        convert_product_prices(products_list, currency_context['currency_info'])
        
        # Return JSON response
        from django.http import JsonResponse
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

def about_page(request):
    """About us page"""
    return render(request, 'customer_website/about.html')
