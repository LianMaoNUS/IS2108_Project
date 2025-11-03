import uuid
from django.db import models
from django.utils import timezone
from AuroraMart.models import User
from django.contrib.auth.hashers import make_password, check_password

# Create your models here.
class Customer(User):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
        ('Unspecified', 'Prefer not to say'),
    ]
    EMPLOYMENT_CHOICES = [
        ('Employed', 'Employed'),
        ('Unemployed', 'Unemployed'),
        ('Student', 'Student'),
        ('Retired', 'Retired'),
        ('Self-employed', 'Self-employed'),
    ]
    EDUCATION_CHOICES = [
        ('High School', 'High School'),
        ('Diploma', 'Diploma'),
        ('Bachelor', "Bachelor's Degree"),
        ('Master', "Master's Degree"),
        ('PhD', 'PhD'),
    ]
    HAS_CHILDREN_CHOICES = [
        (True, 'Yes'),
        (False, 'No'),
    ]
    OCCUPATION_CHOICES = [
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Freelancer', 'Freelancer'),
        ('Unemployed', 'Unemployed'),
        ('Student', 'Student'),
        ('Retired', 'Retired'),
    ]

    customer_id = models.CharField(max_length=20, primary_key=True, unique=True,editable=False)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=50, null=True, blank=True)
    employment_status = models.CharField(max_length=100, null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)
    education = models.CharField(max_length=100, null=True, blank=True)
    household_size = models.PositiveIntegerField(null=True, blank=True)
    has_children = models.BooleanField(default=False)
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
