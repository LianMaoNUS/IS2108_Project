from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Customer
from admin_panel.models import Product, Category

def main_page(request):
    """Homepage for AuroraMart"""
    categories = Category.objects.all()[:6]  # Show first 6 categories
    featured_products = Product.objects.all()[:8]  # Show first 8 products
    return render(request, 'customer_website/main_page.html', {
        'categories': categories,
        'featured_products': featured_products
    })

def signup_page(request):
    """Customer registration page"""
    if request.method == 'POST':
        # Get form data - use username instead of email
        username = request.POST.get('username')  # Changed from email
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Basic validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('signup')
        
        # Check if username already exists (not email)
        if Customer.objects.filter(username=username).exists():  # Changed from email
            messages.error(request, "Username already exists!")
            return redirect('signup')
        
        # Create customer (demographics will be collected later)
        customer = Customer.objects.create(
            username=username,  # Changed from email
            password=password  # Will be hashed by your save() method
        )
        
        messages.success(request, "Account created successfully! Please log in.")
        return redirect('login')
    
    return render(request, 'customer_website/signup.html')

def login_page(request):
    """Customer login page"""
    if request.method == 'POST':
        username = request.POST.get('username')  # Changed from email
        password = request.POST.get('password')
        
        # Authenticate user - use username instead of email
        user = authenticate(request, username=username, password=password)
        
        if user is not None and hasattr(user, 'customer'):
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect('customer_home')
        else:
            messages.error(request, "Invalid username or password!")
    
    return render(request, 'customer_website/login.html')

@login_required
def customer_home(request):
    """Dashboard after login"""
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

def logout_view(request):
    """Logout user"""
    logout(request)
    messages.success(request, "You have been logged out successfully!")
    return redirect('main_page')

# Add these to your existing views.py

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