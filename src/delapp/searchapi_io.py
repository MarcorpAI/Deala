"""
Streamlined deal providers implementation using SearchAPI.io for product search.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import os
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProductDeal:
    product_id: str
    title: str
    price: float
    original_price: Optional[float]
    url: str
    image_url: str
    retailer: str
    description: str
    available: bool
    rating: Optional[float]
    seller: Optional[str]
    review_count: Optional[int]
    timestamp: datetime
    condition: Optional[str]
    shipping_info: Optional[str]
    discount: Optional[str]
    coupon: Optional[str]
    trending: Optional[bool]
    sold_count: Optional[int]
    watchers: Optional[int]
    return_policy: Optional[str]
    location: Optional[str]

class BaseProvider:
    """Base provider with rate limiting"""
    def __init__(self):
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds between requests

    def _rate_limit(self):
        """Basic rate limiting implementation"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

class SearchAPIProvider(BaseProvider):
    """SearchAPI.io product search implementation"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('SEARCHAPI_API_KEY')
        self.base_url = "https://www.searchapi.io/api/v1/search"
        
        if not self.api_key:
            raise ValueError("Missing SearchAPI.io API key")

    
    def get_direct_retailer_url(self, product_id: str) -> Optional[str]:
        """Fetches the direct retailer URL using the product ID"""
        if not product_id:
            return None
            
        params = {
            'api_key': self.api_key,
            'engine': 'google_product',
            'product_id': product_id
        }
        
        try:
            self._rate_limit()
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Get the direct retailer URL from the product data
            if data.get('product_results', {}).get('seller_link'):
                return data['product_results']['seller_link']
                    
            return None
            
        except Exception as e:
            logger.error(f"Error fetching retailer URL: {str(e)}")
            return None

    def search_products(self, query: str, min_price: Optional[float] = None, 
                        max_price: Optional[float] = None, condition: Optional[str] = None,
                        max_results: int = 20) -> List[ProductDeal]:
        """Search for products using SearchAPI.io"""
        try:
            params = {
                'q': query,
                'engine': 'google_shopping',
                'api_key': self.api_key,
                'num': max_results
            }

            # Add price filters if specified
            if min_price is not None:
                params['min_price'] = min_price
            if max_price is not None:
                params['max_price'] = max_price

            # Add condition filter if specified
            if condition:
                params['condition'] = condition

            self._rate_limit()
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Log the raw API response for debugging
            logger.debug(f"SearchAPI.io Response: {data}")

            items = []
            for item in data.get('shopping_results', []):
                try:
                    print("Raw item data:", item) 
                    # direct_url = self.get_direct_retailer_url(item.get('offers_link')) if item.get('offers_link') else None
                    # url_to_use = direct_url or item.get('product_link', '#')

                    direct_url = self.get_direct_retailer_url(item.get('product_id'))

                    product = ProductDeal(
                        product_id=item.get('product_id', ''),
                        title=item.get('title', 'No title available'),
                        price=float(item.get('price', 0).replace('$', '').replace(',', '')),
                        original_price=float(item.get('original_price', 0).replace('$', '').replace(',', '')) if item.get('original_price') else None,
                        # url=item.get('product_link', '#'),
                        url=direct_url or item.get('product_link', '#'),
                        image_url=item.get('thumbnail', ''),
                        retailer=item.get('source', 'Unknown retailer'),
                        description=item.get('description', 'No description available'),
                        available=True,  # Assume available unless specified otherwise
                        rating=float(item.get('rating', 0)) if item.get('rating') else None,
                        seller=item.get('seller', 'Unknown Seller'),
                        review_count=item.get('reviews', 0),
                        timestamp=datetime.now(),
                        condition=item.get('condition', 'Condition not specified'),
                        shipping_info=item.get('shipping', 'Shipping info not available'),
                        discount=f"{item.get('discount', '0%')} off" if item.get('discount') else None,
                        coupon=item.get('coupon', None),
                        trending=item.get('trending', False),
                        sold_count=item.get('sold_count', 0),
                        watchers=item.get('watchers', 0),
                        return_policy=item.get('return_policy', 'No return policy'),
                        location=item.get('location', 'Location not available')
                    )
                    items.append(product)
                except Exception as e:
                    logger.error(f"Error processing item {item.get('product_id', 'Unknown')}: {str(e)}")
                    continue

            return items[:max_results]
        except Exception as e:
            logger.error(f"Error searching products using SearchAPI.io: {str(e)}")
            return []

class DealAggregator:
    """Handles product searches using SearchAPI.io"""
    
    def __init__(self):
        self.provider = SearchAPIProvider()

    def search_deals(self, query: str, min_price: Optional[float] = None,
                    max_price: Optional[float] = None, max_results: int = 10) -> Dict[str, List[ProductDeal]]:
        """Search for deals using SearchAPI.io"""
        try:
            deals = self.provider.search_products(
                query=query,
                min_price=min_price,
                max_price=max_price,
                max_results=max_results
            )
            return {'searchapi': deals}
        except Exception as e:
            logger.error(f"Error in deal aggregation: {str(e)}")
            return {'searchapi': []}