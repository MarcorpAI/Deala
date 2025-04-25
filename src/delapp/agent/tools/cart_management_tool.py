"""
Cart Management Tool for ShopAgent

This tool handles cart operations like adding products, viewing cart contents,
and removing items from the cart.
"""
from typing import Dict, Any, Optional, List, Union
import logging
from asgiref.sync import sync_to_async
from django.utils import timezone
import uuid

from .base_tool import BaseTool
from ...models import Cart, SavedItem, Conversation

logger = logging.getLogger(__name__)

class CartManagementTool(BaseTool):
    """Tool for managing shopping cart operations"""
    
    def __init__(self):
        """Initialize the cart management tool"""
        super().__init__(
            name="cart_management",
            description="Manage shopping cart operations including add, view, and remove"
        )
    
    async def execute(self,
                     action: str,
                     user_id: Optional[str] = None,
                     session_id: Optional[str] = None,
                     product_data: Optional[Dict[str, Any]] = None,
                     product_indices: Optional[List[int]] = None,
                     conversation_id: Optional[str] = None,
                     **kwargs) -> Dict[str, Any]:
        """
        Execute a cart management operation.
        
        Args:
            action: The cart operation to perform ('add', 'view', 'remove', 'clear')
            user_id: ID of the user (optional)
            session_id: Session ID for anonymous users (optional)
            product_data: Product data to add to cart (required for 'add' action)
            product_indices: Indices of products to remove (required for 'remove' action)
            conversation_id: ID of the conversation (optional)
            **kwargs: Additional parameters
            
        Returns:
            Dict containing operation results
        """
        try:
            logger.info(f"Executing cart {action} operation for {'user' if user_id else 'session'} "
                        f"{user_id or session_id}")
            
            # Make sure either user_id or session_id is provided
            if not user_id and not session_id:
                # Generate a new session ID if neither is provided
                session_id = str(uuid.uuid4())
                logger.info(f"Generated new session ID: {session_id}")
            
            # Handle the requested action
            if action.lower() == 'add':
                return await self._add_to_cart(user_id, session_id, product_data, conversation_id)
            elif action.lower() == 'view':
                return await self._view_cart(user_id, session_id)
            elif action.lower() == 'remove':
                return await self._remove_from_cart(user_id, session_id, product_indices)
            elif action.lower() == 'clear':
                return await self._clear_cart(user_id, session_id)
            else:
                return {
                    "success": False,
                    "error": f"Unknown cart action: {action}",
                    "cart_items": []
                }
        
        except Exception as e:
            logger.error(f"Error in cart management: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "cart_items": [],
                "cart_count": 0
            }
    
    async def _add_to_cart(self, user_id: Optional[str], session_id: Optional[str], 
                         product_data: Dict[str, Any], conversation_id: Optional[str]) -> Dict[str, Any]:
        """Add a product to the cart"""
        try:
            if not product_data:
                return {
                    "success": False,
                    "error": "No product data provided",
                    "cart_items": []
                }
            
            # Get or create cart
            cart, new_session_id = await self._get_or_create_cart(user_id, session_id)
            
            # Add product to cart
            saved_item = await self._create_saved_item(cart, product_data, conversation_id)
            
            # Get updated cart item count
            item_count = await self._get_cart_item_count(cart)
            
            return {
                "success": True,
                "message": f"Added {product_data.get('title', 'product')} to your cart",
                "cart_items": [self._format_saved_item(saved_item)],
                "cart_count": item_count,
                "session_id": new_session_id
            }
        except Exception as e:
            logger.error(f"Error adding to cart: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "cart_items": []
            }
    
    async def _view_cart(self, user_id: Optional[str], session_id: Optional[str]) -> Dict[str, Any]:
        """View cart contents"""
        try:
            # Try to get cart
            cart = await self._find_cart(user_id, session_id)
            
            if not cart:
                return {
                    "success": True,
                    "message": "Your cart is empty",
                    "cart_items": [],
                    "cart_count": 0
                }
            
            # Get cart items
            items = await self._get_cart_items(cart)
            
            if not items:
                return {
                    "success": True,
                    "message": "Your cart is empty",
                    "cart_items": [],
                    "cart_count": 0
                }
            
            return {
                "success": True,
                "message": f"You have {len(items)} item(s) in your cart",
                "cart_items": items,
                "cart_count": len(items)
            }
        except Exception as e:
            logger.error(f"Error viewing cart: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "cart_items": []
            }
    
    async def _remove_from_cart(self, user_id: Optional[str], session_id: Optional[str], 
                              product_indices: List[int]) -> Dict[str, Any]:
        """Remove products from the cart"""
        try:
            if not product_indices:
                return {
                    "success": False,
                    "error": "No product indices provided",
                    "cart_items": []
                }
            
            # Try to get cart
            cart = await self._find_cart(user_id, session_id)
            
            if not cart:
                return {
                    "success": False,
                    "error": "Cart not found",
                    "cart_items": []
                }
            
            # Remove items
            removed_count = await self._remove_items_by_indices(cart, product_indices)
            
            # Get updated cart
            remaining_items = await self._get_cart_items(cart)
            
            return {
                "success": True,
                "message": f"Removed {removed_count} item(s) from your cart",
                "cart_items": remaining_items,
                "cart_count": len(remaining_items)
            }
        except Exception as e:
            logger.error(f"Error removing from cart: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "cart_items": []
            }
    
    async def _clear_cart(self, user_id: Optional[str], session_id: Optional[str]) -> Dict[str, Any]:
        """Clear all items from the cart"""
        try:
            # Try to get cart
            cart = await self._find_cart(user_id, session_id)
            
            if not cart:
                return {
                    "success": True,
                    "message": "Cart is already empty",
                    "cart_items": []
                }
            
            # Clear cart
            await self._clear_cart_items(cart)
            
            return {
                "success": True,
                "message": "Your cart has been cleared",
                "cart_items": [],
                "cart_count": 0
            }
        except Exception as e:
            logger.error(f"Error clearing cart: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "cart_items": []
            }
    
    @sync_to_async
    def _get_or_create_cart(self, user_id: Optional[str], session_id: Optional[str]) -> tuple:
        """Get or create a cart for the user or session"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                cart, created = Cart.objects.get_or_create(
                    user=user,
                    defaults={'updated_at': timezone.now()}
                )
                return cart, session_id
            except User.DoesNotExist:
                pass
        
        # For anonymous users, use session ID
        if session_id:
            cart, created = Cart.objects.get_or_create(
                session_id=session_id,
                defaults={'updated_at': timezone.now()}
            )
            return cart, session_id
        else:
            # Create an anonymous cart with new session ID
            new_session_id = str(uuid.uuid4())
            cart = Cart.objects.create(
                session_id=new_session_id,
                updated_at=timezone.now()
            )
            return cart, new_session_id
    
    @sync_to_async
    def _find_cart(self, user_id: Optional[str], session_id: Optional[str]) -> Optional[Cart]:
        """Find a cart for the user or session"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                return Cart.objects.filter(user=user).first()
            except User.DoesNotExist:
                pass
        
        if session_id:
            return Cart.objects.filter(session_id=session_id).first()
        
        return None
    
    @sync_to_async
    def _create_saved_item(self, cart: Cart, product_data: Dict[str, Any], 
                         conversation_id: Optional[str]) -> SavedItem:
        """Create a saved item in the cart"""
        conversation = None
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id)
            except Conversation.DoesNotExist:
                pass
        
        # Check if this product is already in the cart
        product_id = product_data.get('product_id', '')
        existing_item = SavedItem.objects.filter(
            cart=cart,
            product_id=product_id
        ).first()
        
        if existing_item:
            # Update existing item
            existing_item.updated_at = timezone.now()
            existing_item.save()
            return existing_item
        
        # Create new saved item
        price = product_data.get('price', 0)
        if not isinstance(price, (int, float)):
            try:
                # Try to convert string price to float
                price = float(str(price).replace('$', '').replace(',', ''))
            except (ValueError, AttributeError):
                price = 0
        
        original_price = product_data.get('original_price')
        if original_price and not isinstance(original_price, (int, float)):
            try:
                original_price = float(str(original_price).replace('$', '').replace(',', ''))
            except (ValueError, AttributeError):
                original_price = None
        
        return SavedItem.objects.create(
            cart=cart,
            product_id=product_id,
            title=product_data.get('title', 'Product'),
            price=price,
            original_price=original_price,
            image_url=product_data.get('image_url', ''),
            product_url=product_data.get('url', ''),
            retailer=product_data.get('retailer', 'Unknown'),
            description=product_data.get('description', ''),
            conversation=conversation,
            metadata=product_data  # Store the full product data
        )
    
    @sync_to_async
    def _get_cart_item_count(self, cart: Cart) -> int:
        """Get the number of items in the cart"""
        return SavedItem.objects.filter(cart=cart).count()
    
    @sync_to_async
    def _get_cart_items(self, cart: Cart) -> List[Dict[str, Any]]:
        """Get all items in the cart"""
        saved_items = SavedItem.objects.filter(cart=cart).order_by('-created_at')
        
        item_dicts = []
        for item in saved_items:
            # Try to use stored metadata first
            if item.metadata and isinstance(item.metadata, dict):
                item_dict = item.metadata.copy()
            else:
                # Otherwise build a basic dictionary
                item_dict = {
                    'product_id': item.product_id,
                    'title': item.title,
                    'price': item.price,
                    'image_url': item.image_url,
                    'url': item.product_url,
                    'retailer': item.retailer,
                    'description': item.description
                }
            
            # Ensure key fields are present
            if 'id' not in item_dict:
                item_dict['id'] = item.product_id
            if 'saved_item_id' not in item_dict:
                item_dict['saved_item_id'] = item.id
                
            item_dicts.append(item_dict)
            
        return item_dicts
    
    @sync_to_async
    def _remove_items_by_indices(self, cart: Cart, indices: List[int]) -> int:
        """Remove items from the cart by their indices"""
        saved_items = list(SavedItem.objects.filter(cart=cart).order_by('-created_at'))
        
        removed_count = 0
        for idx in indices:
            if 0 <= idx < len(saved_items):
                saved_items[idx].delete()
                removed_count += 1
        
        return removed_count
    
    @sync_to_async
    def _clear_cart_items(self, cart: Cart) -> None:
        """Clear all items from the cart"""
        SavedItem.objects.filter(cart=cart).delete()
    
    def _format_saved_item(self, saved_item: SavedItem) -> Dict[str, Any]:
        """Format a SavedItem model to a dictionary"""
        # Try to use stored metadata first
        if saved_item.metadata and isinstance(saved_item.metadata, dict):
            item_dict = saved_item.metadata.copy()
        else:
            # Otherwise build a basic dictionary
            item_dict = {}
        
        # Ensure key fields are present
        item_dict.update({
            'product_id': saved_item.product_id,
            'title': saved_item.title,
            'price': saved_item.price,
            'original_price': saved_item.original_price,
            'image_url': saved_item.image_url,
            'url': saved_item.product_url,
            'retailer': saved_item.retailer,
            'description': saved_item.description,
            'saved_item_id': saved_item.id
        })
        
        return item_dict
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Define the parameters schema for the cart management tool"""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Cart action to perform (add, view, remove, clear)",
                    "enum": ["add", "view", "remove", "clear"]
                },
                "user_id": {
                    "type": ["string", "null"],
                    "description": "ID of the user (optional)"
                },
                "session_id": {
                    "type": ["string", "null"],
                    "description": "Session ID for anonymous users (optional)"
                },
                "product_data": {
                    "type": ["object", "null"],
                    "description": "Product data to add to cart (required for 'add' action)"
                },
                "product_indices": {
                    "type": ["array", "null"],
                    "description": "Indices of products to remove (required for 'remove' action)",
                    "items": {
                        "type": "integer"
                    }
                },
                "conversation_id": {
                    "type": ["string", "null"],
                    "description": "ID of the conversation (optional)"
                }
            },
            "required": ["action"]
        }
    
    def _get_returns_schema(self) -> Dict[str, Any]:
        """Define the return value schema for the cart management tool"""
        return {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the operation was successful"
                },
                "message": {
                    "type": ["string", "null"],
                    "description": "Human-readable message about the operation"
                },
                "error": {
                    "type": ["string", "null"],
                    "description": "Error message if the operation failed"
                },
                "cart_items": {
                    "type": "array",
                    "description": "Items in the cart after the operation",
                    "items": {
                        "type": "object"
                    }
                },
                "cart_count": {
                    "type": ["integer", "null"],
                    "description": "Number of items in the cart"
                },
                "session_id": {
                    "type": ["string", "null"],
                    "description": "Session ID (possibly new) for anonymous users"
                }
            }
        }
