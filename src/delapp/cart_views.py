from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from django.utils import timezone
import logging
import json
import asyncio

from .models import Cart, SavedItem, Conversation
# Import the agent-based cart operations
from .agent.api import add_to_cart, view_cart, remove_from_cart

logger = logging.getLogger(__name__)

class CartViewSet(viewsets.ViewSet):
    """
    ViewSet for cart operations - view, add, and remove items
    """
    permission_classes = [AllowAny]  # Allow anonymous users
    
    def get_cart(self, request):
        """Get or create a cart for the current user or session"""
        user = request.user if request.user.is_authenticated else None
        session_id = request.session.session_key or request.COOKIES.get('sessionid') or request.data.get('session_id')
        
        # Create session ID if needed
        if not session_id:
            if not request.session.exists(request.session.session_key):
                request.session.create()
            session_id = request.session.session_key
        
        # Get or create cart
        if user and user.id:
            cart, created = Cart.objects.get_or_create(
                user=user,
                defaults={'session_id': session_id, 'updated_at': timezone.now()}
            )
        else:
            # For anonymous users, we need the session ID
            cart, created = Cart.objects.get_or_create(
                session_id=session_id,
                defaults={'updated_at': timezone.now()}
            )
        
        return cart
    
    @action(detail=False, methods=['get'])
    def view(self, request):
        """View cart contents (using agent-based implementation)"""
        try:
            # Get cart for compatibility
            cart = self.get_cart(request)
            
            # Get user ID or session ID
            user_id = str(request.user.id) if request.user.is_authenticated else None
            session_id = cart.session_id
            
            # Call agent-based implementation
            result = asyncio.run(view_cart(
                user_id=user_id,
                session_id=session_id
            ))
            
            # Map agent response to legacy format for compatibility
            if result.get('success', False):
                items_data = result.get('cart_items', [])
                # Format each item for the legacy response structure
                for item in items_data:
                    # Make sure each item has required fields
                    if 'id' not in item and 'item_id' in item:
                        item['id'] = item['item_id']
                    if 'created_at' not in item:
                        item['created_at'] = timezone.now().isoformat()
                    if 'updated_at' not in item:
                        item['updated_at'] = timezone.now().isoformat()
                
                # Return the response in the legacy format
                return Response({
                    'cart_id': cart.id,
                    'items': items_data,
                    'item_count': len(items_data),
                    'total_price': result.get('total_price', 0),
                    'session_id': session_id
                })
            else:
                # Handle error case
                return Response({
                    'error': result.get('error', 'Failed to retrieve cart'),
                    'cart_id': cart.id,
                    'items': [],
                    'item_count': 0,
                    'total_price': 0,
                    'session_id': session_id
                }, status=status.HTTP_200_OK)  # Still return 200 to avoid frontend issues
            
        except Exception as e:
            logger.error(f"Error viewing cart: {str(e)}", exc_info=True)
            return Response({'error': 'Failed to retrieve cart'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add item to cart (using agent-based implementation)"""
        try:
            product_data = request.data
            cart = self.get_cart(request)  # For compatibility
            
            # Get user ID or session ID
            user_id = str(request.user.id) if request.user.is_authenticated else None
            session_id = cart.session_id
            conversation_id = request.data.get('conversation_id')
            
            # Normalize product data for agent
            normalized_product = {}
            # Copy all fields from request data
            for key, value in product_data.items():
                normalized_product[key] = value
            
            # Ensure required fields are present with standard names
            if 'product_id' not in normalized_product and 'id' in product_data:
                normalized_product['product_id'] = product_data['id']
            
            if 'title' not in normalized_product and 'name' in product_data:
                normalized_product['title'] = product_data['name']
                
            if 'price' not in normalized_product and 'currentPrice' in product_data:
                normalized_product['price'] = product_data['currentPrice']
                
            # Call agent-based implementation
            result = asyncio.run(add_to_cart(
                product_data=normalized_product,
                user_id=user_id,
                session_id=session_id,
                conversation_id=conversation_id
            ))
            
            # Map agent response to legacy format
            if result.get('success', False):
                # Successfully added
                return Response({
                    'message': result.get('message', f"Added item to your cart"),
                    'item_id': result.get('item_id', None),
                    'is_new': result.get('is_new', True),
                    'item_count': result.get('cart_count', 1)
                })
            else:
                # Item already exists or other issue
                return Response({
                    'message': result.get('message', "Item could not be added to cart"),
                    'error': result.get('error', None),
                    'is_new': False,
                    'item_count': result.get('cart_count', 0)
                }, status=status.HTTP_200_OK)  # Still return 200 to avoid frontend issues
            
        except Exception as e:
            logger.error(f"Error adding item to cart: {str(e)}", exc_info=True)
            return Response({'error': 'Failed to add item to cart'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """Remove item from cart (using agent-based implementation)"""
        try:
            cart = self.get_cart(request)  # For compatibility
            item_id = request.data.get('item_id')
            remove_all = request.data.get('remove_all', False)
            
            # Get user ID or session ID
            user_id = str(request.user.id) if request.user.is_authenticated else None
            session_id = cart.session_id
            
            # Prepare indices to remove
            product_indices = []
            
            if remove_all:
                # Remove all items - agent will handle this with empty indices
                pass
            elif item_id:
                # Add the item ID to the list
                product_indices.append(item_id)
            else:
                return Response({'error': 'Item ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Call agent-based implementation
            result = asyncio.run(remove_from_cart(
                product_indices=product_indices,
                user_id=user_id,
                session_id=session_id
            ))
            
            # Map agent response to legacy format
            if result.get('success', False):
                # Successfully removed
                return Response({
                    'message': result.get('message', "Removed item(s) from your cart"),
                    'remaining_items': result.get('cart_count', 0),
                    'item_count': result.get('cart_count', 0)
                })
            else:
                # Error case
                return Response({
                    'message': result.get('message', "Could not remove item from cart"),
                    'error': result.get('error', None),
                    'item_count': result.get('cart_count', 0)
                }, status=status.HTTP_200_OK)  # Still return 200 to avoid frontend issues
                
        except Exception as e:
            logger.error(f"Error removing item from cart: {str(e)}", exc_info=True)
            return Response({'error': 'Failed to remove item from cart'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
