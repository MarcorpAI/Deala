"""
LangChain tool wrappers for the ShopAgent

This module provides wrappers that convert our native tool classes into proper LangChain tool objects
that can be used with LangChain's agent framework.
"""
import json
import uuid
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun

# Set up logging
logger = logging.getLogger(__name__)

class ProductSearchLangChainTool(BaseTool):
    """LangChain tool wrapper for product search"""
    
    name: str = "product_search"
    description: str = """
    Search for products based on a natural language query.
    Use this tool when the user is looking for products to buy.
    Input should be the search query exactly as the user asked.
    """
    search_tool: Any = None
    
    def __init__(self):
        """Initialize with our native search tool"""
        super().__init__()
        
        try:
            # Try to import and create the native tool
            from ..tools.product_search_tool import ProductSearchTool
            self.search_tool = ProductSearchTool()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error initializing native search tool: {str(e)}")
            # Create mock search tool for testing
            self.search_tool = None
        
    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the product search tool asynchronously."""
        logger.info(f"ProductSearchLangChainTool executing for query: {query}")
        try:
            # Handle case where search_tool wasn't initialized properly
            if self.search_tool is None:
                return json.dumps({
                    "text": "I'm sorry, but the product search functionality is currently unavailable. Our team is working on it.",
                    "products": [],
                    "success": False
                })
                
            result = await self.search_tool.execute(query)
            products = result.get('products', [])
            is_mock_data = result.get('mock_data', False)
            
            if not products and not is_mock_data:
                return json.dumps({
                    "text": f"I couldn't find any products matching '{query}'. Please try a different search term.",
                    "products": [],
                    "success": False
                })
            
            # Format the response for the human readable part
            response = f"I found {len(products)} products matching '{query}':\n\n"
            
            # Format the products to match the frontend DealCard component expectations
            formatted_products = []
            
            for product in products:
                # Format product for response text
                price = product.get('price', 'Price not available')
                price_display = f"${price:.2f}" if isinstance(price, (int, float)) else price
                
                # Add to text response
                if len(formatted_products) < 5:  # Only show first 5 in text
                    response += f"{len(formatted_products)+1}. {product.get('title', 'Unknown product')} - {price_display}\n"
                    # Add retailer if available
                    if retailer := product.get('retailer'):
                        response += f"   Retailer: {retailer}\n"
                    # Add a blank line between products
                    response += "\n"
                
                # Create frontend-compatible product object
                formatted_product = {
                    'id': product.get('id', str(uuid.uuid4())),
                    'name': product.get('title', 'Product'),  # Frontend expects 'name'
                    'currentPrice': float(price) if isinstance(price, (int, float)) else 0,
                    'originalPrice': float(product.get('original_price', 0)) if product.get('original_price') else None,
                    'image_url': product.get('image_url', '') or 'https://via.placeholder.com/300x300.png?text=Product+Image',
                    'productLink': product.get('url', '#'),  # Frontend expects 'productLink'
                    'retailer': product.get('retailer', 'Online retailer'),
                    'description': product.get('description', '')
                }
                
                # Calculate savings if possible
                if formatted_product['originalPrice'] and formatted_product['currentPrice'] < formatted_product['originalPrice']:
                    formatted_product['savings'] = {
                        'amount': formatted_product['originalPrice'] - formatted_product['currentPrice'],
                        'percent': int((formatted_product['originalPrice'] - formatted_product['currentPrice']) / 
                                      formatted_product['originalPrice'] * 100)
                    }
                
                formatted_products.append(formatted_product)
            
            # Add hint about follow-up capability
            response += "You can ask for more details about any of these products.\n"
            
            # Handle datetime objects for proper serialization
            def json_serial(obj):
                if isinstance(obj, datetime) or isinstance(obj, datetime.date):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")
            
            # Ensure all products have required fields for frontend
            for product in formatted_products:
                # Ensure every product has a name
                if 'name' not in product or not product['name']:
                    product['name'] = 'Product'
                    
                # Ensure image_url exists
                if 'image_url' not in product or not product['image_url']:
                    product['image_url'] = 'https://via.placeholder.com/300x300.png?text=Product+Image'
                    
                # Ensure productLink exists
                if 'productLink' not in product or not product['productLink']:
                    product['productLink'] = '#'
                    
                # Ensure price fields are numbers
                if 'currentPrice' not in product or not isinstance(product['currentPrice'], (int, float)):
                    product['currentPrice'] = 0.0
                    
            # Add a hint that these products can be shown on frontend
            response += "\n\nYou can view these products in detail or ask me more specific questions about any of them."
                
            # Log the products being sent to ensure they're properly formatted
            logger.info(f"Sending {len(formatted_products)} formatted products to frontend")
            if formatted_products:
                logger.info(f"Sample formatted product: {formatted_products[0]['name']} - ${formatted_products[0]['currentPrice']}")
            
            # Always include specific mock_data flag when this is a mock response
            return json.dumps({
                "text": response,
                "products": formatted_products,  # Use the frontend-formatted products
                "success": True,
                "has_products": len(formatted_products) > 0,  # Explicit flag for frontend to show products
                "mock_data": result.get('mock_data', False),  # Pass through mock_data flag
                "product_count": len(formatted_products)  # Explicit count for debugging
            }, default=json_serial)
            
        except Exception as e:
            logger.error(f"Error executing ProductSearchLangChainTool: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # Return a JSON error message
            return json.dumps({
                "text": f"I encountered an error while searching for products: {str(e)}",
                "products": [],
                "success": False
            })
    
    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Synchronous version (required but not used)"""
        raise NotImplementedError("This tool only supports async execution")
        
    def _json_serializer(self, obj):
        """Helper method to properly serialize datetime objects to JSON"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} is not JSON serializable")


class ProductDetailsLangChainTool(BaseTool):
    """LangChain tool wrapper for product details"""
    
    name: str = "product_details"
    description: str = """
    Get detailed information about a specific product.
    Use this when the user wants to know more about a product they've already found.
    Input should be a product ID or name from previous search results.
    """
    details_tool: Any = None
    
    def __init__(self):
        """Initialize with our native details tool"""
        super().__init__()
        
        try:
            # Try to import and create the native tool
            from ..tools.product_details_tool import ProductDetailsTool
            self.details_tool = ProductDetailsTool()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error initializing native details tool: {str(e)}")
            # Set to None as a fallback
            self.details_tool = None
        
    async def _arun(self, product_identifier: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Async run the tool with the given product identifier"""
        try:
            # Handle case where details_tool wasn't initialized
            if self.details_tool is None:
                return f"I'm sorry, but the product details functionality is currently unavailable. Our team is working on it."
            
            # The identifier could be a product ID or a name reference
            result = await self.details_tool.execute(product_id=product_identifier)
            product = result.get('product', {})
            
            if not product:
                return f"I couldn't find details for the product '{product_identifier}'."
            
            # Format the detailed response
            response = f"## {product.get('title', 'Product Details')}\n\n"
            
            # Format price
            price = product.get('price')
            if price is not None:
                if isinstance(price, (int, float)):
                    price = f"${price:.2f}"
                response += f"**Price:** {price}\n\n"
            
            # Add retailer
            if retailer := product.get('retailer'):
                response += f"**Retailer:** {retailer}\n\n"
            
            # Add description
            if description := product.get('description'):
                response += f"**Description:** {description}\n\n"
            
            # Add rating if available
            if rating := product.get('rating'):
                response += f"**Rating:** {rating}/5\n\n"
            
            # Add review count if available
            if review_count := product.get('review_count'):
                response += f"**Reviews:** {review_count}\n\n"
            
            # Add URL if available
            if url := product.get('url'):
                response += f"**Product Link:** {url}\n\n"
            
            return response
        except Exception as e:
            return f"Error getting product details: {str(e)}"
    
    def _run(self, product_identifier: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Synchronous version (required but not used)"""
        raise NotImplementedError("This tool only supports async execution")


class CartManagementLangChainTool(BaseTool):
    """LangChain tool wrapper for cart management"""
    
    name: str = "cart_management"
    description: str = """
    Manage the user's shopping cart (add/remove/view items).
    Use this when the user wants to add a product to their cart, remove a product, or view their cart.
    Input should be a JSON string with 'operation' and other required fields.
    Operations: 'add', 'remove', 'view'
    """
    cart_tool: Any = None
    
    def __init__(self):
        """Initialize with our native cart tool"""
        super().__init__()
        
        try:
            # Try to import and create the native tool
            from ..tools.cart_management_tool import CartManagementTool
            self.cart_tool = CartManagementTool()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error initializing native cart tool: {str(e)}")
            # Set to None as a fallback
            self.cart_tool = None
        
    async def _arun(self, action_json: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Async run the tool with the given action JSON"""
        try:
            # Handle case where cart_tool wasn't initialized
            if self.cart_tool is None:
                return f"I'm sorry, but the shopping cart functionality is currently unavailable. Our team is working on it."
            
            import json
            
            # Parse the action JSON
            try:
                action = json.loads(action_json) if isinstance(action_json, str) else action_json
            except json.JSONDecodeError:
                return f"Error: Invalid JSON format for cart action: {action_json}"
            
            operation = action.get('operation', '')
            
            if operation == 'add':
                product_id = action.get('product_id')
                quantity = action.get('quantity', 1)
                
                result = await self.cart_tool.execute(
                    operation='add',
                    product_id=product_id,
                    quantity=quantity
                )
                
                if result.get('success'):
                    return f"Successfully added the product to your cart."
                else:
                    return f"Failed to add the product to your cart: {result.get('error', 'Unknown error')}"
                    
            elif operation == 'remove':
                product_id = action_data.get('product_id')
                
                result = await self.cart_tool.execute(
                    operation='remove',
                    product_id=product_id
                )
                
                if result.get('success'):
                    return f"Successfully removed the product from your cart."
                else:
                    return f"Failed to remove the product from your cart: {result.get('error', 'Unknown error')}"
                    
            elif operation == 'view':
                result = await self.cart_tool.execute(operation='view')
                
                if not result.get('success'):
                    return f"Failed to view your cart: {result.get('error', 'Unknown error')}"
                
                cart_items = result.get('items', [])
                
                if not cart_items:
                    return "Your cart is currently empty."
                
                response = "## Your Shopping Cart\n\n"
                total = 0
                
                for item in cart_items:
                    price = item.get('price', 0)
                    quantity = item.get('quantity', 1)
                    item_total = price * quantity
                    total += item_total
                    
                    response += f"- {item.get('title')} (x{quantity}): ${item_total:.2f}\n"
                
                response += f"\n**Total:** ${total:.2f}"
                return response
            else:
                return f"Unknown cart operation: {operation}. Valid operations are 'add', 'remove', and 'view'."
        except json.JSONDecodeError:
            return "Error: The input must be a valid JSON string."
        except Exception as e:
            return f"Error managing cart: {str(e)}"
    
    def _run(self, action_json: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Synchronous version (required but not used)"""
        raise NotImplementedError("This tool only supports async execution")
