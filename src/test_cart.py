import os
import django
import asyncio
import logging

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dela.settings')
django.setup()

from delapp.llm_engine import ConversationalDealFinder
from delapp.models import Cart, SavedItem
from asgiref.sync import sync_to_async

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_add_to_cart():
    """Test adding an item to the cart"""
    logger.info("TESTING ADD TO CART")
    
    # Create a ConversationalDealFinder instance
    deal_finder = ConversationalDealFinder()
    
    # Initialize with mock products
    deal_finder.conversation_state = {
        'current_products': [
            {
                'id': 'test_product_1',
                'name': 'Test Product 1',
                'title': 'Test Product 1',
                'price': 99.99,
                'retailer': 'Test Retailer',
                'description': 'A test product',
                'image_url': 'https://example.com/test.jpg',
                'url': 'https://example.com/test-product'
            },
            {
                'id': 'test_product_2',
                'name': 'Test Product 2',
                'title': 'Test Product 2',
                'price': 149.99,
                'retailer': 'Test Retailer 2',
                'description': 'Another test product',
                'image_url': 'https://example.com/test2.jpg',
                'url': 'https://example.com/test-product-2'
            }
        ],
        'session_id': 'test_session'
    }
    
    # Test add to cart intent with different queries
    queries = [
        "Add the first product to my cart",
        "Save the second item",
    ]
    
    for query in queries:
        logger.info(f"Testing query: '{query}'")
        result = await deal_finder._handle_add_to_cart_intent(query)
        logger.info(f"Result message: {result.get('message')}")
        logger.info(f"Cart action: {result.get('cart_action')}")
        
    # Check the database
    @sync_to_async
    def get_cart_items():
        cart = Cart.objects.filter(session_id='test_session').first()
        if cart:
            items = SavedItem.objects.filter(cart=cart)
            return [(item.title, item.price) for item in items]
        return []
    
    cart_items = await get_cart_items()
    logger.info(f"Items in cart: {cart_items}")

async def test_view_cart():
    """Test viewing the cart"""
    logger.info("\nTESTING VIEW CART")
    
    # Create a ConversationalDealFinder instance
    deal_finder = ConversationalDealFinder()
    
    # Set the same session_id as in add_to_cart
    deal_finder.conversation_state = {
        'session_id': 'test_session'
    }
    
    # Test view cart intent
    query = "Show me my cart"
    logger.info(f"Testing query: '{query}'")
    result = await deal_finder._handle_view_cart_intent(query)
    logger.info(f"Result message: {result.get('message')}")
    logger.info(f"Items count: {result.get('cart_count')}")
    logger.info(f"Products returned: {len(result.get('products', []))}")

async def test_remove_from_cart():
    """Test removing from cart"""
    logger.info("\nTESTING REMOVE FROM CART")
    
    # Create a ConversationalDealFinder instance
    deal_finder = ConversationalDealFinder()
    
    # Set the same session_id as in add_to_cart
    deal_finder.conversation_state = {
        'session_id': 'test_session'
    }
    
    # Test remove cart intent with different queries
    queries = [
        "Remove the first item from my cart",
        "Clear my cart"
    ]
    
    for query in queries:
        logger.info(f"Testing query: '{query}'")
        result = await deal_finder._handle_remove_from_cart_intent(query)
        logger.info(f"Result message: {result.get('message')}")
        logger.info(f"Cart action: {result.get('cart_action')}")
        
        # Check the cart after each removal
        @sync_to_async
        def get_cart_items():
            cart = Cart.objects.filter(session_id='test_session').first()
            if cart:
                items = SavedItem.objects.filter(cart=cart)
                return [(item.title, item.price) for item in items]
            return []
        
        cart_items = await get_cart_items()
        logger.info(f"Items in cart after removal: {cart_items}")

async def run_tests():
    """Run all tests in sequence"""
    # First, clean up any existing test data
    @sync_to_async
    def clean_up():
        cart = Cart.objects.filter(session_id='test_session').first()
        if cart:
            SavedItem.objects.filter(cart=cart).delete()
            cart.delete()
        logger.info("Cleaned up test data")
    
    await clean_up()
    
    # Run the tests
    await test_add_to_cart()
    await test_view_cart()
    await test_remove_from_cart()
    
    # Clean up again
    await clean_up()
    
    logger.info("ALL TESTS COMPLETED")

if __name__ == '__main__':
    asyncio.run(run_tests()) 