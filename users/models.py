from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from .managers import UserManager
import uuid

def user_profile_upload_path(instance, filename):
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"

    email_part = instance.email.split("@")[0].replace(".", "_")
    return f"profiles/{email_part}/{filename}"

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    profile_image = models.FileField(
    upload_to=user_profile_upload_path,
    blank=True,
    null=True
)
 


    USERNAME_FIELD = 'email'  #bydefault django username
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()   #py manage.py createsuperuser means User.objects.create_superuser(...) internally




    def __str__(self):
        return f"{self.first_name} {self.last_name}"
