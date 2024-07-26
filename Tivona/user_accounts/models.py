from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from .manager import UserManager

class CustomUser(AbstractUser):
    phone = models.CharField(max_length=12, unique=True, null=False)
    email = models.EmailField(unique=True)
    address = models.TextField(default=False)
    date_joined = models.DateField(default=timezone.now, null=True, blank=True)
    email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.username

    
class Address(models.Model):
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
    name=models.CharField(max_length=25,default=False)
    phone=models.CharField(max_length=12,default=False)
    address=models.CharField(max_length=50,default=False)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    primary_address=models.BooleanField(default=False)
    is_listed=models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name},{self.phone},{self.address},{self.street},{self.city},{self.state},{self.pin_code},{self.country}"