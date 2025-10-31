from django.db import models
from django.contrib.auth.hashers import make_password, check_password

#image
class User(models.Model): 
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    class Meta:
        abstract = True

