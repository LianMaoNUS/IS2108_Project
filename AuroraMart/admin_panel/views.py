import csv
import datetime
import json

from django.utils import timezone
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from django.views import View
from django.db.models import Sum, F
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .forms import AdminLoginForm, AdminSignupForm, ProductForm, CustomerForm, OrderForm, CategoryForm, OrderItemForm
from AuroraMart.models import User 
from customer_website.models import Customer
from admin_panel.models import Admin, Order, Category, Product, OrderItem

def error_check(check):
    return [msg for err_list in check for msg in err_list]

def record_selector(request, model, type):
    ids_param = request.GET.get('id', '')
    ids_param = ids_param.replace('%2C', ',').replace('%2c', ',')
    ids = [i for i in ids_param.split(',') if i]
    
    if ids:
        queryset = model.objects.filter(pk__in=ids)
        if type == 'delete':
            return queryset.delete()
        elif type == 'filter':
            return queryset
    return None


class loginview(View):
    form_class = AdminLoginForm
    template_name = 'admin_panel/login.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                admin = Admin.objects.get(username=username)
                if check_password(password, admin.password):
                    request.session['hasLogin'] = True
                    request.session['username'] = username
                    request.session['role'] = admin.role
                    request.session['profile_picture'] = admin.profile_picture
                    return redirect('admin_dashboard')
                else:
                    error_message = "Incorrect password"
            except Admin.DoesNotExist:
                error_message = "User not found"
            except ValueError as e:
                error_message = f"Invalid data format: {str(e)}"

        return render(request, self.template_name, {"form": form,"error_message": error_message})

class signupview(View):
    form_class = AdminSignupForm
    template_name = 'admin_panel/signup.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            form.save() 
            return redirect('admin_login')
        else:
            return render(request, self.template_name, {
                "form": form, 
                "error_message": error_check(form.errors.values())
            })

class dashboardview(View):
    template_name = 'admin_panel/dashboard.html'
    view_configs = {
        'dashboard': {
            'model': None, 'form': None, 'title': 'Dashboard Overview',
            'fields': [], 'rows': lambda item: []
        },
        'products': {
            'model': Product, 'form': ProductForm, 'title': 'Products',
            'fields': ["sku", "product_name", "category", "subcategory", "unit_price", "quantity_on_hand"],
            'rows': lambda item: [
                item.sku, 
                item.product_name, 
                item.category.name if item.category else '', 
                item.subcategory.name if item.subcategory else '', 
                f"${item.unit_price}", 
                item.quantity_on_hand
            ]
        },
        'customers': {
            'model': Customer, 'form': CustomerForm, 'title': 'Customers',
            'fields': ["customer_id", "username", "age", "gender", "employment_status", "occupation","education","household_size","has_children","monthly_income_sgd","preferred_category"],
            'rows': lambda item: [item.customer_id, item.username, item.age, item.gender, item.employment_status, item.occupation,item.education,item.household_size,item.has_children,item.monthly_income_sgd,item.preferred_category]
        },
        'orders': {
            'model': Order, 'form': OrderForm, 'title': 'Orders',
            'fields': ["order_id", "customer", "status","shipping_address","total_amount"],
            'rows': lambda item: [item.order_id, item.customer.username, item.status, item.shipping_address, item.total_amount]
        },
        'categories': {
            'model': Category, 'form': CategoryForm, 'title': 'Categories',
            'fields': ["category_id", "name","parent_category"],
            'rows': lambda item: [item.category_id, item.name, item.parent_category.name if item.parent_category else '']
        },
        'orderitem': {
            'model': OrderItem, 'form': OrderItemForm, 'title': 'Order Items',
            'fields': ["OrderItem_id", "order_id", "product"," quantity","price_at_purchase"],
            'rows': lambda item: [item.OrderItem_id, item.order_id.order_id, item.product.product_name, item.quantity,item.price_at_purchase]
        }
    }

    def dispatch(self, request, *args, **kwargs):
        self.view_type = request.GET.get('type', 'dashboard')
        self.config = self.view_configs.get(self.view_type)
        if not self.config:
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def _get_queryset(self):
        model = self.config['model']
        queryset = record_selector(self.request, model, 'filter')
        if queryset is None:
            queryset = model.objects.all()

        fields = self.config['fields']
        sort_by = self.request.GET.get('sort_by', fields[0] if fields else None)
        
        if sort_by and sort_by in fields:
            queryset = queryset.order_by(sort_by)
        return queryset

    def _get_dashboard_stats(self):
        context = {}
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        thirty_days_ago = now - datetime.timedelta(days=30)
        orders_this_month = Order.objects.filter(
            order_date__gte=start_of_month, status='COMPLETED'
        ).annotate(
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
            date=F('order_date__date')
        ).values('date').annotate(
            daily_total=Sum(F('items__price_at_purchase') * F('items__quantity'), default=0)
        ).order_by('date')

        chart_labels = [entry['date'].strftime('%b %d') for entry in sales_trend]
        chart_data = [float(entry['daily_total']) for entry in sales_trend]
        context['chart_labels'] = json.dumps(chart_labels or [])
        context['chart_data'] = json.dumps(chart_data or [])

        try:
            new_customers_month = Customer.objects.filter(date_joined__gte=start_of_month).count()
        except AttributeError: 
            new_customers_month = "N/A"  
        context['new_customers_month'] = new_customers_month
        context['total_customers'] = Customer.objects.count()

        low_stock_count = Product.objects.filter(quantity_on_hand__lt=F('reorder_quantity')).count()
        context['low_stock_count'] = low_stock_count

        top_products = OrderItem.objects.filter(
            order_id__order_date__gte=start_of_month, order_id__status='COMPLETED'
        ).values('product__product_name').annotate(
            units_sold=Sum('quantity')
        ).order_by('-units_sold')[:5]
        context['top_selling_products'] = list(top_products)

        pending_orders_count = Order.objects.filter(status='PENDING').count()
        context['pending_orders_count'] = pending_orders_count
        
        context['recent_orders'] = Order.objects.annotate(
            total_value=Sum(F('items__price_at_purchase') * F('items__quantity'))
        ).order_by('-order_date')[:5]

        return context

    def _get_list_view_context(self):
        context = {}
        queryset = self._get_queryset()
        
        fields = self.config['fields']
        rows = self.request.GET.get('rows', '10')
        page_number = self.request.GET.get('page', 1)

        paginator = Paginator(queryset, int(rows) if rows.isdigit() else 10)

        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
            page_number = 1
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
            page_number = paginator.num_pages

        table_rows = [self.config['rows'](item) for item in page_obj]

        context.update({
            'fields': fields,
            'table_rows': table_rows,
            'sort_by': self.request.GET.get('sort_by', fields[0] if fields else None),
            'rows': rows,
            'page_obj': page_obj,
            'paginator': paginator,
            'current_page': int(page_number),
            'total_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None
        })
        return context

    def _get_context_data(self, **kwargs):
        """Builds the context dictionary for the template."""
        context = {
            'type': self.view_type,
            'page_title': self.config['title'],
            'username': self.request.session.get("username"),
            'user_role': self.request.session.get("role"),
            'profile_picture': self.request.session.get("profile_picture"),
            'admin_details': self.request.GET.get('admin_details') == 'true'
        }

        if self.view_type == 'dashboard':
            stats_context = self._get_dashboard_stats()
            context.update(stats_context)
        else:
            list_context = self._get_list_view_context()
            context.update(list_context)
        
        context.update(kwargs)
        return context

    def _export_to_csv(self):
        response = HttpResponse(
            content_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{self.view_type}_{datetime.date.today()}.csv"'
            },
        )
        writer = csv.writer(response)
        queryset = self._get_queryset()
        fields = self.config['fields']
        
        writer.writerow(fields)
        row_builder = self.config['rows']
        
        for item in queryset:
            row_data = row_builder(item)
            processed_row = [cell if cell not in [None, ""] else "None" for cell in row_data]
            writer.writerow(processed_row)

        return response
    
    def _handle_admin_details_get(self):
        try:
            instance = Admin.objects.get(username=self.request.session["username"])
            form = AdminSignupForm(instance=instance)
            context = self._get_context_data(form=form, admin_details=True)
            return render(self.request, self.template_name, context)
        except Admin.DoesNotExist:
            context = self._get_context_data(error_message=["Admin user not found."])
            return render(self.request, self.template_name, context)
        except KeyError:
            context = self._get_context_data(error_message=["Session expired. Please login again."])
            return render(self.request, self.template_name, context)
        except Exception as e:
            context = self._get_context_data(error_message=[f"An error occurred: {str(e)}"])
            return render(self.request, self.template_name, context)

    def get(self, request, *args, **kwargs):
        # 1. Handle Logout
        if self.request.GET.get('logout') == 'true':
            request.session.flush()
            return redirect('admin_login')
        
        # 2. Handle Admin Details request (same logic for all pages)
        if self.request.GET.get('admin_details') == 'true':
            return self._handle_admin_details_get()
        
        # 3. Handle CSV Export
        if self.request.GET.get('export') == 'csv' and self.view_type != 'dashboard':
            return self._export_to_csv()

        # 4. Handle Dashboard View
        if self.view_type == 'dashboard':
            context = self._get_context_data()
            return render(request, self.template_name, context)

        # 5. Handle List Views (Products, Orders, etc.)
        form_to_display = None
        model = self.config['model']
        form = self.config['form']
        action = request.GET.get('action')
        
        if action == 'Update' and request.GET.get('id'):
            try:
                instance = model.objects.get(pk=request.GET.get('id'))
                form_to_display = form(instance=instance)
            except model.DoesNotExist:
                pass
            except ValueError as e:
                context = self._get_context_data(error_message=[f"Invalid ID format: {str(e)}"])
                return render(request, self.template_name, context)
            except Exception as e:
                context = self._get_context_data(error_message=[f"Error loading record: {str(e)}"])
                return render(request, self.template_name, context)
        elif action == 'Delete':
            try:
                record_selector(request, model, 'delete')
            except Exception as e:
                context = self._get_context_data(error_message=[f"Error deleting record: {str(e)}"])
                return render(request, self.template_name, context)
            return redirect(f"{reverse('admin_dashboard')}?type={self.view_type}")
        else:
            form_to_display = form

        context = self._get_context_data(form=form_to_display)
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        admin_update = self.request.GET.get('admin_details') == 'true'
        action = self.request.GET.get('action')
        model = self.config['model']
        
        form_instance = None
        form_class = None

        if admin_update:
            try:
                form_instance = Admin.objects.get(username=request.session["username"])
                form_class = AdminSignupForm
            except Admin.DoesNotExist:
                context = self._get_context_data(error_message=["Admin user not found."])
                return render(request, self.template_name, context)
        
        elif action == 'Update':
            form_class = self.config['form']
            try:
                instance_id = self.request.GET.get('id')
                form_instance = model.objects.get(pk=instance_id)
            except model.DoesNotExist:
                context = self._get_context_data(error_message=["Item to update not found."])
                return render(request, self.template_name, context)
        else:

            form_class = self.config['form']

        form = form_class(request.POST, instance=form_instance)

        if form.is_valid():
            form.save() 
            
            if admin_update:
                request.session['username'] = form.cleaned_data['username']
                request.session['role'] = form.cleaned_data['role']

            return redirect(f"{reverse('admin_dashboard')}?type={self.view_type}")
        else:
            context = self._get_context_data(
                form=form, 
                error_message=error_check(form.errors.values()),
                admin_details=admin_update 
            )
            return render(request, self.template_name, context)

def get_subcategories(request):
    category_id = request.GET.get('category_id')
    subcategories = []
    
    if category_id:
        try:
            main_category = Category.objects.get(pk=category_id)
            subcategories_qs = Category.objects.filter(parent_category=main_category)
            subcategories = [
                {'id': subcat.category_id, 'name': subcat.name} 
                for subcat in subcategories_qs
            ]
        except Category.DoesNotExist:
            pass
    
    return JsonResponse({'subcategories': subcategories})