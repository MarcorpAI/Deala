# carts/services.py

from typing import Optional, List, Dict
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from products.models import StoredProduct
from .models import Cart, CartItem, PriceAlert

class CartService:
    """Service for managing shopping cart operations"""
    
    @staticmethod
    def get_or_create_active_cart(user) -> Cart:
        """Get user's active cart or create a new one"""
        cart, created = Cart.objects.get_or_create(
            user=user,
            status='active',
            defaults={'user': user}
        )
        return cart

    @staticmethod
    def add_to_cart(user, product_id: str, retailer: str, quantity: int = 1) -> CartItem:
        """Add a product to the user's cart"""
        with transaction.atomic():
            # Get product and validate
            try:
                product = StoredProduct.objects.get(product_id=product_id, retailer=retailer)
            except StoredProduct.DoesNotExist:
                raise ValidationError("Product not found")

            if not product.available:
                raise ValidationError("Product is not available")

            # Get or create active cart
            cart = CartService.get_or_create_active_cart(user)

            # Add item to cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={
                    'quantity': quantity,
                    'price_at_addition': product.price
                }
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            return cart_item

    @staticmethod
    def remove_from_cart(user, product_id: str, retailer: str) -> None:
        """Remove a product from the user's cart"""
        cart = CartService.get_or_create_active_cart(user)
        CartItem.objects.filter(
            cart=cart,
            product__product_id=product_id,
            product__retailer=retailer
        ).delete()

    @staticmethod
    def update_quantity(user, product_id: str, retailer: str, quantity: int) -> CartItem:
        """Update quantity of a cart item"""
        cart = CartService.get_or_create_active_cart(user)
        cart_item = CartItem.objects.get(
            cart=cart,
            product__product_id=product_id,
            product__retailer=retailer
        )
        cart_item.quantity = quantity
        cart_item.save()
        return cart_item

    @staticmethod
    def save_for_later(user, product_id: str, retailer: str) -> CartItem:
        """Move item to saved for later"""
        cart = CartService.get_or_create_active_cart(user)
        cart_item = CartItem.objects.get(
            cart=cart,
            product__product_id=product_id,
            product__retailer=retailer
        )
        cart_item.move_to_saved_for_later()
        return cart_item

    @staticmethod
    def move_to_cart(user, product_id: str, retailer: str) -> CartItem:
        """Move item from saved for later to active cart"""
        cart = CartService.get_or_create_active_cart(user)
        cart_item = CartItem.objects.get(
            cart=cart,
            product__product_id=product_id,
            product__retailer=retailer
        )
        cart_item.move_to_cart()
        return cart_item

    @staticmethod
    def set_price_alert(user, product_id: str, retailer: str, target_price: Decimal) -> PriceAlert:
        """Set a price alert for a product"""
        product = StoredProduct.objects.get(product_id=product_id, retailer=retailer)
        alert, created = PriceAlert.objects.get_or_create(
            user=user,
            product=product,
            defaults={'target_price': target_price}
        )
        if not created:
            alert.target_price = target_price
            alert.is_active = True
            alert.save()
        return alert

    @staticmethod
    def get_cart_summary(user) -> Dict:
        """Get summary of user's cart"""
        cart = CartService.get_or_create_active_cart(user)
        items_by_retailer = cart.get_items_by_retailer()
        
        return {
            'total_items': cart.total_items,
            'total_amount': cart.total_amount,
            'items_by_retailer': {
                retailer: {
                    'items': [
                        {
                            'id': item.id,
                            'product': item.product.title,
                            'quantity': item.quantity,
                            'price': item.price_at_addition,
                            'subtotal': item.subtotal,
                            'price_changed': item.price_changed,
                            'saved_for_later': item.saved_for_later
                        } for item in items
                    ],
                    'subtotal': sum(item.subtotal for item in items)
                } for retailer, items in items_by_retailer.items()
            }
        }

    @staticmethod
    def check_cart_changes(user) -> List[Dict]:
        """Check for price or availability changes in cart items"""
        cart = CartService.get_or_create_active_cart(user)
        changes = []
        
        for item in cart.items.all():
            if item.price_changed:
                changes.append({
                    'type': 'price_change',
                    'product': item.product.title,
                    'old_price': item.price_at_addition,
                    'new_price': item.product.price
                })
            
            if not item.product.available:
                changes.append({
                    'type': 'availability',
                    'product': item.product.title,
                    'status': 'unavailable'
                })
                
        return changes