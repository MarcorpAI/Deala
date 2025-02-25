from django.db import models
# from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import json
from datetime import datetime, timedelta

from delapp.models import CustomUser

class StoredProduct(models.Model):
    """Model for storing products from various retailers"""
    product_id = models.CharField(max_length=255)
    title = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    url = models.URLField(max_length=1000)
    image_url = models.URLField(max_length=1000)
    retailer = models.CharField(max_length=50)
    description = models.TextField()
    available = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Additional fields for enhanced functionality
    rating = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    review_count = models.IntegerField(null=True, blank=True)
    condition = models.CharField(max_length=50, null=True, blank=True)
    shipping_info = models.TextField(null=True, blank=True)
    discount = models.CharField(max_length=50, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)  # For flexible additional data storage
    
    class Meta:
        indexes = [
            models.Index(fields=['product_id', 'retailer']),
            models.Index(fields=['timestamp']),
        ]
        unique_together = ['product_id', 'retailer']
    
    @property
    def is_stale(self):
        """Check if the product data is older than 24 hours"""
        return datetime.now() - self.last_updated.replace(tzinfo=None) > timedelta(hours=24)

class PriceHistory(models.Model):
    """Model for tracking price changes"""
    product = models.ForeignKey(StoredProduct, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['product', 'timestamp']),
        ]

class ProductAvailabilityLog(models.Model):
    """Model for tracking product availability changes"""
    product = models.ForeignKey(StoredProduct, on_delete=models.CASCADE, related_name='availability_logs')
    available = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)