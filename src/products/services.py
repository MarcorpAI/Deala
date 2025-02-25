from typing import Optional, Dict, List
from datetime import datetime, timedelta
from .models import StoredProduct, PriceHistory, ProductAvailabilityLog

class ProductStorageService:
    """Service for handling product storage operations"""
    
    @staticmethod
    def store_product(product_deal: 'ProductDeal') -> StoredProduct:
        """Store or update a product from a ProductDeal instance"""
        product, created = StoredProduct.objects.get_or_create(
            product_id=product_deal.product_id,
            retailer=product_deal.retailer,
            defaults={
                'title': product_deal.title,
                'price': product_deal.price,
                'original_price': product_deal.original_price,
                'url': product_deal.url,
                'image_url': product_deal.image_url,
                'description': product_deal.description,
                'available': product_deal.available,
                'rating': product_deal.rating,
                'review_count': product_deal.review_count,
                'condition': product_deal.condition,
                'shipping_info': product_deal.shipping_info,
                'discount': product_deal.discount,
                'metadata': {
                    'coupon': product_deal.coupon,
                    'trending': product_deal.trending,
                    'sold_count': product_deal.sold_count,
                    'watchers': product_deal.watchers,
                    'return_policy': product_deal.return_policy,
                    'location': product_deal.location
                }
            }
        )
        
        if not created:
            # Update existing product
            if product.price != product_deal.price:
                PriceHistory.objects.create(
                    product=product,
                    price=product_deal.price
                )
            
            if product.available != product_deal.available:
                ProductAvailabilityLog.objects.create(
                    product=product,
                    available=product_deal.available
                )
            
            # Update the product fields
            for field in ['price', 'original_price', 'title', 'description', 'available',
                         'rating', 'review_count', 'condition', 'shipping_info', 'discount']:
                if hasattr(product_deal, field):
                    setattr(product, field, getattr(product_deal, field))
            
            # Update metadata
            product.metadata.update({
                'coupon': product_deal.coupon,
                'trending': product_deal.trending,
                'sold_count': product_deal.sold_count,
                'watchers': product_deal.watchers,
                'return_policy': product_deal.return_policy,
                'location': product_deal.location
            })
            
            product.save()
        
        return product

    @staticmethod
    def get_product(product_id: str, retailer: str) -> Optional[StoredProduct]:
        """Retrieve a stored product"""
        try:
            return StoredProduct.objects.get(product_id=product_id, retailer=retailer)
        except StoredProduct.DoesNotExist:
            return None
    
    @staticmethod
    def get_price_history(product_id: str, retailer: str, days: int = 30) -> List[Dict]:
        """Get price history for a product"""
        product = StoredProduct.objects.get(product_id=product_id, retailer=retailer)
        since_date = datetime.now() - timedelta(days=days)
        
        return list(PriceHistory.objects.filter(
            product=product,
            timestamp__gte=since_date
        ).values('price', 'timestamp').order_by('timestamp'))

    @staticmethod
    def cleanup_stale_products(days: int = 30):
        """Remove products that haven't been updated in the specified number of days"""
        stale_date = datetime.now() - timedelta(days=days)
        StoredProduct.objects.filter(last_updated__lt=stale_date).delete()