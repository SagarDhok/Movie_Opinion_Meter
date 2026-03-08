from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from .managers import UserManager



class User(AbstractUser):
    username = None  # Removes the username field completely
    email = models.EmailField(unique=True)
    
    # AbstractUser already provides: first_name, last_name, is_active, is_staff, and date_joined
    # So we only need to add our custom project fields:
    is_email_verified = models.BooleanField(default=False)
    profile_image = models.URLField(blank=True, null=True)

    USERNAME_FIELD = 'email'  
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()  

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
