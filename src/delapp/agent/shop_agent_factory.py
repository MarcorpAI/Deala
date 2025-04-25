"""
ShopAgent Factory 

This module provides a factory for creating instances of ShopAgent with all
necessary components properly configured and initialized.
"""
from typing import Dict, Any, Optional, List
import logging

# Import agent core
from .core.agent_core import ShopAgent

# Import tools
from .tools.product_search_tool import ProductSearchTool
from .tools.product_details_tool import ProductDetailsTool
from .tools.cart_management_tool import CartManagementTool

# Import memory components
from .memory.conversation_memory import ConversationMemory

# Import response generator
from .response_generator.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)

class ShopAgentFactory:
    """Factory for creating fully configured ShopAgent instances"""
    
    @staticmethod
    def create_agent(use_llm: bool = True) -> ShopAgent:
        """
        Create and configure a ShopAgent with all required components.
        
        Args:
            use_llm: Whether to initialize with a language model (if False, uses a mock)
            
        Returns:
            Fully configured ShopAgent instance
        """
        logger.info("Creating agentic ShopAgent instance")
        
        # Create LLM if requested
        llm = None
        if use_llm:
            try:
                # Try to import a language model
                try:
                    from langchain_groq import ChatGroq
                    import os
                    
                    api_key = os.environ.get('GROQ_API_KEY')
                    if api_key:
                        llm = ChatGroq(
                            api_key=api_key,
                            model_name="llama3-8b-8192",  # or any other available model
                            temperature=0.2,
                            max_tokens=1024
                        )
                        logger.info("Using Groq LLM")
                except (ImportError, Exception) as e:
                    logger.warning(f"Failed to initialize Groq LLM: {str(e)}")
                    
                    # Try OpenAI as fallback
                    try:
                        from langchain.chat_models import ChatOpenAI
                        
                        api_key = os.environ.get('OPENAI_API_KEY')
                        if api_key:
                            llm = ChatOpenAI(
                                api_key=api_key,
                                model_name="gpt-3.5-turbo",
                                temperature=0.2,
                                max_tokens=1024
                            )
                            logger.info("Using OpenAI LLM")
                    except (ImportError, Exception) as e:
                        logger.warning(f"Failed to initialize OpenAI LLM: {str(e)}")
            except Exception as e:
                logger.error(f"Error initializing LLM: {str(e)}")
        
        # Initialize tools
        try:
            # Create LangChain wrappers
            from .tools.langchain_tools import (
                ProductSearchLangChainTool,
                ProductDetailsLangChainTool,
                CartManagementLangChainTool
            )
            
            # Create tool instances without provider parameter
            langchain_tools = [
                ProductSearchLangChainTool(),
                ProductDetailsLangChainTool(),
                # Skip cart tool for now until we fix the import
                # CartManagementLangChainTool()
            ]
            logger.info(f"Initialized {len(langchain_tools)} LangChain tools")
        except Exception as e:
            logger.error(f"Error initializing tools: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # Create an empty list as fallback
            langchain_tools = []
        
        # Create conversation memory
        memory = ConversationMemory()
        
        # Create agent - the tools are initialized inside the ShopAgent class
        agent = ShopAgent(llm=llm, tools=langchain_tools)
        
        # Register memory component with the agent
        agent.memory_components['conversation_memory'] = memory
        
        logger.info("Agentic ShopAgent instance created successfully")
        return agent
    
    @staticmethod
    def create_response_formatter() -> ResponseFormatter:
        """
        Create a response formatter instance.
        
        Returns:
            ResponseFormatter instance
        """
        return ResponseFormatter()
