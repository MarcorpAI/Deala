"""
Base Memory Interface for ShopAgent

This module defines the base class for all memory components used by the ShopAgent.
Memory components handle persistent storage and retrieval of conversation context.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union

class BaseMemory(ABC):
    """Base class for all ShopAgent memory components"""
    
    def __init__(self, name: str):
        """
        Initialize a memory component with a name.
        
        Args:
            name: Memory component name
        """
        self.name = name
    
    @abstractmethod
    async def save(self, data: Dict[str, Any]) -> bool:
        """
        Save data to memory.
        
        Args:
            data: Data to save to memory
            
        Returns:
            Boolean indicating success
        """
        pass
    
    @abstractmethod
    async def load(self, **kwargs) -> Dict[str, Any]:
        """
        Load data from memory.
        
        Args:
            **kwargs: Parameters for loading specific data
            
        Returns:
            Dict containing the loaded data
        """
        pass
    
    @abstractmethod
    async def update(self, data: Dict[str, Any], **kwargs) -> bool:
        """
        Update existing data in memory.
        
        Args:
            data: New data to update
            **kwargs: Parameters specifying what to update
            
        Returns:
            Boolean indicating success
        """
        pass
    
    @abstractmethod
    async def clear(self, **kwargs) -> bool:
        """
        Clear data from memory.
        
        Args:
            **kwargs: Parameters specifying what to clear
            
        Returns:
            Boolean indicating success
        """
        pass
