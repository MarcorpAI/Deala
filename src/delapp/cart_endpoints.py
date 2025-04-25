"""
Cart API Endpoints

This module provides RESTful API endpoints for cart operations, including adding, viewing,
and removing items from the shopping cart.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
import json
import logging
import asyncio

from .agent.api import add_to_cart, view_cart, remove_from_cart

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def add_to_cart_view(request):
    """
    Add a product to the cart
    
    POST parameters:
    - product_data: Product information to add to cart
    - session_id: (Optional) Session ID for anonymous users
    - conversation_id: (Optional) ID of the conversation
    """
    try:
        # Extract data from request
        data = request.data
        product_data = data.get('product_data', {})
        session_id = data.get('session_id') or request.COOKIES.get('sessionid')
        conversation_id = data.get('conversation_id')
        
        # Get user ID if authenticated
        user_id = str(request.user.id) if request.user.is_authenticated else None
        
        # Validate product data
        if not product_data or not isinstance(product_data, dict):
            return Response({
                'success': False,
                'error': 'Invalid product data'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure we have either user_id or session_id
        if not user_id and not session_id:
            return Response({
                'success': False,
                'error': 'No user ID or session ID provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add to cart
        result = asyncio.run(add_to_cart(
            product_data=product_data,
            user_id=user_id,
            session_id=session_id,
            conversation_id=conversation_id
        ))
        
        # Create response with session ID if provided
        response = Response(result)
        
        # Set session cookie if we have a new session ID
        if result.get('session_id') and not request.user.is_authenticated:
            response.set_cookie('sessionid', result['session_id'], max_age=86400*30)
        
        return response
    
    except Exception as e:
        logger.error(f"Error in add_to_cart_view: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def view_cart_view(request):
    """
    View the current cart contents
    
    GET/POST parameters:
    - session_id: (Optional) Session ID for anonymous users
    """
    try:
        # Extract data from request
        if request.method == 'POST':
            data = request.data
            session_id = data.get('session_id')
        else:
            session_id = request.GET.get('session_id')
        
        # Try cookie if no session ID provided
        if not session_id:
            session_id = request.COOKIES.get('sessionid')
        
        # Get user ID if authenticated
        user_id = str(request.user.id) if request.user.is_authenticated else None
        
        # Ensure we have either user_id or session_id
        if not user_id and not session_id:
            return Response({
                'success': False,
                'error': 'No user ID or session ID provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # View cart
        result = asyncio.run(view_cart(
            user_id=user_id,
            session_id=session_id
        ))
        
        return Response(result)
    
    except Exception as e:
        logger.error(f"Error in view_cart_view: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
            'cart_items': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def remove_from_cart_view(request):
    """
    Remove item(s) from the cart
    
    POST parameters:
    - product_indices: List of indices to remove from cart
    - session_id: (Optional) Session ID for anonymous users
    """
    try:
        # Extract data from request
        data = request.data
        product_indices = data.get('product_indices', [])
        session_id = data.get('session_id') or request.COOKIES.get('sessionid')
        
        # Get user ID if authenticated
        user_id = str(request.user.id) if request.user.is_authenticated else None
        
        # Validate indices
        if not product_indices or not isinstance(product_indices, list):
            return Response({
                'success': False,
                'error': 'Invalid product indices'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure we have either user_id or session_id
        if not user_id and not session_id:
            return Response({
                'success': False,
                'error': 'No user ID or session ID provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove from cart
        result = asyncio.run(remove_from_cart(
            product_indices=product_indices,
            user_id=user_id,
            session_id=session_id
        ))
        
        return Response(result)
    
    except Exception as e:
        logger.error(f"Error in remove_from_cart_view: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
            'cart_items': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
