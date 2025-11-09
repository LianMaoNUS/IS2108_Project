from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Customer
from admin_panel.models import Product, Category ,Order, OrderItem
from django.views import View
from .forms import CustomerLoginForm, CustomerSignupForm, CustomerForm, CheckoutForm
from django.contrib.auth.hashers import check_password
import pandas as pd
import joblib
import os
from decimal import Decimal
from django.http import JsonResponse
import uuid
from datetime import datetime
from django.db.models import Case, When, Value, IntegerField

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


def get_next_best_action(request, current_category=None):
    """
    Determine next best action to nudge user exploration based on:
    - Browsing history (session-based)
    - Cart contents
    - Preferred category
    - Popular categories
    """
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
        
        # Get all main categories
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
            # Get recommended products based on cart items
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
            unexplored_cat = unexplored.order_by('?').first()  # Random unexplored category
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
        from django.db.models import Sum, Count
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
                    request.session['customer_hasLogin'] = True
                    request.session['customer_username'] = username
                    request.session['customer_profile_picture'] = customer.profile_picture
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
            request.session['customer_hasLogin'] = True
            request.session['customer_username'] = username
            request.session['customer_profile_picture'] = customer.profile_picture
            
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
            request.session.pop('customer_hasLogin', None)
            request.session.pop('customer_username', None)
            request.session.pop('customer_profile_picture', None)
            request.session.pop('preferred_category', None)
            request.session.pop('browsing_history', None)
            request.session.pop('cart', None)
            request.session.pop('selected_currency', None)
            return redirect('login')
            
        user = Customer.objects.get(username=request.session.get('customer_username'))
        main_category = Category.objects.filter(name=user.preferred_category)
        request.session['preferred_category'] = user.preferred_category
        more_categories = Category.objects.filter(parent_category__isnull=True).exclude(name=user.preferred_category)[:5]
        products = Product.objects.filter(category__in=main_category).distinct()[:12]
        top_products = Product.objects.order_by('-reorder_quantity')[:10]
        currency_context = get_currency_context(request)
        convert_product_prices(products, currency_context['currency_info'])
        convert_product_prices(top_products, currency_context['currency_info'])

        context = {
            'username': request.session.get('customer_username'),
            'profile_picture': request.session.get('customer_profile_picture'),
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
                'username': request.session.get('customer_username'),
                'profile_picture': request.session.get('customer_profile_picture'),
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
                'username': request.session.get('customer_username'),
                'profile_picture': request.session.get('customer_profile_picture'),
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
        print(item_list_sku)
        recommended_products_sku = get_recommendations(item_list_sku, metric='lift', top_n=5)
        recommended_products = Product.objects.filter(sku__in=recommended_products_sku)
        print(recommended_products_sku)
            
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
            'username': request.session.get('customer_username'),
            'profile_picture': request.session.get('customer_profile_picture'),
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
            'username': request.session.get('customer_username'),
            'profile_picture': request.session.get('customer_profile_picture'),
            'cart_count': get_cart_count(request),
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

        return render(request, self.template_name, context)

class search_ajax_view(View):
    def get(self, request, *args, **kwargs):
        search_query = request.GET.get('q', '').strip()
        products_list = Product.objects.none()
        
        if search_query and len(search_query) >= 1: 
            products_list = Product.objects.filter(product_name__icontains=search_query)  # Show all results
        
        currency_context = get_currency_context(request)
        convert_product_prices(products_list, currency_context['currency_info'])
        
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
    
class checkout_page(View):
    template_name = 'customer_website/checkout.html'

    def get(self, request, *args, **kwargs):
        cart = request.session.get('cart', {})
        if not cart:
            return render(request, self.template_name, {
                'cart_items': [],
                'subtotal': Decimal('0.00'),
                'shipping_cost': Decimal('0.00'),
                'tax_amount': Decimal('0.00'),
                'total_amount': Decimal('0.00'),
                'cart_count': get_cart_count(request),
                'username': request.session.get('customer_username'),
                'profile_picture': request.session.get('customer_profile_picture'),
                'checkout_form': None,
            })

        cart_items, totals = self._calculate_cart_totals(request, cart)
        
        checkout_form = CheckoutForm()
        
        currency_context = get_currency_context(request)

        context = {
            'cart_items': cart_items,
            'subtotal': totals['subtotal'],
            'shipping_cost': totals['shipping'],
            'tax_amount': totals['tax'],
            'total_amount': totals['total'],
            'cart_count': get_cart_count(request),
            'username': request.session.get('customer_username'),
            'profile_picture': request.session.get('customer_profile_picture'),
            'checkout_form': checkout_form,
        }
        context.update(currency_context)
        
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        cart = request.session.get('cart', {})
        cart_items, totals = self._calculate_cart_totals(request, cart)
        
        checkout_form = CheckoutForm(request.POST)
        
        currency_context = get_currency_context(request)

        if checkout_form.is_valid():
            
            order_result = self._process_order(request, checkout_form.cleaned_data, cart_items, totals)
            
            if order_result['success']:
                # Clear the cart
                request.session['cart'] = {}
                request.session.modified = True
                
                messages.success(request, f'Order placed successfully! Order ID: {order_result["order_id"]}')
                return redirect('order_confirmation', order_id=order_result['order_id'])
            else:
                print(order_result['error'])
                messages.error(request, order_result['error'])
        else:
            messages.error(request, 'Please correct the errors below.')

        context = {
            'cart_items': cart_items,
            'subtotal': totals['subtotal'],
            'shipping_cost': totals['shipping'],
            'tax_amount': totals['tax'],
            'total_amount': totals['total'],
            'cart_count': get_cart_count(request),
            'username': request.session.get('customer_username'),
            'profile_picture': request.session.get('customer_profile_picture'),
            'checkout_form': checkout_form,
        }
        context.update(currency_context)
        
        return render(request, self.template_name, context)

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
        
        # Calculate shipping, tax, and total
        shipping_base = Decimal('5.00') if subtotal > 0 else Decimal('0.00')
        shipping = convert_cart_prices(shipping_base, currency_context['currency_info']) if shipping_base > 0 else Decimal('0.00')
        
        # Tax calculation (8% GST)
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
        """Process the order and create database records"""
        try:
            username = request.session.get('customer_username')
            customer = Customer.objects.get(username=username)

            # Get currency info to convert back to SGD
            currency_context = get_currency_context(request)
            currency_rate = currency_context['currency_info']['rate']
            
            # Convert total back to SGD for database storage
            total_in_sgd = (totals['total'] / currency_rate).quantize(Decimal('0.01'))

            order = Order.objects.create(
                customer=customer,
                status= 'PENDING',
                shipping_address=f"{form_data['address']}, {form_data['city']}, {form_data['postal_code']}, {form_data['country']}",
                order_notes=form_data.get('order_notes', ''),
                total_amount=total_in_sgd,
                order_date=datetime.now()
            )

            # Create order items
            for item in cart_items:
                try:
                    product = Product.objects.get(sku=item['sku'])
                    # Convert price back to SGD for database storage
                    price_in_sgd = (item['unit_price'] / currency_rate).quantize(Decimal('0.01'))
                    
                    OrderItem.objects.create(
                        order_id=order,
                        product=product,
                        quantity=item['quantity'],
                        price_at_purchase=price_in_sgd
                    )
                except Product.DoesNotExist:
                    return {
                        'success': False,
                        'error': f'Product {item["sku"]} not found.'
                    }
                
            order.save()
            
            return {
                'success': True,
                'order_id': order
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

class order_confirmation_page(View):
    template_name = 'customer_website/order_confirmation.html'

    def get(self, request, order_id, *args, **kwargs):
        try:
            order = Order.objects.get(order_id=order_id)
            
            username = request.session.get('customer_username')
            if not username or order.customer.username != username:
                messages.error(request, 'Order not found or access denied.')
                return redirect('customer_home')

            order_items = OrderItem.objects.filter(order_id=order)
            currency_context = get_currency_context(request)
            
            # Convert prices from SGD to selected currency
            order_total = Decimal('0.00')
            for item in order_items:
                item.converted_price = convert_cart_prices(item.price_at_purchase, currency_context['currency_info'])
                item.item_total = item.converted_price * item.quantity
                order_total += item.item_total
            
            # Convert order total amount
            order.converted_total = convert_cart_prices(order.total_amount, currency_context['currency_info'])

            context = {
                'order': order,
                'order_items': order_items,
                'order_total': order_total,
                'cart_count': get_cart_count(request),
                'username': username,
                'profile_picture': request.session.get('customer_profile_picture'),
            }
            context.update(currency_context)
            
            return render(request, self.template_name, context)
            
        except Order.DoesNotExist:
            messages.error(request, 'Order not found.')
            return redirect('customer_home')


class profile_page(View):
    template_name = 'customer_website/profile.html'

    def get(self, request, *args, **kwargs):
        username = request.session.get('customer_username')
        customer = Customer.objects.get(username=username)
        sort_by = request.GET.get('sort', 'date-desc')
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

        if request.GET.get('logout') == 'true':
            # Clear only customer session keys
            request.session.pop('customer_hasLogin', None)
            request.session.pop('customer_username', None)
            request.session.pop('customer_profile_picture', None)
            request.session.pop('preferred_category', None)
            request.session.pop('browsing_history', None)
            request.session.pop('cart', None)
            request.session.pop('selected_currency', None)
            return redirect('login')
        currency_context = get_currency_context(request)
        
        for order in customer_orders:
            order_total = Decimal('0.00')
            order_items = list(order.items.all())
            for item in order_items:
                item.converted_price = convert_cart_prices(item.price_at_purchase, currency_context['currency_info'])
                item_total = item.converted_price * item.quantity
                order_total += item_total
            order.converted_total = order_total
            order.processed_items = order_items 
        
        context = {
            'customer': customer,
            'username': username,
            'profile_picture': request.session.get('customer_profile_picture'),
            'cart_count': get_cart_count(request),
            'customer_orders': customer_orders,
            'current_sort': sort_by,
        }
        context.update(currency_context)
        return render(request, self.template_name, context)


class about_us_view(View):
    template_name = 'customer_website/about.html'

    def get(self, request, *args, **kwargs):
        currency_context = get_currency_context(request)
        context = {
            'username': request.session.get('customer_username'),
            'profile_picture': request.session.get('customer_profile_picture'),
            'cart_count': get_cart_count(request),
        }
        context.update(currency_context)
        return render(request, self.template_name, context)
