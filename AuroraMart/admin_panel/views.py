import re
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib import messages
from .forms import AdminLoginForm, AdminSignupForm, ProductForm,CustomerForm,OrderForm,CategoryForm
from AuroraMart.models import Product, Customer, Order, Admin,Category

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

        view_configs = {
            'products':   {'model': Product,  'form': ProductForm,  'title': 'Products'},
            'customers':  {'model': Customer, 'form': CustomerForm, 'title': 'Customers'},
            'inventory':  {'model': Order,    'form': OrderForm,    'title': 'Inventory'},
            'categories': {'model': Category, 'form': CategoryForm, 'title': 'Categories'},
        }

        view_type = self.request.GET.get('type', 'products')
        pk = kwargs.get('pk')
        config = view_configs.get(view_type)
        Model = config['model']
        Form = config['form']
    
        page_title = config['title']
        queryset = Model.objects.all()
        instance = Model.objects.get(pk=pk) if pk else None
        form = Form(instance=instance)
        fields = [field.name for field in Model._meta.get_fields()]
        table_rows = []


        if view_type == 'products':
            for item in queryset:
                table_rows.append([item.sku, item.product_name, item.category.name, f"${item.unit_price}", item.quantity_on_hand])
    
        elif view_type == 'customers':
            for item in queryset:
             table_rows.append([item.customer_id, item.username, item.age, item.gender, item.employment_status, item.occupation])
            
        elif view_type == 'inventory':
            for item in queryset:
                table_rows.append([item.order_id, item.customer.username, item.status])
            
        elif view_type == 'categories':
            fields = ["category_id", "name", "parent_category"]
            for item in queryset:
             parent_name = item.parent_category.name if item.parent_category else "None"
            table_rows.append([item.category_id, item.name, parent_name])

        template_name = 'admin_panel/dashboard.html'
        context = {
            'type': view_type,
            'queryset': queryset,
            'page_title': page_title,
            'fields': fields,
            'form': form,
            'table_rows': table_rows,
        }
        return render(request, template_name, context)
    
    def post(self, request, *args, **kwargs):
        view_type = self.request.GET.get('type', 'products')
        if view_type == 'categories':
            category = Category.objects.get(pk=kwargs.get('pk')) if kwargs.get('pk') else None
            form = CategoryForm(request.POST, instance=category)
            if form.is_valid():
                form.save()
                return redirect(f"{reverse_lazy('admin_dashboard')}?type=categories")
            else:
                messages.error(request, "There were errors in the form. Please correct them.")
            
            #add others
        return render(request, self.template_name)


def index(request):
    return render(request, 'admin_panel/index.html')


