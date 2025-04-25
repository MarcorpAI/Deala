"""
Product Search Tool for ShopAgent

This tool handles searching for products based on natural language queries.
It extracts relevant search parameters and uses SearchAPI.io to find products.
"""
from typing import Dict, Any, Optional, List, Union
import json
import logging
import re

from .base_tool import BaseTool
from ...searchapi_io import DealAggregator

logger = logging.getLogger(__name__)

class ProductSearchTool(BaseTool):
    """Tool for searching products based on various criteria"""
    
    def __init__(self):
        """Initialize the product search tool with the DealAggregator"""
        super().__init__(
            name="product_search",
            description="Search for products based on natural language queries and specific criteria"
        )
        self.provider = DealAggregator()
    
    async def execute(self, 
                     query: str, 
                     min_price: Optional[float] = None,
                     max_price: Optional[float] = None,
                     max_results: int = 10,
                     **kwargs) -> Dict[str, Any]:
        """
        Execute a product search based on the provided parameters.
        
        Args:
            query: The search query string
            min_price: Minimum price filter (optional)
            max_price: Maximum price filter (optional)
            max_results: Maximum number of results to return
            **kwargs: Additional filter parameters
            
        Returns:
            Dict containing search results and metadata
        """
        try:
            logger.info(f"Executing product search for: {query} with price range: ${min_price or 0}-${max_price or 'unlimited'}")
            
            # Extract any price filters from natural language if not explicitly provided
            if max_price is None:
                extracted_max_price = self._extract_max_price(query)
                if extracted_max_price is not None:
                    max_price = extracted_max_price
                    logger.info(f"Extracted max price from query: ${max_price}")
            
            # Execute the search
            results = await self.provider.search_deals_async(
                query=query,
                min_price=min_price,
                max_price=max_price,
                max_results=max_results
            )
            
            # Log the raw results structure to debug
            logger.debug(f"Raw search results keys: {list(results.keys()) if isinstance(results, dict) else 'Not a dict'}") 
            if isinstance(results, dict) and 'searchapi' in results:
                logger.debug(f"Number of raw products in searchapi: {len(results['searchapi'])}")            
            
            # Format the search results
            products = self._format_search_results(results)
            logger.info(f"Formatted {len(products)} products from search results")
            
            # If the API returned no products (e.g., due to quota limits), provide mock data for testing
            if not products:
                logger.warning("No products returned from API, using mock data for testing")
                products = self._generate_mock_products(query, min_price, max_price, max_results)
                logger.info(f"Generated {len(products)} mock products for testing")
                return {
                    "success": True,
                    "products": products,
                    "count": len(products),
                    "mock_data": True,  # Flag to indicate this is mock data
                    "search_params": {
                        "query": query,
                        "min_price": min_price,
                        "max_price": max_price,
                        "max_results": max_results
                    }
                }
            
            # Log a sample product if available
            if products and len(products) > 0:
                logger.debug(f"Sample product after formatting: {products[0]['title']} - ${products[0]['price']}")
            
            return {
                "success": True,
                "products": products,
                "count": len(products),
                "search_params": {
                    "query": query,
                    "min_price": min_price,
                    "max_price": max_price,
                    "max_results": max_results
                }
            }
        
        except Exception as e:
            logger.error(f"Error in product search: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "products": [],
                "count": 0
            }
            
    def _generate_mock_products(self, query: str, min_price: Optional[float] = None,
                              max_price: Optional[float] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Generate mock product data for testing when the real API is unavailable
        (e.g., when hitting quota limits)
        
        Args:
            query: The search query string
            min_price: Minimum price filter
            max_price: Maximum price filter
            max_results: Maximum number of mock products to generate
            
        Returns:
            List of mock product objects that match the structure of real products
        """
        import random
        import uuid
        from datetime import datetime, timedelta
        
        # Extract key terms from the query for more realistic mock data
        query_lower = query.lower()
        
        # Define product categories and map query terms to them
        product_categories = {
            "shoes": ["nike", "adidas", "sneakers", "shoes", "boots", "footwear", "jordans", "dunks", "sb"],
            "electronics": ["iphone", "samsung", "phone", "laptop", "computer", "tablet", "tv", "headphones"],
            "clothing": ["shirt", "pants", "jacket", "dress", "hoodie", "sweater", "jeans", "t-shirt"],
            "home": ["furniture", "sofa", "chair", "table", "bed", "mattress", "couch"],
            "kitchen": ["appliance", "blender", "mixer", "toaster", "microwave", "coffee"]
        }
        
        # Detect category from the search query
        category = next(
            (cat for cat, terms in product_categories.items() 
            if any(term in query_lower for term in terms)),
            "general"
        )
        
        # Brand detection
        common_brands = {
            "shoes": ["Nike", "Adidas", "New Balance", "Puma", "Reebok", "Converse", "Vans"],
            "electronics": ["Apple", "Samsung", "Sony", "LG", "Microsoft", "Google", "Dell"],
            "clothing": ["H&M", "Zara", "Levi's", "Gap", "Calvin Klein", "Ralph Lauren"],
            "home": ["IKEA", "Ashley", "Wayfair", "Casper", "Pottery Barn"],
            "kitchen": ["KitchenAid", "Cuisinart", "Ninja", "Instant Pot", "OXO"]
        }
        
        # Extract any brand mentioned in the query
        mentioned_brand = None
        all_brands = [brand for brands in common_brands.values() for brand in brands]
        for brand in all_brands:
            if brand.lower() in query_lower:
                mentioned_brand = brand
                break
                
        # Get category-specific brands
        category_brands = common_brands.get(category, common_brands["kitchen"])
        
        # If Nike is mentioned or the search is for shoes and includes SB/dunk terms
        if "nike" in query_lower or (category == "shoes" and any(term in query_lower for term in ["sb", "dunk"])):
            category = "shoes"
            mentioned_brand = "Nike"
            category_brands = ["Nike"]
            
        # Select a brand (prefer mentioned brand if available)
        brand = mentioned_brand or random.choice(category_brands)
        
        # Set price range if not provided
        if min_price is None:
            min_price = 10.0
        if max_price is None:
            max_price = 100.0
            
        # Cap the number of mock products
        num_products = min(max_results, 10)
        
        mock_products = []
        for i in range(num_products):
            # Generate a random price within the specified range
            price = round(random.uniform(min_price, max_price), 2)
            
            # Set up product details based on the category
            product_info = {}
            
            if category == "shoes":
                # Shoe-specific details
                styles = ["SB Dunk Low", "SB Dunk High", "Air Force 1", "Air Max", "Jordan 1", "Blazer", "Air Jordan"] 
                colors = ["Black/White", "University Blue", "Red/White", "Green/White", "Gray/White", "Triple Black"]
                sizes = [f"US {size}" for size in range(7, 14)]
                
                # If searching for SB Dunks specifically
                if "dunk" in query_lower or "sb" in query_lower:
                    styles = ["SB Dunk Low", "SB Dunk High", "SB Dunk Mid"]
                    if "low" in query_lower:
                        styles = ["SB Dunk Low"]
                    elif "high" in query_lower:
                        styles = ["SB Dunk High"]
                
                style = random.choice(styles)
                color = random.choice(colors)
                size = random.choice(sizes)
                
                product_info = {
                    "title": f"{brand} {style} '{random.choice(['Pro', 'Premium', 'Retro', 'Special Edition'])}' {color}",
                    "description": f"Authentic {brand} {style} in {color}. Available in size {size}. Perfect for skateboarding or casual wear.",
                    "retailer": random.choice(["Nike.com", "FootLocker", "GOAT", "StockX", "Finish Line"]),
                    "image_url": f"https://placehold.co/600x400/orange/white?text=Nike+SB+Dunk+{i}"
                }
            else:
                # Generic product info for other categories
                features = ["Premium", "Limited Edition", "Classic", "New Release", "Signature"]
                feature = random.choice(features)
                product_info = {
                    "title": f"{brand} {feature} {query.split()[0]} {random.choice(['Pro', 'Elite', 'Plus', 'Ultra'])}",
                    "description": f"High-quality {category} product from {brand}. Features include {feature.lower()} design and premium materials.",
                    "retailer": random.choice(["Amazon", "Walmart", "Target", "Best Buy", "Specialized Store"]),
                    "image_url": f"https://placehold.co/600x400/gray/black?text={brand}+Product+{i}"
                }
            
            # Create the mock product with appropriate data            
            mock_product = {
                "id": str(uuid.uuid4()),
                "title": product_info["title"],
                "price": price,
                "original_price": round(price * 1.2, 2) if random.random() > 0.5 else None,
                "url": f"https://example.com/products/{i}",
                "image_url": product_info["image_url"],
                "retailer": product_info["retailer"],
                "description": product_info["description"],
                "available": True,
                "rating": round(random.uniform(3.5, 5.0), 1),
                "review_count": random.randint(10, 500),
                "timestamp": datetime.now() - timedelta(days=random.randint(0, 30)),
                "currency": "USD"
            }
            
            mock_products.append(mock_product)
            
        return mock_products
    
    def _extract_max_price(self, query: str) -> Optional[float]:
        """
        Extract maximum price filter from natural language query.
        
        Args:
            query: The search query string
            
        Returns:
            Extracted maximum price or None if not found
        """
        # Common price filter patterns
        patterns = [
            r'under\s+\$?(\d+(?:\.\d+)?)',
            r'less than\s+\$?(\d+(?:\.\d+)?)',
            r'below\s+\$?(\d+(?:\.\d+)?)',
            r'up to\s+\$?(\d+(?:\.\d+)?)',
            r'max(?:imum)?\s+(?:price|cost)?\s+\$?(\d+(?:\.\d+)?)',
            r'no more than\s+\$?(\d+(?:\.\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _format_search_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format the search results into a standardized product list.
        
        Args:
            results: Raw search results from the provider
            
        Returns:
            List of standardized product dictionaries
        """
        formatted_products = []
        
        # Handle different possible data structures
        raw_products = []
        
        # Check for searchapi key (the actual key used by DealAggregator)
        if isinstance(results, dict):
            if 'searchapi' in results:
                # This is the primary format from DealAggregator
                raw_products = results['searchapi']
                logger.debug(f"Found {len(raw_products)} products in 'searchapi' key")
            elif 'products' in results:
                # Alternative format
                raw_products = results['products']
                logger.debug(f"Found {len(raw_products)} products in 'products' key")
            elif len(results) > 0:
                # Maybe it's a direct list of products in a dict?
                logger.debug(f"No standard keys found, available keys: {list(results.keys())}")
                # Try to use all values as potential products
                for key, value in results.items():
                    if isinstance(value, list):
                        raw_products.extend(value)
        elif isinstance(results, list):
            # Direct list of products
            raw_products = results
            logger.debug(f"Results was a direct list with {len(raw_products)} items")
        
        # Process each product, handling different object types
        for product in raw_products:
            try:
                # Handle both dictionary and ProductDeal object formats
                if isinstance(product, dict):
                    # Convert dict to our standard format
                    formatted_product = {
                        'product_id': product.get('product_id', product.get('id', '')),
                        'title': product.get('title', ''),
                        'price': product.get('price', 0),
                        'original_price': product.get('original_price', product.get('originalPrice')),
                        'url': product.get('url', product.get('link', '')),
                        'image_url': product.get('image_url', product.get('imageUrl', '')),
                        'retailer': product.get('retailer', product.get('seller', 'Unknown')),
                        'description': product.get('description', ''),
                        'rating': product.get('rating', product.get('product_star_rating')),
                        'review_count': product.get('review_count', product.get('reviewCount')),
                        'condition': product.get('condition', 'New'),
                        'shipping_info': product.get('shipping_info', '')
                    }
                else:
                    # Try to handle ProductDeal objects by extracting attributes
                    try:
                        # Using getattr to be safe with different object types
                        formatted_product = {
                            'product_id': getattr(product, 'product_id', ''),
                            'title': getattr(product, 'title', ''),
                            'price': getattr(product, 'price', 0),
                            'original_price': getattr(product, 'original_price', None),
                            'url': getattr(product, 'url', ''),
                            'image_url': getattr(product, 'image_url', ''),
                            'retailer': getattr(product, 'retailer', 'Unknown'),
                            'description': getattr(product, 'description', ''),
                            'rating': getattr(product, 'rating', None),
                            'review_count': getattr(product, 'review_count', None),
                            'condition': getattr(product, 'condition', 'New'),
                            'shipping_info': getattr(product, 'shipping_info', '')
                        }
                    except AttributeError:
                        # Skip objects we can't process
                        logger.warning(f"Couldn't extract attributes from product object: {type(product)}")
                        continue
                
                # Add to our formatted products list
                formatted_products.append(formatted_product)
                
            except Exception as e:
                logger.error(f"Error formatting product: {str(e)}")
                continue
            
        logger.info(f"Successfully formatted {len(formatted_products)} products out of {len(raw_products)} raw products")
        return formatted_products
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Define the parameters schema for the product search tool"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query for finding products"
                },
                "min_price": {
                    "type": ["number", "null"],
                    "description": "Minimum price filter"
                },
                "max_price": {
                    "type": ["number", "null"],
                    "description": "Maximum price filter"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    
    def _get_returns_schema(self) -> Dict[str, Any]:
        """Define the return value schema for the product search tool"""
        return {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the search was successful"
                },
                "products": {
                    "type": "array",
                    "description": "List of product results",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string"},
                            "title": {"type": "string"},
                            "price": {"type": ["number", "string"]},
                            "original_price": {"type": ["number", "string", "null"]},
                            "url": {"type": "string"},
                            "image_url": {"type": "string"},
                            "retailer": {"type": "string"},
                            "description": {"type": "string"},
                            "rating": {"type": ["number", "null"]},
                            "review_count": {"type": ["integer", "null"]},
                            "condition": {"type": "string"},
                            "shipping_info": {"type": "string"}
                        }
                    }
                },
                "count": {
                    "type": "integer",
                    "description": "Number of products found"
                },
                "search_params": {
                    "type": "object",
                    "description": "Parameters used for the search"
                }
            }
        }
