import uuid
from django.db import models
from django.db.models import Avg
from AuroraMart.models import User
from customer_website.models import Customer
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

# Create your models here.
class Admin(User):
    ROLE_CHOICES = [
        ('VIEWER', 'Viewer'),
        ('EDITOR', 'Editor')
    ]

    admin_id = models.CharField(max_length=20, primary_key=True, unique=True)
    role = models.CharField(max_length=100, default='Viewer',choices=ROLE_CHOICES)

    def save(self, *args, **kwargs):
        if not self.admin_id:
            self.admin_id = "ADM-" + str(uuid.uuid4())
        if not self.password.startswith(('pbkdf2_sha256$', 'bcrypt$', 'argon2')):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

class Category(models.Model):
    category_id = models.CharField(max_length=20, primary_key=True, unique=True)
    name = models.CharField(max_length=255, unique=True)
    parent_category = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategories',
    )

    def __str__(self):
        if self.parent_category:
            return f"{self.parent_category.name} > {self.name}"
        return self.name
    
    def save(self,*args, **kwargs):
        if not self.category_id:
            self.category_id = "CAT-" + str(uuid.uuid4())
        return super().save(*args, **kwargs)
    
    def is_main_category(self):
        """Returns True if this is a main category (no parent)"""
        return self.parent_category is None
    
    def is_subcategory(self):
        """Returns True if this is a subcategory (has parent)"""
        return self.parent_category is not None
    
    def get_main_category(self):
        """Returns the main category (root) for this category"""
        if self.parent_category:
            return self.parent_category.get_main_category()
        return self
    
    class Meta:
        # Ensures plural form is "Categories" in the admin panel
        verbose_name_plural = "Categories"

class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True,primary_key=True)
    product_name = models.CharField(max_length=255)
    description = models.TextField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_rating = models.FloatField(default=0.0)
    quantity_on_hand = models.PositiveIntegerField(default=0)
    reorder_quantity = models.PositiveIntegerField(default=10)
    product_image = models.URLField(
        max_length=500,
        default='https://cdn.mmem.com.au/media/catalog/product/placeholder/default/product-image.jpg',
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=False, 
        related_name='products',
    )
    subcategory = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name='subcategory_products',
    )

    def __str__(self):
        return self.product_name

class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    review_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey('customer_website.Customer', on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    review_title = models.CharField(max_length=255)
    review_content = models.TextField()
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        default=5
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'

    def __str__(self):
        return f"{self.review_title} - {self.product.product_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_product_rating()

    def update_product_rating(self):
        avg_rating = self.product.reviews.aggregate(Avg('rating'))['rating__avg']
        if avg_rating:
            self.product.product_rating = round(avg_rating, 1)
            self.product.save(update_fields=['product_rating'])


class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    order_id = models.CharField(max_length=20, primary_key=True, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    customer_email = models.EmailField(max_length=254,default= 'test@email.com' )
    order_date = models.DateTimeField(auto_now_add=True)
    shipping_address = models.TextField(max_length=500,null=False, blank=False,default='')
    order_notes = models.TextField(max_length=1000, null=True, blank=True)
    
    # Original total before any discounts
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Discount applied
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Final total after discount
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Coupon information
    coupon = models.ForeignKey(
        'Coupon', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='orders'
    )
    coupon_code = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        help_text="Coupon code used (for display purposes)"
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def save(self,*args, **kwargs):
        if not self.order_id:
            self.order_id = "ORD-" + str(uuid.uuid4())
        super().save(*args, **kwargs)
    
    def apply_coupon(self, coupon_code):   
        try:
            coupon = Coupon.objects.get(code=coupon_code.upper())
        except Coupon.DoesNotExist:
            return False, "Invalid coupon code"
        
        if not coupon.is_valid():
            return False, "Coupon is not valid"
        
        if not coupon.can_be_used_by(self.customer):
            return False, "You are not eligible to use this coupon"
        
        # Check if customer already used this coupon (if one-time use per customer)
        if CouponUsage.objects.filter(coupon=coupon, customer=self.customer).exists():
            return False, "You have already used this coupon"
        
        # Calculate discount
        discount = coupon.calculate_discount(self.subtotal_amount)
        if discount <= 0:
            return False, "Coupon does not apply to this order"
        
        # Apply discount
        self.coupon = coupon
        self.coupon_code = coupon.code
        self.discount_amount = discount
        self.total_amount = self.subtotal_amount - discount
        
        self.save()
        return True, f"Coupon applied! You saved ${discount:.2f}"
    
    def remove_coupon(self):
        """Remove coupon from order"""
        if self.coupon:
            self.coupon = None
            self.coupon_code = None
            self.discount_amount = 0.00
            self.total_amount = self.subtotal_amount
            self.save()
            return True, "Coupon removed"
        return False, "No coupon applied"
    
    def calculate_subtotal(self):
        """Calculate subtotal from order items"""
        return sum(item.quantity * item.price_at_purchase for item in self.items.all())
    
    def update_totals(self):
        """Update subtotal and total amounts"""
        self.subtotal_amount = self.calculate_subtotal()
        if self.coupon:
            self.discount_amount = self.coupon.calculate_discount(self.subtotal_amount)
            self.total_amount = self.subtotal_amount - self.discount_amount
        else:
            self.discount_amount = 0.00
            self.total_amount = self.subtotal_amount
        self.save()
    
    def __str__(self):
        return self.order_id


class OrderItem(models.Model):
    OrderItem_id = models.CharField(max_length=20, primary_key=True, unique=True)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE) # Protect product history
    quantity = models.PositiveIntegerField(default=1)
    # Store the price at the time of purchase to maintain historical accuracy.
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self,*args, **kwargs):
        if not self.OrderItem_id:
            self.OrderItem_id = "ORDITEM-" + str(uuid.uuid4())
        return super().save(*args, **kwargs)

class Coupon(models.Model):
    coupon_id = models.CharField(max_length=20, primary_key=True, unique=True)
    code = models.CharField(max_length=50, unique=True, help_text="Unique coupon code")
    description = models.TextField(blank=True, help_text="Description of the coupon")
    
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount percentage (0-100%)",
        default=0.00
    )
    
    minimum_order_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Minimum order value to apply coupon"
    )
    maximum_discount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Maximum discount amount for percentage coupons"
    )
    
    valid_from = models.DateField(help_text="Coupon valid from date (midnight)")
    valid_until = models.DateField(help_text="Coupon valid until date (midnight)")
    
    usage_limit = models.PositiveIntegerField(
        default=0, 
        help_text="Total number of times coupon can be used (0 = unlimited)"
    )
    usage_count = models.PositiveIntegerField(default=0, help_text="Current usage count")
    
    is_active = models.BooleanField(default=True)
    
    applicable_categories = models.ManyToManyField(
        Category, 
        blank=True, 
        related_name='coupons',
        help_text="Main categories this coupon applies to (leave empty for all)",
        limit_choices_to={'parent_category__isnull': True}
    )
    
    assigned_customers = models.ManyToManyField(
        'customer_website.Customer',
        blank=True,
        related_name='assigned_coupons',
        help_text="Specific customers this coupon is assigned to (leave empty for all customers)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.discount_percentage}%"

    def save(self, *args, **kwargs):
        if not self.coupon_id:
            self.coupon_id = "COUP-" + str(uuid.uuid4())
        super().save(*args, **kwargs)

    def is_valid(self):
        from django.utils import timezone
        now = timezone.now().date() 
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.usage_limit == 0 or self.usage_count < self.usage_limit)
        )

    def can_be_used_by(self, customer):
        if self.assigned_customers.exists():
            return self.assigned_customers.filter(customer_id=customer.customer_id).exists()
        return True

    def calculate_discount(self, order_total, applicable_items=None):
        """Calculate discount amount for given order total"""
        if not self.is_valid():
            return 0.00
        
        if order_total < self.minimum_order_value:
            return 0.00
        
        # Calculate percentage discount
        discount = (order_total * self.discount_percentage) / 100
        if self.maximum_discount and discount > self.maximum_discount:
            discount = self.maximum_discount
        
        return min(discount, order_total)  # Don't exceed order total


class CouponUsage(models.Model):
    coupon_usage_id = models.CharField(max_length=20, primary_key=True, unique=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='coupon_usages')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='coupon_usages')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.coupon.code} used by {self.customer.username}"

    def save(self, *args, **kwargs):
        if not self.coupon_usage_id:
            self.coupon_usage_id = "COUPUSE-" + str(uuid.uuid4())
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['coupon', 'customer', 'order'] 

