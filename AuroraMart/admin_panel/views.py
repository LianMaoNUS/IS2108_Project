import re
import csv
import datetime
import datetime
import json
from django.utils import timezone
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
from admin_panel.models import Admin,Order,Category,Product,OrderItem
from django.db.models import Sum, Count, Avg,F

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
        'dashboard': {
            'model': None, 'form': None, 'title': 'Dashboard Overview',
            'fields': [], 'rows': lambda item: []
        },
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
        }
    }

    def dispatch(self, request, *args, **kwargs):
        self.view_type = request.GET.get('type', 'dashboard')
        self.config = self.view_configs.get(self.view_type)
        if not self.config:
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def export_to_csv(self,context):
        response = HttpResponse(
            content_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{self.view_type}_{datetime.date.today()}.csv"'
            },
        )
        writer = csv.writer(response)
        queryset = self.config['model'].objects.all()
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
        context = {
            'type': self.view_type,
            'page_title': self.config['title'],
            'username': self.request.session.get("username"),
            'user_role': self.request.session.get("role"),
            'admin_details': self.request.GET.get('admin_details') == 'true' 
        }

        if self.view_type != 'dashboard':
            queryset = self.config['model'].objects.all()
            fields = self.config['fields']
            sort_by = self.request.GET.get('sort_by', fields[0] if fields else None)
            rows = self.request.GET.get('rows', '10')

            if sort_by and sort_by in fields:
                queryset = queryset.order_by(sort_by)

            try:
                queryset = queryset[:int(rows)]
            except (ValueError, TypeError):
                queryset = queryset[:10]

            table_rows = [self.config['rows'](item) for item in queryset]

            context.update({
                'fields': fields,
                'table_rows': table_rows,
                'sort_by': sort_by,
                'rows': rows,
            })
        else:
            now = timezone.now()
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            thirty_days_ago = now - datetime.timedelta(days=30)

            orders_this_month = Order.objects.filter(order_date__gte=start_of_month, status='COMPLETED').annotate(
                total_value=Sum(F('items__price_at_purchase') * F('items__quantity'))
            )
            total_revenue_month = orders_this_month.aggregate(total=Sum('total_value'))['total'] or 0
            num_orders_month = orders_this_month.count()
            average_order_value = total_revenue_month / num_orders_month if num_orders_month > 0 else 0

            context['total_revenue_month'] = total_revenue_month
            context['average_order_value'] = average_order_value

            sales_trend = Order.objects.filter(
                order_date__gte=thirty_days_ago, status='COMPLETED'
            ).annotate(
                date=F('order_date__date') # Group by date
            ).values('date').annotate(
                daily_total=Sum(F('items__price_at_purchase') * F('items__quantity'),default=0)
            ).order_by('date')

            # Prepare for Chart.js MAY REMOVE
            chart_labels = [entry['date'].strftime('%b %d') for entry in sales_trend]
            chart_data = [float(entry['daily_total']) for entry in sales_trend]
            context['chart_labels'] = json.dumps(chart_labels or [])
            context['chart_data'] = json.dumps(chart_data or [])
            print(chart_labels)

            # --- Customers ---
            try:
                 new_customers_month = Customer.objects.filter(date_joined__gte=start_of_month).count()
            except AttributeError: # If no date_joined field
                 new_customers_month = "N/A" # Or query differently if you have another creation field

            context['new_customers_month'] = new_customers_month
            context['total_customers'] = Customer.objects.count()

            # --- Products & Inventory ---
            low_stock_count = Product.objects.filter(quantity_on_hand__lt=F('reorder_quantity')).count()
            context['low_stock_count'] = low_stock_count

            # Top selling products (requires OrderItem model)
            top_products = OrderItem.objects.filter(
                order_id__order_date__gte=start_of_month, order_id__status='COMPLETED'
            ).values('product__product_name').annotate(
                units_sold=Sum('quantity')
            ).order_by('-units_sold')[:5]

            context['top_selling_products'] = [{'name': p['product__product_name'], 'units_sold': p['units_sold']} for p in top_products]

            # --- Orders ---
            pending_orders_count = Order.objects.filter(status='PENDING').count()
            context['pending_orders_count'] = pending_orders_count

            recent_orders = Order.objects.annotate(
                 total_value=Sum(F('items__price_at_purchase') * F('items__quantity'))
            ).order_by('-order_date')[:5] 
            context['recent_orders'] = recent_orders

        context.update(kwargs)
        return context
    
    def get(self, request, *args, **kwargs):
        if (self.request.GET.get('logout') == 'true'):
            request.session.flush()
            return redirect('admin_login')
        
        if self.view_type != 'dashboard':
            form_to_display = None
            form = self.config['form']
            model = self.config['model']
            if request.GET.get('admin_details') == 'true':
                instance = Admin.objects.get(username=request.session["username"])
                form_to_display = AdminSignupForm(instance=instance)
            elif request.GET.get('action') == 'Update' and request.GET.get('id'):
                instance = model.objects.get(pk=request.GET.get('id'))
                form_to_display = form(instance=instance)
            elif request.GET.get('action') == 'Delete':
                model.objects.filter(pk=self.request.GET.get('id')).delete()
                context = self.get_context_data(form=form_to_display)
                return render(request, self.template_name, context)
            else:
                form_to_display = form

            context = self.get_context_data(form=form_to_display)

            if (self.request.GET.get('export') == 'csv'):
                return self.export_to_csv(context)
            return render(request, self.template_name, context)
            
        else:
            context = self.get_context_data()
            return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        admin_update = self.request.GET.get('admin_details')
        action = self.request.GET.get('action')
        form_template = f"admin_panel/dashboard&type={request.GET.get("type")}"
        model = self.config['model']
        
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
            form_class = self.config['form']
            try:
                instance_id = self.request.GET.get('id')
                form_instance = model.objects.get(pk=instance_id)
            except model.DoesNotExist:
                context = self.get_context_data(error_message=["Item to update not found."])
                return render(request, self.template_name, context)

        else:
            form_class = self.config['form']

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