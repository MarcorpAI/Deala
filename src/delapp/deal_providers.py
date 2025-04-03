"""
Streamlined deal providers implementation focusing on eBay and Rakuten integration.
"""
from typing import Dict, List, Optional
from datetime import datetime
import os
import time
from functools import lru_cache
import logging
import requests
from ebaysdk.finding import Connection as Finding
from ebaysdk.shopping import Connection as Shopping
from .models import ProductDeal  # Changed this line
from products.services import ProductStorageService
from dotenv import load_dotenv
load_dotenv()



print("Current EBAY_APP_ID:", os.getenv('EBAY_APP_ID'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)







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

class EbayProvider(BaseProvider):
    """eBay product search implementation"""
    
    def __init__(self):
        super().__init__()
        self.app_id = "Markkaav-Deala-PRD-066ca4013-7b5eb942"
        self.cert_id = "PRD-66ca4013b5af-16c8-4ee4-b038-02b6"
        self.dev_id =  "9418f37d-8999-453c-b918-791a5598aa6c"

        print("Loaded EBAY_APP_ID:", self.app_id)
        print("Loaded EBAY_CERT_ID:", self.cert_id)
        print("Loaded EBAY_DEV_ID:", self.dev_id)
                
        if not all([self.app_id, self.cert_id, self.dev_id]):
            raise ValueError("Missing eBay API credentials")
        
        self.config = {
            'domain': 'svcs.ebay.com',  # Production endpoint
            'siteid': 'EBAY-US',
            'warnings': True
        }
        
        
        self.finding_api = Finding(appid=self.app_id, config_file=None, **self.config)
        self.shopping_api = Shopping(appid=self.app_id, config_file=None, **self.config)

    

    @lru_cache(maxsize=100)
    def _get_item_details(self, item_id: str) -> Dict:
        """Cached item details retrieval"""
        self._rate_limit()
        try:
            # Make the API call to get item details
            response = self.shopping_api.execute('GetSingleItem', {
                'ItemID': item_id,
                'IncludeSelector': 'Details,ItemSpecifics'
            })
            
            # Log the raw response for debugging
            logger.debug(f"Item details response for {item_id}: {response.dict()}")

            # Check if the response contains the 'Ack' field
            if hasattr(response, 'dict') and 'Ack' in response.dict():
                ack = response.dict()['Ack']
                if ack == 'Success':
                    # The API call was successful, return the response
                    return response.dict()
                else:
                    # The API call failed or has warnings
                    logger.warning(f"API call for item {item_id} returned Ack: {ack}")
                    return {}
            else:
                # The response does not contain the expected 'Ack' field
                logger.warning(f"Unexpected response structure for item {item_id}")
                return {}
        except Exception as e:
            logger.error(f"Error retrieving details for item {item_id}: {str(e)}")
            return {}

    def _calculate_default_rating(self, item) -> float:
        """Calculate a default rating based on available item metrics"""
        base_rating = 4.0  # Start with a decent base rating
        
        try:
            # Adjust rating based on seller feedback score if available
            if hasattr(item, 'sellerInfo') and hasattr(item.sellerInfo, 'positiveFeedbackPercent'):
                feedback_percent = float(item.sellerInfo.positiveFeedbackPercent)
                rating_adjustment = (feedback_percent - 95) / 10  # Scale feedback impact
                base_rating += rating_adjustment
            
            # Adjust rating based on number of items sold
            if hasattr(item.sellingStatus, 'quantitySold'):
                sold_count = int(item.sellingStatus.quantitySold)
                if sold_count > 100:
                    base_rating += 0.5
                elif sold_count > 50:
                    base_rating += 0.3
                elif sold_count > 10:
                    base_rating += 0.1
            
            # Adjust rating based on item condition
            if hasattr(item, 'condition') and hasattr(item.condition, 'conditionId'):
                if item.condition.conditionId == '1000':  # New
                    base_rating += 0.2
            
            # Ensure rating stays within 1-5 range
            return min(max(base_rating, 1.0), 5.0)
            
        except Exception as e:
            logger.warning(f"Error calculating default rating: {str(e)}")
            return 4.0  # Return base rating if calculation fails

        



    def search_products(self, query: str, min_price: Optional[float] = None, 
                   max_price: Optional[float] = None, condition: Optional[str] = None,
                   max_results: int = 20) -> List[ProductDeal]:
        try:
            api_params = {
                'keywords': query,
                'paginationInput': {'entriesPerPage': max_results},
                'sortOrder': 'BestMatch',
                'itemFilter': []
            }

            # Add price filters if specified
            if min_price is not None:
                api_params['itemFilter'].append({
                    'name': 'MinPrice',
                    'value': str(min_price)
                })
            if max_price is not None:
                api_params['itemFilter'].append({
                    'name': 'MaxPrice',
                    'value': str(max_price)
                })

            # Add condition filter if specified
            if condition:
                condition_map = {
                    "new": "1000",
                    "used": "3000",
                    "refurbished": "2500",
                    "open box": "1500",
                    "seller refurbished": "2000"
                }
                condition_value = condition_map.get(condition.lower())
                if condition_value:
                    api_params['itemFilter'].append({
                        'name': 'Condition',
                        'value': condition_value
                    })
                else:
                    logger.warning(f"Invalid condition value: {condition}")

            # Log the API parameters for debugging
            logger.debug(f"eBay API Parameters: {api_params}")

            self._rate_limit()
            response = self.finding_api.execute('findItemsAdvanced', api_params)
            
            # Log the raw API response for debugging
            logger.debug(f"eBay API Response: {response.dict()}")

            items = []
            if hasattr(response.reply, 'searchResult') and hasattr(response.reply.searchResult, 'item'):
                for item in response.reply.searchResult.item:
                    try:
                        # Log the raw item structure for debugging
                        logger.debug(f"Processing item: {item.itemId}")
                        logger.debug(f"Item structure: {item}")

                        # Try to get additional details, but fall back to basic info if it fails
                        item_details = self._get_item_details(item.itemId)
                        
                        # Handle missing attributes gracefully
                        default_rating = self._calculate_default_rating(item)
                        title = getattr(item, 'title', 'No title available')
                        price = float(getattr(item.sellingStatus, 'currentPrice', {}).get('value', 0))
                        original_price = float(item.listingInfo.buyItNowPrice.value) if hasattr(item.listingInfo, 'buyItNowPrice') else None
                        url = getattr(item, 'viewItemURL', 'No URL available')
                        image_url = getattr(item, 'galleryURL', 'No image available')
                        description = item_details.get('Item', {}).get('Description', 'No description available')
                        condition = item_details.get('Item', {}).get('ConditionDisplayName', 'Condition not specified')
                        shipping_info = item.shippingInfo.shippingServiceCost.value if hasattr(item.shippingInfo, 'shippingServiceCost') else 'Shipping cost not available'
                        discount = f"{((original_price - price) / original_price * 100):.0f}% off" if original_price else None
                        coupon = item.listingInfo.discountPriceInfo.originalRetailPrice.value if hasattr(item.listingInfo, 'discountPriceInfo') else None
                        trending = item.listingInfo.listingType == 'Auction'  # Example: Auctions are trending
                        sold_count = item.sellingStatus.quantitySold if hasattr(item.sellingStatus, 'quantitySold') else 0
                        watchers = item.listingInfo.watchCount if hasattr(item.listingInfo, 'watchCount') else 0
                        return_policy = item.returnPolicy.returnsAccepted if hasattr(item, 'returnPolicy') else 'No return policy'
                        location = item.location if hasattr(item, 'location') else 'Location not available'

                        product = ProductDeal(
                            product_id=item.itemId,
                            title=title,
                            price=price,
                            original_price=original_price,
                            url=url,
                            image_url=image_url,
                            retailer='eBay',
                            description=description,
                            available=True,
                            rating=default_rating,  # Use the calculated default rating
                            review_count=100,
                            timestamp=datetime.now(),
                            condition=condition,
                            shipping_info=shipping_info,
                            discount=discount,
                            coupon=coupon,
                            trending=trending,
                            sold_count=sold_count,
                            watchers=watchers,
                            return_policy=return_policy,
                            location=location
                        )
                        items.append(product)
                    except Exception as e:
                        logger.error(f"Error processing item {item.itemId}: {str(e)}")
                        continue
            
            return items
        except Exception as e:
            logger.error(f"Error searching eBay products: {str(e)}")
            return []




class WalmartProvider(BaseProvider):
    """Walmart product search implementation using RapidAPI"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('WALMART_API_KEY')
        self.base_url = "https://walmart-api4.p.rapidapi.com/search"

        
        if not self.api_key:
            raise ValueError("Missing RapidAPI key")

    def _safe_float(self, value, default=None):
        """Safely convert value to float, handling empty strings and invalid values"""
        if not value or value == '':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _extract_price_from_string(self, price_str):
        """Extract numeric price from string like '$79.00'"""
        if not price_str:
            return None
        try:
            # Handle case where price might be already a float or int
            if isinstance(price_str, (float, int)):
                return float(price_str)
            return float(price_str.replace('$', '').replace(',', ''))
        except (ValueError, AttributeError):
            return None

    def _get_image_url(self, image_data):
        """Safely extract image URL from image data which could be string or dict"""
        if isinstance(image_data, str):
            return image_data
        elif isinstance(image_data, dict):
            return image_data.get('thumbnailUrl', '')
        return ''

    
    def _get_shipping_info(self, fulfillment_groups):
        """Safely extract shipping information"""
        if not fulfillment_groups or not isinstance(fulfillment_groups, list):
            return 'Shipping info not available'
        
        try:
            for group in fulfillment_groups:
                if isinstance(group, dict) and 'text' in group:
                    return group['text']
        except Exception:
            pass
        
        return 'Shipping info not available'

    def _get_description(self, desc):
        """Safely handle description text"""
        return desc if desc is not None else 'No description available'

    

    def search_products(self, query: str, min_price: Optional[float] = None, 
                    max_price: Optional[float] = None, condition: Optional[str] = None,
                    max_results: int = 20) -> List[ProductDeal]:
        try:
            headers = {
                'X-RapidAPI-Key': self.api_key,
                'X-RapidAPI-Host': 'walmart-api4.p.rapidapi.com'
            }
            
            params = {
                'q': query,
                'page': '1',
                'sort': 'price_low'
            }

            if min_price is not None:
                params['minPrice'] = min_price
            if max_price is not None:
                params['maxPrice'] = max_price

            self._rate_limit()
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            items = []
            search_results = data.get('searchResult', [])
            
            logger.debug(f"Number of search result groups: {len(search_results)}")
            
            for result_group in search_results:
                logger.debug(f"Processing result group with {len(result_group) if isinstance(result_group, list) else 'non-list'} items")
                
                if not isinstance(result_group, list):
                    continue
                
                for item in result_group:
                    try:
                        logger.debug(f"Processing item: {item.get('name', 'Unknown')}")
                        
                        # Get the price
                        current_price = None
                        original_price = None
                        
                        if 'price' in item:
                            current_price = self._extract_price_from_string(item['price'])
                            
                        if not current_price and 'priceInfo' in item:
                            price_info = item['priceInfo']
                            current_price = (
                                self._extract_price_from_string(price_info.get('linePrice')) or
                                self._extract_price_from_string(price_info.get('itemPrice'))
                            )
                            original_price = self._extract_price_from_string(price_info.get('wasPrice'))
                        
                        if not current_price:
                            logger.debug(f"Skipping item {item.get('name', 'Unknown')} - no valid price found")
                            continue

                        # Create ProductDeal object
                        product = ProductDeal(
                            product_id=str(item.get('sellerId', '')),
                            title=item.get('name', 'No title available'),
                            price=current_price,
                            original_price=original_price,
                            url=item.get('productLink', ''),
                            image_url=self._get_image_url(item.get('image', '')),
                            retailer='Walmart',
                            description=self._get_description(item.get('shortDescription')),
                            available=item.get('availabilityStatusDisplayValue') == 'In stock',
                            rating=self._safe_float(item.get('rating', {}).get('averageRating')),
                            review_count=item.get('rating', {}).get('numberOfReviews'),
                            timestamp=datetime.now(),
                            condition=condition,
                            product_star_rating=None,

                            shipping_info=self._get_shipping_info(item.get('fulfillmentBadgeGroups')),
                            discount=f"{item.get('priceInfo', {}).get('savingsAmt')}% off" if item.get('priceInfo', {}).get('savingsAmt') else None,
                            coupon=None,
                            trending=bool(item.get('isSponsoredFlag')),
                            sold_count=None,
                            watchers=None,
                            return_policy=item.get('returnPolicy', {}).get('returnPolicyText', 'No return policy'),
                            location=None
                        )

                        items.append(product)
                        logger.debug(f"Successfully processed item: {product.title}")
                        
                    except Exception as e:
                        logger.error(f"Error processing Walmart item: {str(e)}", exc_info=True)
                        continue

            logger.debug(f"Successfully processed {len(items)} items")
            return items[:max_results]
        except Exception as e:
            logger.error(f"Error searching Walmart products: {str(e)}", exc_info=True)
            return []




## AMAZON PROVIDER




class AmazonProvider(BaseProvider):
    """Walmart product search implementation using RapidAPI"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('AMAZON_API_KEY')
        self.base_url =  "https://real-time-amazon-data.p.rapidapi.com/search"
        
        if not self.api_key:
            raise ValueError("Missing RapidAPI key")

    def _safe_float(self, value, default=None):
        """Safely convert value to float, handling empty strings and invalid values"""
        if not value or value == '':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _extract_price_from_string(self, price_str):
        """Extract numeric price from string like '$79.00'"""
        if not price_str:
            return None
        try:
            # Handle case where price might be already a float or int
            if isinstance(price_str, (float, int)):
                return float(price_str)
            return float(price_str.replace('$', '').replace(',', ''))
        except (ValueError, AttributeError):
            return None

    def _get_image_url(self, image_data):
        """Safely extract image URL from image data which could be string or dict"""
        if isinstance(image_data, str):
            return image_data
        elif isinstance(image_data, dict):
            return image_data.get('thumbnailUrl', '')
        return ''

    
    def _get_shipping_info(self, fulfillment_groups):
        """Safely extract shipping information"""
        if not fulfillment_groups or not isinstance(fulfillment_groups, list):
            return 'Shipping info not available'
        
        try:
            for group in fulfillment_groups:
                if isinstance(group, dict) and 'text' in group:
                    return group['text']
        except Exception:
            pass
        
        return 'Shipping info not available'

    def _get_description(self, desc):
        """Safely handle description text"""
        return desc if desc is not None else 'No description available'

        
    def search_products(self, query: str, min_price: Optional[float] = None, 
                        max_price: Optional[float] = None, condition: Optional[str] = None,
                        max_results: int = 20) -> List[ProductDeal]:
        """Search for products on Amazon using RapidAPI"""
        try:
            headers = {
                'X-RapidAPI-Key': self.api_key,
                'X-RapidAPI-Host': 'real-time-amazon-data.p.rapidapi.com'
            }
            
            params = {
                'query': query,
                'page': '1',
            }

            # Add price filters if specified
            if min_price is not None:
                params['minPrice'] = min_price
            if max_price is not None:
                params['maxPrice'] = max_price

            self._rate_limit()
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Log the raw API response
            logger.debug(f"Amazon API Response: {data}")

            items = []
            products = data.get('data', {}).get('products', [])  # Access the products list
            
            for item in products:
                try:
                    # Extract price information
                    current_price = self._extract_price_from_string(item.get('product_price'))
                    original_price = self._extract_price_from_string(item.get('product_original_price'))

                    # Create ProductDeal object
                    product = ProductDeal(
                        product_id=item.get('asin', 'N/A'),  # Use ASIN as the product ID
                        title=item.get('product_title', 'No title available'),
                        price=current_price,
                        original_price=original_price,
                        url=item.get('product_url', ''),
                        image_url=item.get('product_photo', 'No image available'),
                        retailer='Amazon',
                        # product_star_rating=item.get('product_star_rating', None),
                        description=f"Rating: {item.get('product_star_rating', 'N/A')}",
                        available=True,  # Assume available since no info in the response
                        rating=self._safe_float(item.get('product_star_rating')),
                        review_count=item.get('product_num_ratings'),
                        timestamp=datetime.now(),
                        condition=condition,  # No condition in the response
                        shipping_info=item.get('delivery', 'Shipping info not available'),
                        discount=f"{((original_price - current_price) / original_price * 100):.0f}% off" if original_price else None,
                        coupon=None,  # No coupon info in the response
                        trending=item.get('is_best_seller', False) or item.get('is_amazon_choice', False),
                        sold_count=None,  # No sold count in the response
                        watchers=None,  # No watchers in the response
                        return_policy='No return policy',  # No return policy in the response
                        location=None  # No location in the response
                    )
                    items.append(product)
                except Exception as e:
                    logger.error(f"Error processing Amazon item: {str(e)}")
                    continue
            
            logger.debug(f"Processed {len(items)} items")
            return items[:max_results]
        except Exception as e:
            logger.error(f"Error searching Amazon products: {str(e)}")
            return []


class EtsyProvider(BaseProvider):
    def search_products(self, query: str, min_price: Optional[float] = None, 
                        max_price: Optional[float] = None, condition: Optional[str] = None,
                        max_results: int = 20) -> List[ProductDeal]:
        # Implement Etsy product search logic here
        pass








class DealAggregator:
    """Handles product searches across multiple providers with storage integration"""
    
    def __init__(self):
        # Initialize providers
        self.ebay = EbayProvider()
        # self.amazon = AmazonProvider()
        self.walmart = WalmartProvider()
        self.storage = ProductStorageService()

    def set_llm(self, llm):
        self.llm = llm

    


    def _standardize_amazon_response(self, item: dict) -> ProductDeal:
        """Transform Amazon API response into standard ProductDeal format with improved price handling"""
        if isinstance(item, ProductDeal):
            return item
            
        try:
            # Extract and validate current price
            price_str = item.get('product_price', '0')
            current_price = float(price_str.replace('$', '').replace(',', '')) if price_str else 0.0
            
            # Extract and validate original price
            original_price_str = item.get('product_original_price')
            original_price = float(original_price_str.replace('$', '').replace(',', '')) if original_price_str else None
            
            return ProductDeal(
                product_id=item.get('asin', ''),
                title=item.get('product_title', 'No title available'),
                price=current_price,  # Use validated price
                original_price=original_price,  # Use validated original price
                url=item.get('product_url', ''),
                image_url=item.get('product_photo', ''),
                retailer='Amazon',
                description=item.get('product_title', 'No description available'),
                available=True,
                rating=float(item.get('product_star_rating', 0)) if item.get('product_star_rating') else None,
                review_count=item.get('product_num_ratings'),
                timestamp=datetime.now(),
                condition='New',
                shipping_info=item.get('delivery', 'Shipping info not available'),
                discount=f"{((original_price - current_price) / original_price * 100):.0f}% off" if original_price and current_price < original_price else None,
                coupon=None,
                trending=item.get('is_best_seller', False) or item.get('is_amazon_choice', False),
                sold_count=None,
                watchers=None,
                return_policy='Amazon standard return policy',
                location='United States'
            )
        except (ValueError, TypeError) as e:
            logger.error(f"Error standardizing Amazon response: {str(e)}")
            return None

    def _standardize_walmart_response(self, item: dict) -> ProductDeal:
            """Transform Walmart API response into standard ProductDeal format"""
            if isinstance(item, ProductDeal):
                return item
                
            current_price = float(item.get('price', 0))
            original_price = float(item.get('priceInfo', {}).get('wasPrice', '0').replace('$', '').replace(',', '')) if item.get('priceInfo', {}).get('wasPrice') else None
            
            return ProductDeal(
                product_id=str(item.get('sellerId', '')),
                title=item.get('name', 'No title available'),
                price=current_price,
                original_price=original_price,
                url=item.get('productLink', ''),
                image_url=item.get('image', ''),
                retailer='Walmart',
                description=item.get('shortDescription', 'No description available'),
                available=item.get('availabilityStatusDisplayValue') == 'In stock',
                rating=float(item.get('rating', {}).get('averageRating', 0)) if item.get('rating', {}).get('averageRating') else None,
                review_count=item.get('rating', {}).get('numberOfReviews'),
                timestamp=datetime.now(),
                condition='New',
                shipping_info=next((group['text'] for group in item.get('fulfillmentBadgeGroups', []) if isinstance(group, dict) and 'text' in group), 'Shipping info not available'),
                discount=f"{item.get('priceInfo', {}).get('savingsAmt')}% off" if item.get('priceInfo', {}).get('savingsAmt') else None,
                coupon=None,
                trending=bool(item.get('isSponsoredFlag')),
                sold_count=None,
                watchers=None,
                return_policy=item.get('returnPolicy', {}).get('returnPolicyText', 'Standard return policy'),
                location='United States'
            )

     




    # def search_deals(self, query: str, min_price: Optional[float] = None,
    #                 max_price: Optional[float] = None, max_results: int = 10,
    #                 condition: Optional[str] = None) -> Dict[str, List[ProductDeal]]:
    #     """
    #     Search for deals across all providers with storage integration and price validation
    #     """
    #     results = {
    #         'ebay': [],
    #         'amazon': [],
    #         'walmart': []
    #     }
        
    #     def validate_product_deal(product_deal: ProductDeal) -> Optional[ProductDeal]:
    #         """Validate and fix product deal data before storage"""
    #         try:
    #             # Set default price if null
    #             if product_deal.price is None:
    #                 if product_deal.original_price is not None:
    #                     product_deal.price = product_deal.original_price
    #                 else:
    #                     product_deal.price = 0.0  # Or return None to skip this product
    #                     logger.warning(f"Product {product_deal.product_id} has no price information")
    #                     return None

    #             # Ensure price is float
    #             product_deal.price = float(product_deal.price)
                
    #             # Convert original_price to float if exists
    #             if product_deal.original_price is not None:
    #                 product_deal.original_price = float(product_deal.original_price)
                
    #             return product_deal
    #         except (ValueError, TypeError) as e:
    #             logger.error(f"Error validating product {product_deal.product_id}: {str(e)}")
    #             return None

    #     try:
    #         # Search eBay
    #         ebay_results = self.ebay.search_products(
    #             query=query,
    #             min_price=min_price,
    #             max_price=max_price,
    #             max_results=max_results,
    #             condition=condition
    #         )
            
    #         # Validate and store eBay results
    #         for product_deal in ebay_results:
    #             validated_deal = validate_product_deal(product_deal)
    #             if validated_deal:
    #                 stored_product = self.storage.store_product(validated_deal)
    #                 results['ebay'].append(validated_deal)
            
    #         # Search Amazon
    #         amazon_response = self.amazon.search_products(
    #             query=query,
    #             min_price=min_price,
    #             max_price=max_price,
    #             max_results=max_results
    #         )
            
    #         # Validate and store Amazon results
    #         for item in amazon_response:
    #             product_deal = self._standardize_amazon_response(item)
    #             validated_deal = validate_product_deal(product_deal)
    #             if validated_deal:
    #                 stored_product = self.storage.store_product(validated_deal)
    #                 results['amazon'].append(validated_deal)
            
    #         # Search Walmart
    #         walmart_response = self.walmart.search_products(
    #             query=query,
    #             min_price=min_price,
    #             max_price=max_price,
    #             max_results=max_results
    #         )
            
    #         # Validate and store Walmart results
    #         for item in walmart_response:
    #             product_deal = self._standardize_walmart_response(item)
    #             validated_deal = validate_product_deal(product_deal)
    #             if validated_deal:
    #                 stored_product = self.storage.store_product(validated_deal)
    #                 results['walmart'].append(validated_deal)
            
    #         # Enhance descriptions
    #         results['ebay'] = self._enhance_product_descriptions(results['ebay'], query)
    #         results['amazon'] = self._enhance_product_descriptions(results['amazon'], query)
    #         results['walmart'] = self._enhance_product_descriptions(results['walmart'], query)
                
    #     except Exception as e:
    #         logger.error(f"Error in deal aggregation: {str(e)}")
            
    #     return results



    def search_deals(self, query: str, min_price: Optional[float] = None,
                    max_price: Optional[float] = None, max_results: int = 10,
                    condition: Optional[str] = None) -> Dict[str, List[ProductDeal]]:
        """
        Search for deals across all providers with storage integration and price validation
        """
        results = {
            'ebay': [],
            'walmart': [],
            'amazon': []  # Keep empty list for Amazon to maintain compatibility
        }
        
        def validate_product_deal(product_deal: ProductDeal) -> Optional[ProductDeal]:
            """Validate and fix product deal data before storage"""
            try:
                # Set default price if null
                if product_deal.price is None:
                    if product_deal.original_price is not None:
                        product_deal.price = product_deal.original_price
                    else:
                        product_deal.price = 0.0  # Or return None to skip this product
                        logger.warning(f"Product {product_deal.product_id} has no price information")
                        return None

                # Ensure price is float
                product_deal.price = float(product_deal.price)
                
                # Convert original_price to float if exists
                if product_deal.original_price is not None:
                    product_deal.original_price = float(product_deal.original_price)
                
                return product_deal
            except (ValueError, TypeError) as e:
                logger.error(f"Error validating product {product_deal.product_id}: {str(e)}")
                return None

        try:
            # Search eBay
            ebay_results = self.ebay.search_products(
                query=query,
                min_price=min_price,
                max_price=max_price,
                max_results=max_results,
                condition=condition
            )
            
            # Validate and store eBay results
            for product_deal in ebay_results:
                validated_deal = validate_product_deal(product_deal)
                if validated_deal:
                    stored_product = self.storage.store_product(validated_deal)
                    results['ebay'].append(validated_deal)
            
            # Search Walmart
            walmart_response = self.walmart.search_products(
                query=query,
                min_price=min_price,
                max_price=max_price,
                max_results=max_results
            )
            
            # Validate and store Walmart results
            for item in walmart_response:
                product_deal = self._standardize_walmart_response(item)
                validated_deal = validate_product_deal(product_deal)
                if validated_deal:
                    stored_product = self.storage.store_product(validated_deal)
                    results['walmart'].append(validated_deal)
            
            # Enhance descriptions
            results['ebay'] = self._enhance_product_descriptions(results['ebay'], query)
            results['walmart'] = self._enhance_product_descriptions(results['walmart'], query)
                
        except Exception as e:
            logger.error(f"Error in deal aggregation: {str(e)}")
            
        return results


    def _enhance_product_descriptions(self, products: List[ProductDeal], query: str) -> List[ProductDeal]:
        """Enhance product descriptions with AI-generated content"""
        if self.llm is None:
            # Import here to avoid circular import
            from .llm_engine import ConversationalDealFinder
            self.llm = ConversationalDealFinder()
        enhanced = []
        for product in products:
            try:
                # Generate new description
                ai_description = self.llm.generate_product_description(product, query)
                
                # Create updated product deal
                enhanced_product = ProductDeal(
                    **{**product.__dict__, 'description': ai_description}
                )
                enhanced.append(enhanced_product)
            except Exception as e:
                logger.error(f"Error enhancing product {product.product_id}: {str(e)}")
                enhanced.append(product)
        return enhanced

    def get_price_history(self, product_id: str, retailer: str, days: int = 30) -> List[Dict]:
        """Get price history for a specific product"""
        return self.storage.get_price_history(product_id, retailer, days)

    def get_product_details(self, product_id: str, retailer: str) -> Optional[ProductDeal]:
        """Get detailed information for a specific product"""
        stored_product = self.storage.get_product(product_id, retailer)
        if not stored_product:
            return None
            
        # Convert stored product back to ProductDeal
        return ProductDeal(
            product_id=stored_product.product_id,
            title=stored_product.title,
            price=float(stored_product.price),
            original_price=float(stored_product.original_price) if stored_product.original_price else None,
            url=stored_product.url,
            image_url=stored_product.image_url,
            retailer=stored_product.retailer,
            description=stored_product.description,
            available=stored_product.available,
            rating=stored_product.rating,
            review_count=stored_product.review_count,
            timestamp=stored_product.timestamp,
            condition=stored_product.condition,
            shipping_info=stored_product.shipping_info,
            discount=stored_product.discount,
            coupon=stored_product.metadata.get('coupon'),
            trending=stored_product.metadata.get('trending'),
            sold_count=stored_product.metadata.get('sold_count'),
            watchers=stored_product.metadata.get('watchers'),
            return_policy=stored_product.metadata.get('return_policy'),
            location=stored_product.metadata.get('location')
        )

    def cleanup_old_products(self, days: int = 30):
        """Remove products that haven't been updated in the specified number of days"""
        self.storage.cleanup_stale_products(days)