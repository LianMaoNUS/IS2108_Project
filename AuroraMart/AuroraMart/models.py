from django.db import models
from django.contrib.auth.hashers import make_password, check_password

#image
class User(models.Model): 
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    profile_picture = models.URLField(
        max_length=500, 
        default='https://www.pngmart.com/files/21/Admin-Profile-Vector-PNG-Clipart.png',
        help_text='Profile picture URL'
    )

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    class Meta:
        abstract = True

