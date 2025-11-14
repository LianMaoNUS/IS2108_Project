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
from django.core.mail import send_mail
from django.conf import settings

from .forms import (
    AdminLoginForm, AdminSignupForm, AdminUpdateForm, ProductForm,
    CustomerForm, OrderForm, CategoryForm, OrderItemForm, CouponForm,
    CouponUsageForm)

from AuroraMart.models import User 
from customer_website.models import Customer
from admin_panel.models import Admin, Order, Category, Product, OrderItem, Coupon, CouponUsage

def error_check(check):
    return [msg for err_list in check for msg in err_list]


class AdminBaseView(View):
    def get_admin_context(self, request):
        return {
            'username': request.session.get('admin_username'),
            'user_role': request.session.get('admin_role'),
            'profile_picture': request.session.get('admin_profile_picture'),
        }

    def render_with_base(self, request, template_name, context=None, status=None):
        context = context.copy() if context else {}
        base = self.get_admin_context(request)
        merged = {**base, **context}
        if status is not None:
            return render(request, template_name, merged, status=status)
        return render(request, template_name, merged)


def record_selector(request, model, type):
    ids_param = request.GET.get('id') or request.POST.get('id', '')
    ids = [i.strip() for i in ids_param.split(',') if i.strip()]

    if not ids:
        return None

    queryset = model.objects.filter(pk__in=ids)

    if type == 'delete':
        result = queryset.delete()
        return result
    elif type == 'filter':
        return queryset
    return None



class loginview(AdminBaseView):
    form_class = AdminLoginForm
    template_name = 'admin_panel/login.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return self.render_with_base(request, self.template_name, {"form": form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                admin = Admin.objects.get(username=username)
                if check_password(password, admin.password):
                    request.session['admin_hasLogin'] = True
                    request.session['admin_username'] = username
                    request.session['admin_role'] = admin.role
                    request.session['admin_profile_picture'] = str(admin.profile_picture) if admin.profile_picture else None
                    return redirect('admin_dashboard')
                else:
                    error_message = "Incorrect password"
            except Admin.DoesNotExist:
                error_message = "User not found"
            except ValueError as e:
                error_message = f"Invalid data format: {str(e)}"

        return self.render_with_base(request, self.template_name, {"form": form,"error_message": error_message})

class signupview(AdminBaseView):
    form_class = AdminSignupForm
    template_name = 'admin_panel/signup.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return self.render_with_base(request, self.template_name, {"form": form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            form.save() 
            request.session['admin_username'] = form.cleaned_data['username']
            request.session['admin_role'] = form.cleaned_data['role']
            return self.render_with_base(request, 'admin_panel/login.html', {
                "form": AdminLoginForm(),
                "success_message": "Signup successful! Please log in."
            })
        else:
            return render(request, self.template_name, {
                "form": form, 
                "error_message": error_check(form.errors.values())
            })

class AdminDashboardView(AdminBaseView):
    template_name = 'admin_panel/main_dashboard.html'

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
        context['page_title'] = "Dashboard Overview"

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

    def get(self, request, *args, **kwargs):
        stats = self._get_dashboard_stats()
        return self.render_with_base(request, self.template_name, stats)


class AdminTableView(AdminBaseView):
    template_name = 'admin_panel/table_view.html'
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
            'fields': ["customer_id", "username", "age", "gender", "employment_status", "occupation","education","household_size","number_of_children","monthly_income_sgd","preferred_category"],
            'rows': lambda item: [item.customer_id, item.username, item.age, item.gender, item.employment_status, item.occupation,item.education,item.household_size,item.number_of_children,item.monthly_income_sgd,item.preferred_category]
        },
        'orders': {
            'model': Order, 'form': OrderForm, 'title': 'Orders',
            'fields': ["order_id", "customer", "status","subtotal_amount","discount_amount","total_amount","coupon_code","shipping_address","customer_email"],
            'rows': lambda item: [item.order_id, item.customer.username, item.status, item.subtotal_amount, item.discount_amount, item.total_amount, item.coupon_code or 'No coupon', item.shipping_address, item.customer_email]
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
        },
        'coupons': {
            'model': Coupon, 'form': CouponForm, 'title': 'Coupons', 
            'fields': ["coupon_id", "code", "discount_percentage", "valid_from", "valid_until", "usage_count", "usage_limit", "assigned_customers", "is_active"],
            'rows': lambda item: [
                item.coupon_id, 
                item.code, 
                item.discount_percentage, 
                item.valid_from.strftime('%Y-%m-%d') if item.valid_from else 'N/A', 
                item.valid_until.strftime('%Y-%m-%d') if item.valid_until else 'N/A', 
                item.usage_count, 
                item.usage_limit or 'Unlimited',
                ', '.join([customer.username for customer in item.assigned_customers.all()]) if item.assigned_customers.exists() else 'All customers',
                'Yes' if item.is_active else 'No'
            ]
        },
        'couponusage': {
            'model': CouponUsage, 'form': CouponUsageForm, 'title': 'Coupon Usage',
            'fields': ["coupon_usage_id", "coupon", "customer", "order", "discount_amount", "used_at"],
            'rows': lambda item: [item.coupon_usage_id, item.coupon.code, item.customer.username, item.order.order_id, f"${item.discount_amount}", item.used_at.strftime('%Y-%m-%d %H:%M') if item.used_at else 'N/A']
        }
    }


    def dispatch(self, request, *args, **kwargs):
        self.view_type = request.GET.get('type', 'products') 
        self.config = self.view_configs.get(self.view_type)
        if not self.config:
            self.view_type = 'products'
            self.config = self.view_configs[self.view_type]
        return super().dispatch(request, *args, **kwargs)

    def _get_queryset(self):
        model = self.config['model']
        action = self.request.GET.get('action')
        if action != 'Update':
            print(f"Getting queryset for view type: {self.request} with action: {action}")
            queryset = record_selector(self.request, model, 'filter')
           
        else:
            queryset = None

        if queryset is None:
            queryset = model.objects.all()

        search_query = self.request.GET.get('search', '').strip()
        search_fields = {
            'products': 'product_name',
            'customers': 'username',
            'orders': 'status',
            'categories': 'name',
            'orderitem': 'product__product_name',
            'coupons': 'code',
            'couponusage': 'coupon__code'
        }
        self.search_field_label = {
            'products': 'product name',
            'customers': 'username',
            'orders': 'status',
            'categories': 'category name',
            'orderitem': 'product name',
            'coupons': 'coupon code',
            'couponusage': 'coupon code'
        }.get(self.view_type, 'field')

        if search_query:
            search_field = search_fields.get(self.view_type)
            if search_field:
                queryset = queryset.filter(**{f'{search_field}__icontains': search_query})

        fields = self.config['fields']
        sort_by = self.request.GET.get('sort_by', fields[0] if fields else None)

        if sort_by and sort_by in fields:
            queryset = queryset.order_by(sort_by)
        return queryset

    def _get_list_view_context(self):
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

        return {
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
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'search_query': self.request.GET.get('search', ''),
            'search_field_label': getattr(self, 'search_field_label', 'field')
        }

    def _get_context_data(self, **kwargs):
        context = {
            'type': self.view_type,
            'page_title': self.config['title'],
            'username': self.request.session.get("admin_username"),
            'user_role': self.request.session.get("admin_role"),
            'profile_picture': self.request.session.get("admin_profile_picture"),
            'admin_details': self.request.GET.get('admin_details') == 'true',
            'action': self.request.GET.get('action', '')
        }
        list_context = self._get_list_view_context()
        context.update(list_context)
        context.update(kwargs)
        return context

    def _export_to_csv(self):
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{self.view_type}_{datetime.date.today()}.csv"'},
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

    def get(self, request, *args, **kwargs):
        if request.GET.get('export') == 'csv':
            return self._export_to_csv()
        
        form_to_display = None
        model = self.config['model']
        form = self.config['form']
        action = request.GET.get('action')

        if action == 'Update' and request.GET.get('id'):
            try:
                instance = model.objects.get(pk=request.GET.get('id'))
                form_to_display = form(instance=instance)
                if request.GET.get('category'):
                    category_id = request.GET.get('category')
                    try:
                        category = Category.objects.get(pk=category_id)
                        if 'category' in form_to_display.fields:
                            form_to_display.fields['category'].initial = category.pk
                        if 'subcategory' in form_to_display.fields:
                            form_to_display.fields['subcategory'].queryset = Category.objects.filter(parent_category=category)
                    except Category.DoesNotExist:
                        pass
            except model.DoesNotExist:
                pass
        elif action == 'Delete':
            try:
                record_selector(request, model, 'delete')
                target_type = request.GET.get('type') or self.view_type or 'products'
                return redirect(f"{reverse('admin_list')}?type={target_type}&success=delete")
            except Exception as e:
                context = self._get_context_data(error_message=[f"Error deleting record: {str(e)}"])
                return self.render_with_base(request, self.template_name, context)
        else:
            form_to_display = form()
            if request.GET.get('category'):
                category_id = request.GET.get('category')
                try:
                    category = Category.objects.get(pk=category_id)
                    if 'category' in form_to_display.fields:
                        form_to_display.fields['category'].initial = category.pk
                    if 'subcategory' in form_to_display.fields:
                        form_to_display.fields['subcategory'].queryset = Category.objects.filter(parent_category=category)
                except Category.DoesNotExist:
                    pass

        try:
            if self.view_type == 'couponusage' and form_to_display is not None:
                coupon_param = request.GET.get('coupon')
                customer_param = request.GET.get('customer') or request.GET.get('customer_id')

                if coupon_param and 'coupon' in form_to_display.fields:
                    try:
                        coupon_obj = Coupon.objects.get(pk=coupon_param)
                        form_to_display.fields['coupon'].initial = coupon_obj.pk
                        if 'customer' in form_to_display.fields:
                            assigned = coupon_obj.assigned_customers.all()
                            if assigned.exists():
                                form_to_display.fields['customer'].queryset = assigned
                            else:
                                form_to_display.fields['customer'].queryset = Customer.objects.all()
                    except Coupon.DoesNotExist:
                        pass

                if customer_param and 'order' in form_to_display.fields:
                    try:
                        cust = Customer.objects.get(pk=customer_param)
                        form_to_display.fields['order'].queryset = Order.objects.filter(customer=cust)
                        form_to_display.fields['order'].initial = None
                    except Customer.DoesNotExist:
                        pass
        except Exception:
            pass

        context = self._get_context_data(form=form_to_display)
        success = request.GET.get('success')
        if success:
            context['success_message'] = [f"{success.capitalize()} completed successfully."]
        context['show_modal'] = 'True' if action in ['Update', 'Add'] else 'False'
        return self.render_with_base(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        action = self.request.GET.get('action') or self.request.POST.get('action')
        model = self.config['model']
        form_instance = None
        form_class = None

        if action == 'Delete':
            try:
                result = record_selector(request, model, 'delete')
                if result is None:
                    # No IDs provided or no records found
                    context = self._get_context_data(error_message=["No records selected for deletion."])
                    return self.render_with_base(request, self.template_name, context)
                
                # Check if deletion actually occurred
                deleted_count = sum(result[0].values()) if isinstance(result, tuple) and len(result) > 0 else 0
                if deleted_count == 0:
                    context = self._get_context_data(error_message=["No records were deleted. They may not exist or may be protected."])
                    return self.render_with_base(request, self.template_name, context)
                
                target_type = request.GET.get('type') or self.view_type or 'products'
                return redirect(f"{reverse('admin_list')}?type={target_type}&success=delete")
            except Exception as e:
                # Log the full exception for debugging
                import traceback
                error_details = traceback.format_exc()
                print(f"Error deleting records: {str(e)}\n{error_details}")
                
                context = self._get_context_data(error_message=[f"Error deleting record: {str(e)}"])
                return self.render_with_base(request, self.template_name, context)

        if action == 'Update':
            form_class = self.config['form']
            try:
                instance_id = self.request.GET.get('id') or self.request.POST.get('id')
                form_instance = model.objects.get(pk=instance_id)
                old_status = form_instance.status if model == Order else None
            except model.DoesNotExist:
                context = self._get_context_data(error_message=["Item to update not found."])
                return self.render_with_base(request, self.template_name, context)
        else:
            form_class = self.config['form']

        form = form_class(request.POST, instance=form_instance)

        if form.is_valid():
            saved_instance = form.save()
            if model == Order and action == 'Update':
                new_status = getattr(saved_instance, 'status', None)
                if new_status and old_status != new_status and new_status in ('COMPLETED', 'CANCELLED'):
                    self._send_order__email(saved_instance)
            return redirect(f"{reverse('admin_list')}?type={self.view_type}&success={action.lower()}")
        else:
            context = self._get_context_data(form=form, error_message=error_check(form.errors.values()))
            return self.render_with_base(request, self.template_name, context)

    def _send_order__email(self, order):
        try:
            customer = order.customer
            order_items = order.items.all()
            items_text = ""
            for item in order_items:
                items_text += f"- {item.product.product_name} x {item.quantity} @ ${item.price_at_purchase}\n"
            subject = f"Order #{order.order_id} Completed - AuroraMart" if order.status == 'COMPLETED' else f"Order #{order.order_id} Cancelled - AuroraMart"
            
            message = f"""
Hello {customer.username},

Great news! Your order has been completed and is ready for delivery.

Order Details:
--------------
Order ID: {order.order_id}
Order Date: {order.order_date.strftime('%B %d, %Y at %I:%M %p')}
Total Amount: ${order.total_amount}

Items Ordered:
{items_text}

Shipping Address:
{order.shipping_address}

Your order will be delivered soon. Thank you for shopping with AuroraMart!

If you have any questions about your order, please don't hesitate to contact us.

Best regards,
The AuroraMart Team

---
This is an automated email. Please do not reply to this message.
            """ if order.status == 'COMPLETED' else f"""
Hello {customer.username},

We regret to inform you that your order has been cancelled.

Order Details:
--------------
Order ID: {order.order_id}
Order Date: {order.order_date.strftime('%B %d, %Y at %I:%M %p')}
Total Amount: ${order.total_amount}
Items Ordered:
{items_text}

If you have any questions regarding this cancellation, please contact our support team.
Best regards,
The AuroraMart Team
---

This is an automated email. Please do not reply to this message.
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'auroramart456@gmail.com'),
                recipient_list=[order.customer_email],
                fail_silently=True, 
            )
            
        except Exception as e:
            print(f"Failed to send order completion email: {str(e)}")

class profileSettingsView(AdminBaseView):
    template_name = 'admin_panel/profile_settings.html'
    form_class = AdminUpdateForm

    def get_common_context(self, request):
        return {
            'username': request.session.get("admin_username"),
            'user_role': request.session.get("admin_role"),
            'profile_picture': request.session.get("admin_profile_picture")
        }

    def get(self, request, *args, **kwargs):
        username = request.session.get("admin_username")
        try:
            admin = Admin.objects.get(username=username)
            form = self.form_class(instance=admin)
            context = self.get_common_context(request)
            context['form'] = form
            return self.render_with_base(request, self.template_name, context)
        except Admin.DoesNotExist:
            return self.render_with_base(request, 'admin_panel/login.html')

    def post(self, request, *args, **kwargs):
        username = request.session.get("admin_username")
        try:
            admin = Admin.objects.get(username=username)
            form = self.form_class(request.POST, instance=admin)
            context = self.get_common_context(request)
            context['form'] = form

            if form.is_valid():
                form.save()
                request.session['admin_username'] = form.cleaned_data['username']
                request.session['admin_role'] = form.cleaned_data['role']
                context['success_message'] = ["Profile updated successfully."]
                context['username'] = request.session.get("admin_username")
                context['user_role'] = request.session.get("admin_role")
                return self.render_with_base(request, self.template_name, context)
            else:
                context['error_message'] = error_check(form.errors.values())
                return self.render_with_base(request, self.template_name, context)
        except Admin.DoesNotExist:
            return self.render_with_base(request, 'admin_panel/login.html')

            
def logoutview(request):
    request.session.pop('admin_hasLogin', None)
    request.session.pop('admin_username', None)
    request.session.pop('admin_role', None)
    request.session.pop('admin_profile_picture', None)
    return redirect('admin_login')

