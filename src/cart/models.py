# carts/models.py

from django.db import models
from delapp.models import CustomUser

from products.models import StoredProduct
from decimal import Decimal

class Cart(models.Model):
    """Shopping cart model"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('saved', 'Saved for Later'),
            ('abandoned', 'Abandoned'),
            ('converted', 'Converted to Order')
        ],
        default='active'
    )

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    @property
    def total_items(self):
        return self.items.count()

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())

    def get_items_by_retailer(self):
        """Group cart items by retailer"""
        items_by_retailer = {}
        for item in self.items.all():
            retailer = item.product.retailer
            if retailer not in items_by_retailer:
                items_by_retailer[retailer] = []
            items_by_retailer[retailer].append(item)
        return items_by_retailer

class CartItem(models.Model):
    """Individual item in a shopping cart"""
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(StoredProduct, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    saved_for_later = models.BooleanField(default=False)
    price_at_addition = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        indexes = [
            models.Index(fields=['cart', 'saved_for_later']),
            models.Index(fields=['product', 'cart']),
        ]
        unique_together = ['cart', 'product']  # Prevent duplicate products in cart

    @property
    def subtotal(self):
        return Decimal(str(self.quantity)) * self.price_at_addition

    @property
    def price_changed(self):
        """Check if product price has changed since addition to cart"""
        return self.price_at_addition != self.product.price

    def move_to_saved_for_later(self):
        """Move item to saved for later section"""
        self.saved_for_later = True
        self.save()

    def move_to_cart(self):
        """Move item back to active cart"""
        self.saved_for_later = False
        self.save()

class PriceAlert(models.Model):
    """Price alerts for cart items"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(StoredProduct, on_delete=models.CASCADE)
    target_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['product', 'target_price']),
        ]
        unique_together = ['user', 'product']  # One alert per product per user