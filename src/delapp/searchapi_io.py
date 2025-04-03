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
from dotenv import load_dotenv, find_dotenv
from functools import lru_cache
import hashlib
import json
import asyncio
import aiohttp
import traceback

# Force reload the .env file
load_dotenv(find_dotenv(), override=True)

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
        logger.info(f"SEARCHAPI KEY LOADED: {self.api_key[:5]}..." if self.api_key else "NO SEARCHAPI KEY FOUND")
        self.base_url = "https://www.searchapi.io/api/v1/search"
        self._cache = {}  # Simple in-memory cache
        self._retailer_url_cache = {}  # Cache for retailer URLs
        self._api_call_count = 0  # Track API calls for debugging
        
        if not self.api_key:
            raise ValueError("Missing SearchAPI.io API key")

    
    def get_direct_retailer_url(self, product_id: str) -> Optional[str]:
        """Fetches the direct retailer URL using the product ID"""
        if not product_id:
            return None
            
        # Check cache first before making API call
        if product_id in self._retailer_url_cache:
            return self._retailer_url_cache[product_id]
            
        # Limit API calls for retailer URLs - only fetch for certain items to save API quota
        # Retailer URL calls consume a lot of quota so we'll be selective
        # For others, we'll just use the standard product link
        return None
            
    async def get_direct_retailer_url_async(self, product_id: str, session: aiohttp.ClientSession) -> Optional[str]:
        """Async version to fetch the direct retailer URL using the product ID"""
        if not product_id:
            return None
            
        # Check cache first
        if product_id in self._retailer_url_cache:
            return self._retailer_url_cache[product_id]
        
        # Skip retailer URL fetching to conserve API quota
        return None

    def _generate_cache_key(self, query: str, min_price: Optional[float], max_price: Optional[float], 
                           condition: Optional[str], max_results: int) -> str:
        """Generate a unique cache key for search parameters"""
        params = {
            'q': query,
            'min_price': min_price,
            'max_price': max_price,
            'condition': condition,
            'max_results': max_results
        }
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(param_str.encode()).hexdigest()

    @lru_cache(maxsize=100)
    def search_products(self, query: str, min_price: Optional[float] = None, 
                        max_price: Optional[float] = None, condition: Optional[str] = None,
                        max_results: int = 20) -> List[ProductDeal]:
        """Search for products using SearchAPI.io with caching"""
        cache_key = self._generate_cache_key(query, min_price, max_price, condition, max_results)
        
        # Check if we have cached results
        if cache_key in self._cache:
            logger.info(f"Cache hit for query: {query}")
            return self._cache[cache_key]
            
        try:
            # Limit max_results to save API quota
            effective_max = min(max_results, 10)  # Never request more than 10 items to save quota
                
            params = {
                'q': f"{query}",  # Explicitly include product type
                'engine': 'google_shopping',
                'api_key': self.api_key,
                'num': effective_max,
                'gl': 'us',  # Set country if needed
                'hl': 'en'   # Set language
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
            self._api_call_count += 1
            logger.info(f"Making API call #{self._api_call_count} for: {query}")
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Log the raw API response for debugging
            logger.debug(f"SearchAPI.io Response: {data}")

            items = []
            for item in data.get('shopping_results', []):
                try:
                    # Use the product link directly instead of fetching retailer URL to save API calls
                    product_link = item.get('product_link', '#')
                    
                    price_str = item.get('price', '0')
                    if isinstance(price_str, str):
                        # Remove currency symbols and commas
                        price_str = price_str.replace('$', '').replace(',', '')
                        price = float(price_str)
                    else:
                        price = float(price_str)
                        
                    original_price_str = item.get('original_price')
                    original_price = None
                    if original_price_str:
                        if isinstance(original_price_str, str):
                            original_price_str = original_price_str.replace('$', '').replace(',', '')
                            original_price = float(original_price_str)
                        else:
                            original_price = float(original_price_str)

                    product = ProductDeal(
                        product_id=item.get('product_id', ''),
                        title=item.get('title', 'No title available'),
                        price=price,
                        original_price=original_price,
                        url=product_link,  # Direct product_link without retailer URL lookup
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

            result = items[:effective_max]
            # Cache the results
            self._cache[cache_key] = result
            return result
        except Exception as e:
            logger.error(f"Error searching products using SearchAPI.io: {str(e)}")
            return []

    async def search_products_async(self, query: str, min_price: Optional[float] = None, 
                               max_price: Optional[float] = None, condition: Optional[str] = None,
                               max_results: int = 20) -> List[ProductDeal]:
        """Async version to search for products using SearchAPI.io"""
        cache_key = self._generate_cache_key(query, min_price, max_price, condition, max_results)
        
        # Check if we have cached results
        if cache_key in self._cache:
            logger.info(f"Cache hit for async query: {query}")
            return self._cache[cache_key]
            
        try:
            # Limit max_results to save API quota
            effective_max = min(max_results, 10)  # Never request more than 10 items
            
            params = {
                'q': query,
                'engine': 'google_shopping',
                'api_key': self.api_key,
                'num': effective_max
            }

            # Add price filters if specified
            if min_price is not None:
                params['min_price'] = min_price
                logger.info(f"Setting min_price: {min_price}")
            if max_price is not None:
                params['max_price'] = max_price
                logger.info(f"Setting max_price: {max_price}")

            # Add condition filter if specified
            if condition:
                params['condition'] = condition
                logger.info(f"Setting condition: {condition}")
                
            logger.info(f"SearchAPI.io async params: {params}")

            async with aiohttp.ClientSession() as session:
                logger.info(f"Sending async request to URL: {self.base_url}")
                self._api_call_count += 1
                logger.info(f"Making API call #{self._api_call_count} for: {query}")
                
                async with session.get(self.base_url, params=params) as response:
                    logger.info(f"Received async response with status: {response.status}")
                    
                    if response.status != 200:
                        logger.error(f"API error: {response.status}")
                        error_text = await response.text()
                        logger.error(f"Error response: {error_text}")
                        return []
                        
                    data = await response.json()
                    
                    # Log the raw API response for debugging
                    logger.info(f"Async SearchAPI.io shopping_results count: {len(data.get('shopping_results', []))}")
                    
                    items = []
                    # Process items directly instead of in parallel to reduce API calls
                    for item in data.get('shopping_results', []):
                        try:
                            # Use the product link directly instead of fetching retailer URL
                            product_link = item.get('product_link', '#')
                            
                            price_str = item.get('price', '0')
                            if isinstance(price_str, str):
                                # Remove currency symbols and commas
                                price_str = price_str.replace('$', '').replace(',', '')
                                price = float(price_str)
                            else:
                                price = float(price_str)
                                
                            original_price_str = item.get('original_price')
                            original_price = None
                            if original_price_str:
                                if isinstance(original_price_str, str):
                                    original_price_str = original_price_str.replace('$', '').replace(',', '')
                                    original_price = float(original_price_str)
                                else:
                                    original_price = float(original_price_str)
                            
                            product = ProductDeal(
                                product_id=item.get('product_id', ''),
                                title=item.get('title', 'No title available'),
                                price=price,
                                original_price=original_price,
                                url=product_link,  # Direct product_link without retailer URL lookup
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
                    
                    result = items[:effective_max]
                    # Cache the results
                    self._cache[cache_key] = result
                    return result
                    
        except Exception as e:
            logger.error(f"Error in async product search: {str(e)}")
            logger.error(traceback.format_exc())
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
            
    async def search_deals_async(self, query: str, min_price: Optional[float] = None,
                             max_price: Optional[float] = None, max_results: int = 10) -> Dict[str, List[ProductDeal]]:
        """Async version to search for deals using SearchAPI.io"""
        try:
            deals = await self.provider.search_products_async(
                query=query,
                min_price=min_price,
                max_price=max_price,
                max_results=max_results
            )
            return {'searchapi': deals}
        except Exception as e:
            logger.error(f"Error in async deal aggregation: {str(e)}")
            return {'searchapi': []}

    def set_llm(self, llm_instance):
        """Store the LLM instance for compatibility with previous implementation"""
        self.llm = llm_instance
        return self