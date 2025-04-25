"""
Conversation Memory for ShopAgent

This module provides persistent storage and retrieval of conversation context,
maintaining history of interactions, products mentioned, and user preferences.
"""
from typing import Dict, Any, Optional, List, Union
import logging
from asgiref.sync import sync_to_async
import json

from .base_memory import BaseMemory
from ...models import Conversation, ConversationMessage, ConversationState

logger = logging.getLogger(__name__)

class ConversationMemory(BaseMemory):
    """Memory component for storing and retrieving conversation context"""
    
    def __init__(self):
        """Initialize the conversation memory component"""
        super().__init__(name="conversation_memory")
    
    async def save(self, data: Dict[str, Any]) -> bool:
        """
        Save conversation data.
        
        Args:
            data: Dict containing conversation data to save:
                - conversation_id: ID of existing conversation or None for new
                - user_id: Optional user ID
                - role: Message role ('user' or 'assistant')
                - content: Message content
                - search_results: Optional search results
                - products: Optional product list 
                - state: Optional conversation state to update
            
        Returns:
            Boolean indicating success
        """
        try:
            # Extract key parameters
            conversation_id = data.get('conversation_id')
            user_id = data.get('user_id')
            role = data.get('role', 'user')
            content = data.get('content', '')
            search_results = data.get('search_results')
            products = data.get('products', [])
            
            # Get or create conversation
            conversation = await self._get_or_create_conversation(conversation_id, user_id)
            
            # Save message
            await self._save_message(conversation, role, content, search_results, len(products) > 0)
            
            # Update conversation state if provided
            if 'state' in data and data['state']:
                await self._update_conversation_state(conversation, data['state'], products)
            elif products:
                # If products provided but no explicit state, at least save the products
                await self._update_products_in_state(conversation, products)
            
            return True
        
        except Exception as e:
            logger.error(f"Error saving to conversation memory: {str(e)}", exc_info=True)
            return False
    
    async def load(self, conversation_id: Optional[str] = None, 
                 message_limit: int = 10, 
                 include_state: bool = True,
                 **kwargs) -> Dict[str, Any]:
        """
        Load conversation data.
        
        Args:
            conversation_id: ID of conversation to load
            message_limit: Maximum number of messages to load
            include_state: Whether to include conversation state
            **kwargs: Additional loading parameters
            
        Returns:
            Dict containing the loaded conversation data
        """
        try:
            if not conversation_id:
                return {
                    "success": False,
                    "error": "No conversation ID provided",
                    "messages": [],
                    "state": {}
                }
            
            # Load conversation
            conversation = await self._get_conversation(conversation_id)
            if not conversation:
                return {
                    "success": False,
                    "error": f"Conversation not found: {conversation_id}",
                    "messages": [],
                    "state": {}
                }
            
            # Load messages
            messages = await self._get_messages(conversation, message_limit)
            
            # Load state if requested
            state = {}
            if include_state:
                state = await self._get_conversation_state(conversation)
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "messages": messages,
                "state": state
            }
        
        except Exception as e:
            logger.error(f"Error loading from conversation memory: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "messages": [],
                "state": {}
            }
    
    async def update(self, data: Dict[str, Any], **kwargs) -> bool:
        """
        Update conversation state.
        
        Args:
            data: Dict containing state data to update:
                - conversation_id: ID of conversation to update
                - state: State data to update
            **kwargs: Additional update parameters
            
        Returns:
            Boolean indicating success
        """
        try:
            conversation_id = data.get('conversation_id')
            state_data = data.get('state', {})
            
            if not conversation_id or not state_data:
                return False
            
            # Get conversation
            conversation = await self._get_conversation(conversation_id)
            if not conversation:
                return False
            
            # Update state
            await self._update_conversation_state(conversation, state_data, data.get('products', []))
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating conversation memory: {str(e)}", exc_info=True)
            return False
    
    async def clear(self, conversation_id: Optional[str] = None, **kwargs) -> bool:
        """
        Clear conversation data.
        
        Args:
            conversation_id: ID of conversation to clear
            **kwargs: Additional clearing parameters
            
        Returns:
            Boolean indicating success
        """
        try:
            if not conversation_id:
                return False
            
            # Get conversation
            conversation = await self._get_conversation(conversation_id)
            if not conversation:
                return False
            
            # Clear messages and state
            await self._clear_conversation(conversation)
            
            return True
        
        except Exception as e:
            logger.error(f"Error clearing conversation memory: {str(e)}", exc_info=True)
            return False
    
    @sync_to_async
    def _get_or_create_conversation(self, conversation_id: Optional[str], user_id: Optional[str]) -> Conversation:
        """Get an existing conversation or create a new one"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # If conversation ID provided, try to get it
        if conversation_id:
            try:
                return Conversation.objects.get(id=conversation_id)
            except Conversation.DoesNotExist:
                pass
        
        # Create new conversation
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass
        
        conversation = Conversation.objects.create(user=user)
        
        # Create initial state
        ConversationState.objects.create(conversation=conversation)
        
        return conversation
    
    @sync_to_async
    def _get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID"""
        try:
            return Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return None
    
    @sync_to_async
    def _save_message(self, conversation: Conversation, role: str, content: str, 
                    search_results: Optional[Dict[str, Any]], has_products: bool) -> ConversationMessage:
        """Save a message to the conversation"""
        return ConversationMessage.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            search_results=search_results,
            has_products=has_products
        )
    
    @sync_to_async
    def _get_messages(self, conversation: Conversation, limit: int) -> List[Dict[str, Any]]:
        """Get messages from the conversation"""
        messages = ConversationMessage.objects.filter(conversation=conversation).order_by('created_at')
        
        if limit > 0:
            messages = messages[:limit]
        
        return [
            {
                'id': str(message.id),
                'role': message.role,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'has_products': message.has_products,
                'search_results': message.search_results
            }
            for message in messages
        ]
    
    @sync_to_async
    def _get_conversation_state(self, conversation: Conversation) -> Dict[str, Any]:
        """Get the conversation state"""
        try:
            state = ConversationState.objects.get(conversation=conversation)
            
            # Format state data
            return {
                'current_products': state.current_products,
                'last_query': state.last_query,
                'last_category': state.last_category,
                'applied_filters': state.applied_filters,
                'last_intent': state.last_intent,
                'conversation_turn': state.conversation_turn,
                'product_references': state.product_references,
                'user_preferences': state.user_preferences,
                'keywords': state.keywords,
                'last_action': state.last_action
            }
        except ConversationState.DoesNotExist:
            return {}
    
    @sync_to_async
    def _update_conversation_state(self, conversation: Conversation, 
                                 state_data: Dict[str, Any],
                                 products: List[Dict[str, Any]]) -> None:
        """Update the conversation state"""
        state, created = ConversationState.objects.get_or_create(conversation=conversation)
        
        # Update provided fields
        if 'last_query' in state_data:
            state.last_query = state_data['last_query']
        
        if 'last_category' in state_data:
            state.last_category = state_data['last_category']
        
        if 'applied_filters' in state_data:
            if isinstance(state.applied_filters, dict):
                # Merge with existing filters
                current_filters = state.applied_filters
                current_filters.update(state_data['applied_filters'])
                state.applied_filters = current_filters
            else:
                state.applied_filters = state_data['applied_filters']
        
        if 'last_intent' in state_data:
            state.last_intent = state_data['last_intent']
        
        if 'conversation_turn' in state_data:
            state.conversation_turn = state_data['conversation_turn']
        elif not created:
            # Increment turn count
            state.conversation_turn += 1
        
        if 'product_references' in state_data:
            if isinstance(state.product_references, dict):
                # Merge with existing references
                current_refs = state.product_references
                current_refs.update(state_data['product_references'])
                state.product_references = current_refs
            else:
                state.product_references = state_data['product_references']
        
        if 'user_preferences' in state_data:
            if isinstance(state.user_preferences, dict):
                # Merge with existing preferences
                current_prefs = state.user_preferences
                current_prefs.update(state_data['user_preferences'])
                state.user_preferences = current_prefs
            else:
                state.user_preferences = state_data['user_preferences']
        
        if 'keywords' in state_data:
            # Convert to list if it's a set-like object
            keywords = state_data['keywords']
            if isinstance(keywords, (set, list, tuple)):
                keywords = list(keywords)
            state.keywords = keywords
        
        if 'last_action' in state_data:
            state.last_action = state_data['last_action']
        
        # Update products if provided
        if products:
            state.current_products = products
        
        state.save()
    
    @sync_to_async
    def _update_products_in_state(self, conversation: Conversation, products: List[Dict[str, Any]]) -> None:
        """Update only the products in the conversation state"""
        state, created = ConversationState.objects.get_or_create(conversation=conversation)
        state.current_products = products
        state.save()
    
    @sync_to_async
    def _clear_conversation(self, conversation: Conversation) -> None:
        """Clear all messages and reset state for a conversation"""
        # Delete all messages
        ConversationMessage.objects.filter(conversation=conversation).delete()
        
        # Reset state
        try:
            state = ConversationState.objects.get(conversation=conversation)
            state.current_products = []
            state.last_query = ""
            state.last_category = ""
            state.applied_filters = {}
            state.last_intent = None
            state.conversation_turn = 0
            state.product_references = {}
            state.user_preferences = {}
            state.keywords = []
            state.last_action = None
            state.save()
        except ConversationState.DoesNotExist:
            pass
