from django.shortcuts import redirect
from django.urls import reverse

class AdminAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        if (request.path.startswith(reverse('admin_dashboard')) or \
           request.path.startswith(reverse('admin_list'))) and \
           not request.path.startswith(reverse('admin_login')) and \
           not request.path.startswith(reverse('admin_signup')):
            if not request.session.get('admin_hasLogin'):
                return redirect('admin_login')
            
        response = self.get_response(request)
        
        return response