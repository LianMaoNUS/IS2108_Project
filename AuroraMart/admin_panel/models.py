import uuid
from django.db import models
from AuroraMart.models import User
from customer_website.models import Customer
from django.contrib.auth.hashers import make_password, check_password

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
<<<<<<< HEAD
    parent_category = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategories',
        help_text='Leave blank for main categories, select a parent for subcategories'
    )

    def __str__(self):
        if self.parent_category:
            return f"{self.parent_category.name} > {self.name}"
=======
    is_subcategory = models.BooleanField(default=False)

    def __str__(self):
>>>>>>> 22aa262936ccb0cc0fa0b2c51c017d722aef8917
        return self.name
    
    def save(self,*args, **kwargs):
        if not self.category_id:
<<<<<<< HEAD
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
    
=======
            print("hhhh")
            self.category_id = "CAT-" + str(uuid.uuid4())
        return super().save(*args, **kwargs)
    
>>>>>>> 22aa262936ccb0cc0fa0b2c51c017d722aef8917
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
        help_text='Product image URL'
    )   
<<<<<<< HEAD
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='products',
        help_text='Can be assigned to either main category or subcategory'
    )
    subcategory = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategory_products',
        help_text='Select a subcategory if applicable'
    )
=======
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    subcategory = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_products')
>>>>>>> 22aa262936ccb0cc0fa0b2c51c017d722aef8917

    def __str__(self):
        return self.product_name

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    order_id = models.CharField(max_length=20, primary_key=True, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def save(self,*args, **kwargs):
        if not self.order_id:
            self.order_id = "ORD-" + str(uuid.uuid4())
        return super().save(*args, **kwargs)
    
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

