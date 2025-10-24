import re
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.views import View
from django.contrib import messages
from .forms import AdminLoginForm, AdminSignupForm, ProductForm,CustomerForm,OrderForm,CategoryForm
from AuroraMart.models import Product, Customer, Order, Admin,Category
from django.http import HttpResponse

class loginview(View):
    form_class = AdminLoginForm
    template_name = 'admin_panel/login.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            print( "form is valid")
            username=form.cleaned_data['username']
            password=form.cleaned_data['password']
            try:
                admin = Admin.objects.get(username=username)
                if check_password(password, admin.password):
                    request.session['hasLogin'] = True
                    request.session['username'] = username
                    request.session['role'] = admin.role
                    return redirect('admin_dashboard')
            except Admin.DoesNotExist:
                return render(request, self.template_name, {"form": form, "errors": "Invalid username or password."})
        return render(request, self.template_name, {"form": form})

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
        sort_by = self.request.GET.get('sort_by')
        rows = self.request.GET.get('rows', '10')
        pk = kwargs.get('pk')
        config = view_configs.get(view_type)
        Model = config['model']
        Form = config['form']
        page_title = config['title']
        queryset = Model.objects.all()
        instance = Model.objects.get(pk=pk) if pk else None
        form = Form(instance=instance)
        fields = []
        table_rows = []
        username = request.session["username"]
        user_role = request.session["role"]

        if (self.request.GET.get('logout') == 'true'):
            request.session.flush()
            return redirect('admin_login')
        
        if self.request.GET.get('action') == 'update':
            id = self.request.GET.get('id')
            data = Model.objects.get(pk=id)
            form = Form(instance=data)
        elif self.request.GET.get('action') == 'delete':
            Model.objects.filter(pk=self.request.GET.get('id')).delete()
            return redirect(f"{reverse_lazy('admin_dashboard')}?type={view_type}")
        
        def sort_rows(queryset=queryset, rows=rows,sort_by=sort_by):
            if sort_by in fields:
                 queryset = queryset.order_by(sort_by)
                 try:
                    queryset = queryset[:int(rows)]
                 except (ValueError, TypeError):
                    queryset = queryset[:10]
            return queryset


        if view_type == 'products':
            fields = ["sku", "product_name", "category", "unit_price", "quantity_on_hand"]
            queryset = sort_rows()
            for item in queryset:
                table_rows.append([item.sku, item.product_name, item.category.name, f"${item.unit_price}", item.quantity_on_hand])
    
        elif view_type == 'customers':
            fields = ["customer_id", "username", "age", "gender", "employment_status", "occupation"]
            queryset = sort_rows()
            for item in queryset:
             table_rows.append([item.customer_id, item.username, item.age, item.gender, item.employment_status, item.occupation])
            
        elif view_type == 'inventory':
            fields = ["order_id", "customer", "status"]
            queryset = sort_rows()
            for item in queryset:
                table_rows.append([item.order_id, item.customer.username, item.status])
            
        elif view_type == 'categories':
            fields = ["category_id", "name", "parent_category"]
            queryset = sort_rows()
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
            'sort_by': sort_by,
            'rows': rows,
            'username': username,
            'user_role': user_role
        }
        
        return render(request, template_name, context)
    
    def post(self, request, *args, **kwargs):
        view_type = self.request.GET.get('type', 'products')
        action = self.request.GET.get('action')

        if action == 'update':
            id = self.request.GET.get('id')
            if view_type == 'products':
                product = Product.objects.get(pk=id)
                form = ProductForm(request.POST, instance=product)
                if form.is_valid():
                    product.sku = form.cleaned_data['sku']
                    product.product_name = form.cleaned_data['product_name']
                    product.category = form.cleaned_data['category']    
                    product.unit_price = form.cleaned_data['unit_price']
                    product.quantity_on_hand = form.cleaned_data['quantity_on_hand']
                    product.save()
                    return redirect(f"{reverse_lazy('admin_dashboard')}?type=products")
                else:
                    messages.error(request, "There were errors in the form. Please correct them.")
            elif view_type == 'categories':
                category = Category.objects.get(pk=id)
                form = CategoryForm(request.POST, instance=category)
                if form.is_valid():
                    category.name = form.cleaned_data['name']
                    category.parent_category = form.cleaned_data['parent_category']    
                    category.save()
                    return redirect(f"{reverse_lazy('admin_dashboard')}?type=categories")
                else:
                    messages.error(request, "There were errors in the form. Please correct them.")
            elif view_type == 'customers':
                customer = Customer.objects.get(pk=id)
                form = CustomerForm(request.POST, instance=customer)    
                if form.is_valid():
                    customer.username = form.cleaned_data['username']
                    customer.age = form.cleaned_data['age']
                    customer.gender = form.cleaned_data['gender']    
                    customer.employment_status = form.cleaned_data['employment_status']
                    customer.occupation = form.cleaned_data['occupation']
                    customer.save() 
                    return redirect(f"{reverse_lazy('admin_dashboard')}?type=customers")   
        else:
             if view_type == 'products':
                product = Product.objects.get(pk=kwargs.get('pk')) if kwargs.get('pk') else None
                form = ProductForm(request.POST, instance=product)
                if form.is_valid():
                    form.save()
                    return redirect(f"{reverse_lazy('admin_dashboard')}?type=products")
                else:
                    messages.error(request, "There were errors in the form. Please correct them.")
             elif view_type == 'categories':
                category = Category.objects.get(pk=kwargs.get('pk')) if kwargs.get('pk') else None
                form = CategoryForm(request.POST, instance=category)
                if form.is_valid():
                    form.save()
                    return redirect(f"{reverse_lazy('admin_dashboard')}?type=categories")
             elif view_type == 'customers':
                customer = Customer.objects.get(pk=kwargs.get('pk')) if kwargs.get('pk') else None
                form = CustomerForm(request.POST, instance=customer)    
                if form.is_valid():
                    form.save()
                    return redirect(f"{reverse_lazy('admin_dashboard')}?type=customers")
                else:
                    messages.error(request, "There were errors in the form. Please correct them.")
        return redirect(f"{reverse_lazy('admin_dashboard')}")
    


