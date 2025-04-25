"""
URL patterns for the ShopAgent architecture

This module defines URL patterns for accessing the agent-based views
and cart functionality.
"""
from django.urls import path
from . import agent_views
from . import cart_endpoints

# ShopAgent URLs
urlpatterns = [
    # Conversation API
    path('api/agent/query/', agent_views.agent_query_view, name='agent_query'),
    path('api/conversations/', agent_views.get_conversations_view, name='get_conversations'),
    path('api/conversations/<str:conversation_id>/messages/', 
         agent_views.get_conversation_messages_view, name='get_conversation_messages'),
    
    # Cart API
    path('api/cart/add/', cart_endpoints.add_to_cart_view, name='add_to_cart'),
    path('api/cart/view/', cart_endpoints.view_cart_view, name='view_cart'),
    path('api/cart/remove/', cart_endpoints.remove_from_cart_view, name='remove_from_cart'),
]
