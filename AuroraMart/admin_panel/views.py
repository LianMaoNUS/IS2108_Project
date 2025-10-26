import re
import csv
import datetime
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.views import View
from django.contrib import messages
from .forms import AdminLoginForm, AdminSignupForm, ProductForm,CustomerForm,OrderForm,CategoryForm
from AuroraMart.models import User
from customer_website.models import Customer
from admin_panel.models import Admin,Order,Category,Product

def error_check(check):
    errors =[]
    for error_list in check:
            for error_message in error_list:
                errors.append(error_message)
    return errors


class loginview(View):
    form_class = AdminLoginForm
    template_name = 'admin_panel/login.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        error_message = []
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
                else:
                    error_message.append("Incorrect password")
                
            except Admin.DoesNotExist:
                error_message.append("User not found")
        return render(request, self.template_name, {"form": form,"error_message": error_message})

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
        
        if form.is_valid():
                new_admin = Admin(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password'],
                    role=form.cleaned_data['role']
                )
                new_admin.save()
                return render(request, 'admin_panel/login', {"form": form})
        else:
            return render(request,self.template_name,{"form": form, "error_message": error_check(error_check(form.errors.values()))})
            

class dashboardview(View):
    template_name = 'admin_panel/dashboard.html'
    view_configs = {
        'products': {
            'model': Product, 'form': ProductForm, 'title': 'Products',
            'fields': ["sku", "product_name", "category", "unit_price", "quantity_on_hand"],
            'rows': lambda item: [item.sku, item.product_name, item.category, f"${item.unit_price}", item.quantity_on_hand]
        },
        'customers': {
            'model': Customer, 'form': CustomerForm, 'title': 'Customers',
            'fields': ["customer_id", "username", "age", "gender", "employment_status", "occupation","education","household_size","has_children","monthly_income_sgd","preferred_category"],
            'rows': lambda item: [item.customer_id, item.username, item.age, item.gender, item.employment_status, item.occupation,item.education,item.household_size,item.has_children,item.monthly_income_sgd,item.preferred_category]
        },
        'orders': {
            'model': Order, 'form': OrderForm, 'title': 'Orders',
            'fields': ["order_id", "customer", "status"],
            'rows': lambda item: [item.order_id, item.customer.username, item.status]
        },
        'categories': {
            'model': Category, 'form': CategoryForm, 'title': 'Categories',
            'fields': ["category_id", "name", "parent_category"],
            'rows': lambda item: [item.category_id, item.name, item.parent_category.name if item.parent_category else "None"]
        },
    }

    def dispatch(self, request, *args, **kwargs):
        self.view_type = request.GET.get('type', 'products')
        self.config = self.view_configs.get(self.view_type)
        if not self.config:
            return redirect('admin_dashboard')
            
        self.Model = self.config['model']
        self.Form = self.config['form']
        return super().dispatch(request, *args, **kwargs)
    
    def export_to_csv(self,context):
        response = HttpResponse(
            content_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{self.view_type}_{datetime.date.today()}.csv"'
            },
        )
        writer = csv.writer(response)
        queryset = self.Model.objects.all()
        print(context)
        fields = self.config['fields']
        sort_by = self.request.GET.get('sort_by', fields[0]) 

        if sort_by in fields:
            queryset = queryset.order_by(sort_by)
        
        writer.writerow(fields)
        row_builder = self.config['rows']
        for item in queryset:
            row_data = row_builder(item)
            processed_row = [cell if cell not in [None, ""] else "None" for cell in row_data]
            writer.writerow(processed_row)
            
        return response
    
    def get_context_data(self, **kwargs):
        queryset = self.Model.objects.all()
        fields = self.config['fields']
        sort_by = self.request.GET.get('sort_by',fields[0])
        rows = self.request.GET.get('rows', '10')
        
        if sort_by in fields:
            queryset = queryset.order_by(sort_by)
        
        try:
            queryset = queryset[:int(rows)]
        except (ValueError, TypeError):
            queryset = queryset[:10]

        table_rows = [self.config['rows'](item) for item in queryset]

        context = {
            'type': self.view_type,
            'page_title': self.config['title'],
            'fields': fields,
            'table_rows': table_rows,
            'sort_by': sort_by,
            'rows': rows,
            'username': self.request.session.get("username"),
            'user_role': self.request.session.get("role"),
            'admin_details': self.request.GET.get('admin_details'),
            'action': self.request.GET.get('action','')
        }
        
        context.update(kwargs)
        return context
    
    def get(self, request, *args, **kwargs):
        if (self.request.GET.get('logout') == 'true'):
            request.session.flush()
            return redirect('admin_login')
        
        
        form_to_display = None
        if request.GET.get('admin_details') == 'true':
            instance = Admin.objects.get(username=request.session["username"])
            form_to_display = AdminSignupForm(instance=instance)
        elif request.GET.get('action') == 'Update' and request.GET.get('id'):
            instance = self.Model.objects.get(pk=request.GET.get('id'))
            form_to_display = self.Form(instance=instance)
        elif request.GET.get('action') == 'Delete':
            self.Model.objects.filter(pk=self.request.GET.get('id')).delete()
            context = self.get_context_data(form=form_to_display)
            return render(request, self.template_name, context)
        else:
            form_to_display = self.Form()


        context = self.get_context_data(form=form_to_display)
        if (self.request.GET.get('export') == 'csv'):
            return self.export_to_csv(context)
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        admin_update = self.request.GET.get('admin_details')
        action = self.request.GET.get('action')
        form_template = f"admin_panel/dashboard&type={request.GET.get("type")}"
        
        form_instance = None
        form_class = None

        if admin_update == 'true':
            try:
                form_instance = Admin.objects.get(username=request.session["username"])
                form_class = AdminSignupForm
            except Admin.DoesNotExist:
                context = self.get_context_data(error_message=["Admin user not found."])
                return render(request, self.template_name, context)
        
        elif action == 'Update':
            form_class = self.Form
            try:
                instance_id = self.request.GET.get('id')
                form_instance = self.Model.objects.get(pk=instance_id)
            except self.Model.DoesNotExist:
                context = self.get_context_data(error_message=["Item to update not found."])
                return render(request, self.template_name, context)

        else:
            form_class = self.Form

        form = form_class(request.POST, instance=form_instance)

        if form.is_valid():
            
            form.save() 

            if admin_update == 'true':
                request.session['username'] = form.cleaned_data['username']
                request.session['role'] = form.cleaned_data['role']

            return redirect(f"{reverse_lazy('admin_dashboard')}?type={request.GET.get("type")}")
        else:
            context = self.get_context_data(form=form, error_message=error_check(form.errors.values()))
            return render(request, self.template_name, context)