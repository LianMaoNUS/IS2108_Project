import re
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib import messages
from .forms import AdminLoginForm, AdminSignupForm
from AuroraMart.models import Product, Customer, Order, Admin

class loginview(LoginView):
    form_class = AdminLoginForm
    template_name = 'admin_panel/login.html'
    success_url = reverse_lazy('admin_panel/dashboard.html')

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().username}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)

class signupview(View):
    form_class = AdminSignupForm
    template_name = 'admin_panel/signup.html'
    
    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk') 
        admins = Admin.objects.get(pk=pk) if pk else None
        form = self.form_class(instance=admins)
        return render(request, self.template_name, {"form": form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        def check_username(username):
            if len(username) < 6:
                return "Username must be at least 6 characters long."
            if not re.match(r'^[a-zA-Z0-9_]+$', username):
                return "Username can only contain letters, numbers, and underscores."
            return "Valid"
        
        def check_password(password,check_password):
            if  password != check_password:
                return "Passwords do not match."
            if len(password) < 8:
                return "Password must be at least 8 characters long."
            if not re.search(r'[A-Z]', password):
                return "Password must contain at least one uppercase letter."
            if not re.search(r'[a-z]', password):
                return "Password must contain at least one lowercase letter."
            if not re.search(r'[0-9]', password):
                return "Password must contain at least one digit."
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                return "Password must contain at least one special character."
            return "Valid"
        
        if form.is_valid():
            username=form.cleaned_data['username']
            password=form.cleaned_data['password']
            checked_password=form.cleaned_data['password_check']
            username_check =check_username(username)
            password_check =check_password(password,checked_password)
            if username_check != "Valid":
                return render(request, self.template_name, {"form": form, "error": username_check})
            elif password_check != "Valid":
                return render(request, self.template_name, {"form": form, "error": password_check})
            else:
                new_admin = Admin(
                    admin_id="A" + form.cleaned_data['username'],
                    username=username,
                    password=password,
                    role=form.cleaned_data['role']
                )
                new_admin.save()
                return redirect('admin_login')
        return render(request, self.template_name, {"form": form})


class dashboardview(View):

    def get(self, request, *args, **kwargs):
        view_type = self.request.GET.get('type', 'products')
        queryset = None
        page_title = ""
        fields = ""

        if view_type == 'products':
            queryset = Product.objects.all()
            page_title = 'Products'
            fields = [field.name for field in Product._meta.get_fields()]
        elif view_type == 'customers':
            queryset = Customer.objects.all()
            page_title = 'Customers'
            fields = [field.name for field in Customer._meta.get_fields()]
        elif view_type == 'inventory':
            queryset = Order.objects.all()
            page_title = 'Inventory'
            fields = [field.name for field in Order._meta.get_fields()] 

        template_name = 'admin_panel/dashboard.html'

        return render(request, template_name, {'type': view_type,'queryset': queryset, 'page_title': page_title,'fields': fields})
    
    def post(self, request, *args, **kwargs):
        return render(request, self.template_name)


def index(request):
    return render(request, 'admin_panel/index.html')


