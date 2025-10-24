from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class User(models.Model): 
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    class Meta:
        abstract = True

class Customer(User):
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
        ('UNSPECIFIED', 'Prefer not to say'),
    ]
    EMPLOYMENT_CHOICES = [
        ('EMPLOYED', 'Employed'),
        ('UNEMPLOYED', 'Unemployed'),
        ('STUDENT', 'Student'),
        ('RETIRED', 'Retired'),
        ('SELF_EMPLOYED', 'Self-employed'),
    ]
    EDUCATION_CHOICES = [
        ('HIGH_SCHOOL', 'High School'),
        ('DIPLOMA', 'Diploma'),
        ('BACHELORS', "Bachelor's Degree"),
        ('MASTERS', "Master's Degree"),
        ('PHD', 'PhD'),
    ]
    HAS_CHILDREN_CHOICES = [
        ('YES', 'Yes'),
        ('NO', 'No'),
    ]

    customer_id = models.CharField(max_length=20, primary_key=True, unique=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=50, null=True, blank=True)
    employment_status = models.CharField(max_length=100, null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)
    education = models.CharField(max_length=100, null=True, blank=True)
    household_size = models.PositiveIntegerField(null=True, blank=True)
    has_children = models.BooleanField(default=False)
    monthly_income_sgd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_category = models.CharField(max_length=100, null=True, blank=True,default='General')

    def save(self, *args, **kwargs):
        if not self.password.startswith(('pbkdf2_sha256$', 'bcrypt$', 'argon2')):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)


class Admin(User):
    ROLE_CHOICES = [
        ('VIEWER', 'Viewer'),
        ('EDITOR', 'Editor')
    ]

    admin_id = models.CharField(max_length=20, primary_key=True, unique=True)
    role = models.CharField(max_length=100, default='Viewer',choices=ROLE_CHOICES)

    def save(self, *args, **kwargs):
        if not self.password.startswith(('pbkdf2_sha256$', 'bcrypt$', 'argon2')):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)


class Category(models.Model):
    category_id = models.CharField(max_length=20, primary_key=True, unique=True)
    name = models.CharField(max_length=255, unique=True)
    # The recursive relationship: a category can have a parent, which is also a Category.
    # 'self' creates the link to the same model.
    # related_name helps in querying for subcategories easily.
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')

    def __str__(self):
        return self.name
    
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
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')

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


class OrderItem(models.Model):
    OrderItem_id = models.CharField(max_length=20, primary_key=True, unique=True)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT) # Protect product history
    quantity = models.PositiveIntegerField(default=1)
    # Store the price at the time of purchase to maintain historical accuracy.
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

