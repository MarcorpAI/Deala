from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.utils import timezone
from .managers import CustomUserManager
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class ProductDeal:
    product_id: str
    title: str
    price: float
    url: str
    image_url: str
    retailer: str
    description: str
    available: bool
    timestamp: datetime
    # Optional fields must come after required fields
    original_price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    condition: Optional[str] = None
    shipping_info: Optional[str] = None
    discount: Optional[str] = None
    coupon: Optional[str] = None
    trending: Optional[bool] = None
    sold_count: Optional[int] = None
    watchers: Optional[int] = None
    return_policy: Optional[str] = None
    location: Optional[str] = None
    product_star_rating: Optional[float] = None

@dataclass
class UserPreference:
    """Store user preferences for deal searching"""
    preferred_condition: Optional[str] = None  # New, Used, Refurbished
    max_price: Optional[float] = None
    min_rating: Optional[float] = None
    favorite_categories: List[str] = None


 


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=40, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=False)  # Changed to False
    is_staff = models.BooleanField(default=False)
    lemonsqueezy_customer_id = models.CharField(max_length=255, blank=True, null=True)
    email_verified = models.BooleanField(default=False)  # New field
    verification_token = models.CharField(max_length=100, blank=True, null=True)  # New field
    verification_token_created = models.DateTimeField(null=True, blank=True)

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
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="query", null=True, blank=True)



    



class Conversation(models.Model):
    """Model to represent a shopping conversation session"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="conversations", null=True, blank=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Conversation {self.id} - {self.title or 'Untitled'}"
    
    class Meta:
        ordering = ['-updated_at']






class ConversationMessage(models.Model):
    """Model to store individual messages in a conversation"""
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
    )
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Store search results for assistant messages
    search_results = models.JSONField(null=True, blank=True)
    
    # If this message contains product recommendations
    has_products = models.BooleanField(default=False)
    
    # Store query understanding for the assistant's response
    query_understanding = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
    
    class Meta:
        ordering = ['created_at']
    

class ConversationState(models.Model):
    """Store conversation state for continuity between requests"""
    conversation = models.OneToOneField(Conversation, on_delete=models.CASCADE, related_name="state")
    current_products = models.JSONField(default=list)
    last_query = models.TextField(blank=True)
    last_category = models.CharField(max_length=100, blank=True)
    applied_filters = models.JSONField(default=dict)
    last_intent = models.CharField(max_length=50, blank=True, null=True)
    conversation_turn = models.IntegerField(default=0)
    product_references = models.JSONField(default=dict)
    user_preferences = models.JSONField(default=dict)
    keywords = models.JSONField(default=list)
    last_action = models.CharField(max_length=50, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"State for conversation {self.conversation.id}"
    
    class Meta:
        ordering = ['-updated_at']






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





class UserDevice(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255, unique=True)
    refresh_token = models.CharField(max_length=500, blank=True, null=True)
    last_login = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.device_id}"