"""
Test script for ShopAgent initialization

This script tests the initialization of the ShopAgent to help diagnose
why the agent executor isn't being initialized properly.
"""
import os
import sys
import logging
import asyncio
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
logger = logging.getLogger("test_agent")

# Try to load environment variables from .env file
load_dotenv()

# Log API keys (redacted) for debugging
api_keys = {
    "GROQ_API_KEY": bool(os.environ.get("GROQ_API_KEY")),
    "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
}
logger.info(f"API keys available: {api_keys}")

async def test_agent_initialization():
    """Test ShopAgent initialization and query processing"""
    try:
        from delapp.agent.shop_agent_factory import ShopAgentFactory
        
        # Try creating agent with LLM
        logger.info("Creating ShopAgent with LLM...")
        agent_with_llm = ShopAgentFactory.create_agent(use_llm=True)
        logger.info(f"Agent created: {agent_with_llm}")
        logger.info(f"Agent executor initialized: {agent_with_llm.agent_executor is not None}")
        
        # Try a fallback approach without LLM
        logger.info("Creating ShopAgent without LLM (fallback)...")
        agent_no_llm = ShopAgentFactory.create_agent(use_llm=False)
        logger.info(f"Fallback agent created: {agent_no_llm}")
        
        if agent_with_llm.agent_executor:
            # Test a simple query
            logger.info("Testing query processing...")
            result = await agent_with_llm.process_query(
                query="Show me coffee makers under $50",
                conversation_id="test_conversation"
            )
            logger.info(f"Query result: {result}")
        else:
            logger.error("Agent executor not initialized, can't test query processing")
            
    except Exception as e:
        logger.error(f"Error in test: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_agent_initialization())
    logger.info("Test completed")
