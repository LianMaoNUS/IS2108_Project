from django.shortcuts import redirect
from django.urls import reverse

class CustomerAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        if request.path == '/' or \
           request.path.startswith(reverse('customer_home')) or \
           request.path.startswith(reverse('cart')) or \
           request.path.startswith(reverse('checkout')) or \
           request.path.startswith('/order-confirmation/') or \
           request.path.startswith('/product/') or \
           request.path.startswith(reverse('all_products')) or \
           request.path.startswith(reverse('about')) or \
           request.path.startswith(reverse('profile')):
            if not request.session.get('customer_hasLogin'):
                return redirect('login')
            
        if request.path == reverse('new_user'):
            if not request.session.get('new_user'):
                return redirect('login')
            
        response = self.get_response(request)
        
        return response