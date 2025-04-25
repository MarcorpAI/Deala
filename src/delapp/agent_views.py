"""
ShopAgent Django Views

This module provides Django views that interface with the ShopAgent architecture,
handling user queries and conversation management.
"""
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
import json
import logging
import asyncio
from django.utils import timezone
from django.conf import settings

from .models import Conversation, ConversationMessage, ConversationState
from .agent.api import process_query

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def agent_query_view(request):
    """
    Process a user query using the agent-based architecture
    
    POST parameters:
    - query: User's natural language query
    - conversation_id: (Optional) ID of the conversation
    - session_id: (Optional) Session ID for anonymous users
    """
    try:
        # Extract data from request
        data = request.data
        query = data.get('query', '').strip()
        conversation_id = data.get('conversation_id')
        session_id = data.get('session_id') or request.COOKIES.get('sessionid')
        
        # Get user ID if authenticated
        user_id = str(request.user.id) if request.user.is_authenticated else None
        
        # Validate query
        if not query:
            return Response({
                'success': False,
                'error': 'No query provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process the query
        result = asyncio.run(process_query(
            query=query,
            conversation_id=conversation_id,
            user_id=user_id,
            session_id=session_id
        ))
        
        # Extract response data
        response_data = {
            'success': True,
            'message': result.get('response', ''),
            'conversation_id': result.get('conversation_id') or conversation_id,
            'products': result.get('products', []),
            'followup_questions': result.get('followup_questions', []),
        }
        
        # Include debug info if in debug mode
        if settings.DEBUG and 'intermediate_steps' in result:
            response_data['debug'] = {
                'intermediate_steps': result['intermediate_steps']
            }
        
        # Create response
        response = Response(response_data)
        
        # Set session cookie if needed
        if session_id and not request.user.is_authenticated:
            response.set_cookie('sessionid', session_id, max_age=86400*30)
        
        return response
    
    except Exception as e:
        logger.error(f"Error in agent_query_view: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
            'message': "I encountered an error while processing your request. Please try again.",
            'conversation_id': conversation_id
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_conversations_view(request):
    """
    Get the user's conversation history
    """
    try:
        # Only return conversations for authenticated users
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'error': 'Authentication required',
                'conversations': []
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get all active conversations for the user
        conversations = Conversation.objects.filter(user=request.user, active=True).order_by('-updated_at')
        
        # Format the conversations
        formatted_conversations = [
            {
                'id': str(conversation.id),
                'title': conversation.title or f"Conversation {idx+1}",
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat()
            }
            for idx, conversation in enumerate(conversations)
        ]
        
        return Response({
            'success': True,
            'conversations': formatted_conversations
        })
    
    except Exception as e:
        logger.error(f"Error in get_conversations_view: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
            'conversations': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_conversation_messages_view(request, conversation_id):
    """
    Get messages for a specific conversation
    """
    try:
        # Find the conversation
        try:
            # For authenticated users, ensure the conversation belongs to them
            if request.user.is_authenticated:
                conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            else:
                conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Conversation not found',
                'messages': []
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all messages for the conversation
        messages = ConversationMessage.objects.filter(conversation=conversation).order_by('created_at')
        
        # Format the messages
        formatted_messages = [
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
        
        # Get conversation state
        try:
            state = ConversationState.objects.get(conversation=conversation)
            current_products = state.current_products
        except ConversationState.DoesNotExist:
            current_products = []
        
        return Response({
            'success': True,
            'conversation_id': conversation_id,
            'messages': formatted_messages,
            'current_products': current_products
        })
    
    except Exception as e:
        logger.error(f"Error in get_conversation_messages_view: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
            'messages': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
