import uuid
from django.db import models
from django.utils import timezone
from AuroraMart.models import User
from django.contrib.auth.hashers import make_password

class Customer(User):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    EMPLOYMENT_CHOICES = [
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Self-employed', 'Self-employed'),
        ('Student', 'Student'),
        ('Retired', 'Retired'),
    ]
    EDUCATION_CHOICES = [
        ('Secondary', 'Secondary'),
        ('Diploma', 'Diploma'),
        ('Bachelor', 'Bachelor'),
        ('Master', 'Master'),
        ('Doctorate', 'Doctorate'),
    ]
    OCCUPATION_CHOICES = [
        ('Admin', 'Administrative'),
        ('Education', 'Education'),
        ('Sales', 'Sales'),
        ('Service', 'Service Industry'),
        ('Skilled Trades', 'Skilled Trades'),
        ('Tech', 'Technology'),
    ]

    customer_id = models.CharField(max_length=20, primary_key=True, unique=True,editable=False)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=50, choices=GENDER_CHOICES, null=True, blank=True)
    employment_status = models.CharField(max_length=100, choices=EMPLOYMENT_CHOICES, null=True, blank=True)
    occupation = models.CharField(max_length=100, choices=OCCUPATION_CHOICES, null=True, blank=True)
    education = models.CharField(max_length=100, choices=EDUCATION_CHOICES, null=True, blank=True)
    household_size = models.PositiveIntegerField(null=True, blank=True)
    number_of_children = models.PositiveIntegerField(default=0, null=True, blank=True)
    monthly_income_sgd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_category = models.CharField(max_length=100, null=True, blank=True,default='General')
    date_joined = models.DateTimeField(default=timezone.now, editable=False)

    def save(self, *args, **kwargs):
        if not self.customer_id:
            self.customer_id = "CUST-" + str(uuid.uuid4())
        if not self.password.startswith(('pbkdf2_sha256$', 'bcrypt$', 'argon2')):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Wishlist(models.Model):
    wishlist_id = models.CharField(max_length=20, primary_key=True, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='wishlists')
    product = models.ForeignKey('admin_panel.Product', on_delete=models.CASCADE, related_name='wishlisted_by')
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['customer', 'product']
        ordering = ['-added_date']

    def save(self, *args, **kwargs):
        if not self.wishlist_id:
            self.wishlist_id = "WISH-" + str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer.username} - {self.product.product_name}"
