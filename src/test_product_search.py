"""
Test script specifically for product search functionality

This script tests the product search capabilities to ensure structured
product data is being returned to the frontend.
"""
import os
import sys
import logging
import asyncio
import json
import django
from dotenv import load_dotenv

# Add the project root to the Python path so we can import Django modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up Django environment - MUST happen before importing any Django models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dela.settings')
django.setup()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s %(asctime)s %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_product_search")

# Try to load environment variables from .env file
load_dotenv()

async def test_product_search():
    """Test the product search functionality from start to end"""
    try:
        from delapp.agent.shop_agent_factory import ShopAgentFactory
        from delapp.agent.tools.langchain_tools import ProductSearchLangChainTool
        
        logger.info("Creating ProductSearchLangChainTool...")
        search_tool = ProductSearchLangChainTool()
        
        # Try a direct search
        query = "Show me coffee makers under $50"
        logger.info(f"Executing search for: '{query}'...")
        
        # Execute the search
        search_result_json = await search_tool._arun(query)
        
        # Parse the JSON result
        logger.info("Parsing search results...")
        result_obj = json.loads(search_result_json)
        
        # Show a summary of the results
        logger.info(f"Search successful: {result_obj.get('success', False)}")
        logger.info(f"Found {len(result_obj.get('products', []))} products")
        
        # Print the text response
        text_response = result_obj.get('text', '')
        print(f"\n{'-'*80}\nTEXT RESPONSE:\n{'-'*80}\n{text_response}\n{'-'*80}\n")
        
        # Print detailed info about the first 3 products
        products = result_obj.get('products', [])
        if products:
            print(f"\n{'-'*80}\nPRODUCT DATA (First 3 of {len(products)}):\n{'-'*80}")
            for i, product in enumerate(products[:3]):
                print(f"\nProduct {i+1}:")
                for key, value in product.items():
                    print(f"  {key}: {value}")
                    
            # Check if products have the necessary fields for the frontend
            required_fields = ['id', 'title', 'price', 'url']
            missing_fields = []
            
            for i, product in enumerate(products):
                for field in required_fields:
                    if field not in product:
                        missing_fields.append(f"Product {i} missing '{field}'")
            
            if missing_fields:
                logger.warning(f"Missing required fields in products: {', '.join(missing_fields)}")
            else:
                logger.info("All products have the required fields for frontend display")
                
        # Now create a ShopAgent and test product search through it
        logger.info("\nTesting product search through ShopAgent...")
        agent = ShopAgentFactory.create_agent(use_llm=True)
        
        if agent.agent_executor:
            result = await agent.process_query(
                query=query,
                conversation_id="test_conversation"
            )
            
            # Print the agent result
            print(f"\n{'-'*80}\nAGENT RESULT:\n{'-'*80}")
            print(f"Response: {result['response'][:200]}...")
            print(f"Number of products: {len(result['products'])}")
            
            if result['products']:
                print(f"\nFirst product from agent:")
                for key, value in result['products'][0].items():
                    print(f"  {key}: {value}")
        else:
            logger.error("Agent executor not initialized, can't test query processing")
            
    except Exception as e:
        logger.error(f"Error in test: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_product_search())
    logger.info("Test completed")
