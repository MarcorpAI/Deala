from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.utils import timezone
from .managers import CustomUserManager
# Create your models here.









# class CustomUser(AbstractBaseUser, PermissionsMixin):
#     email = models.EmailField(unique=True)
#     first_name = models.CharField(max_length=40, blank=True)
#     last_name = models.CharField(max_length=30, blank=True)
#     is_active = models.BooleanField(default=True)
#     is_staff = models.BooleanField(default=False)
#     lemonsqueezy_customer_id = models.CharField(max_length=255, blank=True, null=True)

#     objects = CustomUserManager()

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = []

#     def __str__(self):
#         return self.email
        

#     def get_short_name(self):
#         return self.first_name or self.email




class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=40, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=False)  # Changed to False
    is_staff = models.BooleanField(default=False)
    lemonsqueezy_customer_id = models.CharField(max_length=255, blank=True, null=True)
    email_verified = models.BooleanField(default=False)  # New field
    verification_token = models.CharField(max_length=100, blank=True, null=True)  # New field

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def get_short_name(self):
        return self.first_name or self.email

    def generate_verification_token(self):
        self.verification_token = get_random_string(64)
        self.save()

    def verify_email(self):
        self.email_verified = True
        self.is_active = True
        self.verification_token = None
        self.save()

















class UserQuery(models.Model):
    query  = models.TextField(max_length=1000)
    date_created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="query")



    



class UserSubscription(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    lemonsqueezy_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    variant_id = models.CharField(max_length=255)
    verification_token = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.email}'s Subscription"
