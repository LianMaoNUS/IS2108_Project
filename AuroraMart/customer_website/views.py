from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Customer
from admin_panel.models import Product, Category
from django.views import View
from .forms import CustomerLoginForm, CustomerSignupForm,CustomerForm
from django.contrib.auth.hashers import check_password

def error_check(check):
    return [msg for err_list in check for msg in err_list]

def main_page(request):
    if request.GET.get('logout') == 'true':
        request.session.flush()
        return redirect('login')
    categories = Category.objects.all()[:6]  # Show first 6 categories
    featured_products = Product.objects.all()[:8]  # Show first 8 products
    return render(request, 'customer_website/main_page.html', {
        'categories': categories,
        'featured_products': featured_products
    })

class signupview(View):
    form_class = CustomerSignupForm
    template_name = 'customer_website/signup.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            form.save() 
            return redirect('new_user')
        else:
            return render(request, self.template_name, {
                "form": form, 
                "error_message": error_check(form.errors.values())
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
    
        return render(request, self.template_name, {"form": form})
    
class new_userview(View):
    template_name = 'customer_website/new_user.html'
    customer_details_form_class = CustomerForm

    def get(self, request, *args, **kwargs):
        form = self.customer_details_form_class()
        return render(request, self.template_name, {"form": form})
    
    def post(self, request, *args, **kwargs):
        form = self.customer_details_form_class(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customer_home')
        else:
            return render(request, self.template_name, {
                "form": form, 
                "error_message": error_check(form.errors.values())
            })  

def customer_home(request):
    """Dashboard after login"""

    if request.GET.get('logout') == 'true':
        request.session.flush()
        return redirect('login')
    
    if hasattr(request.user, 'customer'):
        categories = Category.objects.all()
        products = Product.objects.all()[:12]
        return render(request, 'customer_website/customer_home.html', {
            'categories': categories,
            'products': products,
            'customer': request.user.customer
        })
    else:
        messages.error(request, "Access denied!")
        return redirect('main_page')


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