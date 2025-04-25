"""
Product Details Tool for ShopAgent

This tool retrieves detailed information about specific products,
resolving product references from conversation context.
"""
from typing import Dict, Any, Optional, List, Union
import logging

from .base_tool import BaseTool
from ...searchapi_io import DealAggregator

logger = logging.getLogger(__name__)

class ProductDetailsTool(BaseTool):
    """Tool for retrieving detailed information about products"""
    
    def __init__(self):
        """Initialize the product details tool"""
        super().__init__(
            name="product_details",
            description="Retrieve detailed information about a specific product"
        )
        self.provider = DealAggregator()
    
    async def execute(self,
                     product_id: str,
                     **kwargs) -> Dict[str, Any]:
        """
        Execute a product details request.
        
        Args:
            product_id: ID of the product to retrieve details for
            **kwargs: Additional parameters
            
        Returns:
            Dict containing product details
        """
        try:
            logger.info(f"Retrieving details for product: {product_id}")
            
            # Get the direct retailer URL for the product
            retailer_url = await self.provider.provider.get_direct_retailer_url_async(product_id)
            
            # Build the product details response
            # This could be enhanced to make additional API calls for comprehensive details
            return {
                "success": True,
                "product_details": {
                    "product_id": product_id,
                    "direct_url": retailer_url,
                    # Additional details would be populated here based on available data
                }
            }
        
        except Exception as e:
            logger.error(f"Error retrieving product details: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "product_details": None
            }
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Define the parameters schema for the product details tool"""
        return {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "ID of the product to retrieve details for"
                }
            },
            "required": ["product_id"]
        }
    
    def _get_returns_schema(self) -> Dict[str, Any]:
        """Define the return value schema for the product details tool"""
        return {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the details retrieval was successful"
                },
                "product_details": {
                    "type": ["object", "null"],
                    "description": "Detailed product information",
                    "properties": {
                        "product_id": {"type": "string"},
                        "direct_url": {"type": "string"},
                        # Additional properties would be defined here
                    }
                },
                "error": {
                    "type": ["string", "null"],
                    "description": "Error message if the operation failed"
                }
            }
        }
