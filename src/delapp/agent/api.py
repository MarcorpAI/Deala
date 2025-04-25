"""
ShopAgent API Interface

This module provides API functions that integrate the ShopAgent with Django views
and existing application components.
"""
from typing import Dict, Any, Optional, List
import logging
import json
import asyncio
from django.http import JsonResponse, HttpRequest
from django.conf import settings

from .shop_agent_factory import ShopAgentFactory
from .response_generator.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)

# Create singleton instances
_agent = None
_formatter = None

def get_agent(use_llm: bool = True):
    """Get or create the ShopAgent singleton instance"""
    global _agent
    if _agent is None:
        _agent = ShopAgentFactory.create_agent(use_llm=use_llm)
    return _agent

def get_formatter():
    """Get or create the ResponseFormatter singleton instance"""
    global _formatter
    if _formatter is None:
        _formatter = ShopAgentFactory.create_response_formatter()
    return _formatter

async def process_query(query: str, 
                      conversation_id: Optional[str] = None, 
                      user_id: Optional[str] = None,
                      session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a user query using the ShopAgent.
    
    Args:
        query: The user's query
        conversation_id: Optional conversation ID
        user_id: Optional user ID
        session_id: Optional session ID
        
    Returns:
        Dict with agent response and relevant data
    """
    try:
        logger.info(f"Processing query: '{query}' for conversation: {conversation_id}")
        
        # Get agent instance
        agent = get_agent(use_llm=True)
        
        # Process the query
        result = await agent.process_query(
            query=query,
            conversation_id=conversation_id,
            user_id=user_id,
            context={"session_id": session_id} if session_id else None
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return {
            'response': "I encountered an error while processing your request. Please try again.",
            'conversation_id': conversation_id,
            'error': str(e)
        }

async def add_to_cart(product_data: Dict[str, Any], 
                    user_id: Optional[str] = None,
                    session_id: Optional[str] = None,
                    conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Add a product to the cart.
    
    Args:
        product_data: Product data to add
        user_id: Optional user ID
        session_id: Optional session ID
        conversation_id: Optional conversation ID
        
    Returns:
        Dict with cart operation result
    """
    try:
        logger.info(f"Adding product to cart for {'user' if user_id else 'session'} "
                    f"{user_id or session_id}")
        
        # Get agent instance
        agent = get_agent()
        
        # Find the cart management tool
        cart_tool = None
        for tool in agent.tools:
            if tool.name == "cart_management":
                cart_tool = tool
                break
        
        if not cart_tool:
            raise ValueError("Cart management tool not found")
        
        # Call the tool directly
        result = await cart_tool.func(
            action="add",
            user_id=user_id,
            session_id=session_id,
            product_data=product_data,
            conversation_id=conversation_id
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error adding to cart: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'cart_items': []
        }

async def view_cart(user_id: Optional[str] = None,
                  session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    View the cart contents.
    
    Args:
        user_id: Optional user ID
        session_id: Optional session ID
        
    Returns:
        Dict with cart contents
    """
    try:
        logger.info(f"Viewing cart for {'user' if user_id else 'session'} "
                    f"{user_id or session_id}")
        
        # Get agent instance
        agent = get_agent()
        
        # Find the cart management tool
        cart_tool = None
        for tool in agent.tools:
            if tool.name == "cart_management":
                cart_tool = tool
                break
        
        if not cart_tool:
            raise ValueError("Cart management tool not found")
        
        # Call the tool directly
        result = await cart_tool.func(
            action="view",
            user_id=user_id,
            session_id=session_id
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error viewing cart: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'cart_items': []
        }

async def remove_from_cart(product_indices: List[int],
                         user_id: Optional[str] = None,
                         session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Remove products from the cart.
    
    Args:
        product_indices: Indices of products to remove
        user_id: Optional user ID
        session_id: Optional session ID
        
    Returns:
        Dict with operation result
    """
    try:
        logger.info(f"Removing products {product_indices} from cart for "
                    f"{'user' if user_id else 'session'} {user_id or session_id}")
        
        # Get agent instance
        agent = get_agent()
        
        # Find the cart management tool
        cart_tool = None
        for tool in agent.tools:
            if tool.name == "cart_management":
                cart_tool = tool
                break
        
        if not cart_tool:
            raise ValueError("Cart management tool not found")
        
        # Call the tool directly
        result = await cart_tool.func(
            action="remove",
            user_id=user_id,
            session_id=session_id,
            product_indices=product_indices
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error removing from cart: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'cart_items': []
        }
