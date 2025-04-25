"""
Base Tool Interface for ShopAgent

This module defines the base class for all tools used by the ShopAgent.
Each tool provides specific functionality that the agent can use to solve user queries.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union


class BaseTool(ABC):
    """Base class for all ShopAgent tools"""
    
    def __init__(self, name: str, description: str):
        """
        Initialize a tool with a name and description.
        
        Args:
            name: Tool name used by the agent to refer to this tool
            description: Tool description explaining when and how to use this tool
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool's functionality.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Dict containing the tool's results and any relevant metadata
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the schema for this tool's required parameters and return types.
        
        Returns:
            Dict describing the tool's parameters and return value schemas
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema(),
            "returns": self._get_returns_schema()
        }
    
    @abstractmethod
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """
        Define the parameters schema for this tool.
        
        Returns:
            Dict describing the parameters expected by this tool
        """
        pass
    
    @abstractmethod
    def _get_returns_schema(self) -> Dict[str, Any]:
        """
        Define the return value schema for this tool.
        
        Returns:
            Dict describing the return values provided by this tool
        """
        pass
