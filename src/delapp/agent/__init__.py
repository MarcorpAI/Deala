"""ShopAgent Architecture

This package provides the agentic shopping assistant architecture for Deala,
implementing a modular and flexible approach to handling user queries and cart operations.

Components include:
- Core agent architecture
- Specialized tools
- Memory management
- Response generation
"""

from .shop_agent_factory import ShopAgentFactory
from .core.agent_core import ShopAgent
from .tools.base_tool import BaseTool
from .memory.base_memory import BaseMemory
from .api import process_query, add_to_cart, view_cart, remove_from_cart

__all__ = [
    'ShopAgentFactory',
    'ShopAgent',
    'BaseTool',
    'BaseMemory',
    'process_query',
    'add_to_cart',
    'view_cart',
    'remove_from_cart'
]