from django.urls import path, include
from . import views
from .views import VerifyEmailView, CustomTokenObtainPairView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.routers import DefaultRouter
from .cart_views import CartViewSet

from .views import user_query_api_view, CreateUserView

# Set up the router for cart endpoints
cart_router = DefaultRouter()
cart_router.register(r'cart', CartViewSet, basename='cart')

urlpatterns = [
    # Legacy endpoint (will be deprecated)
    path("api/user-query/", user_query_api_view, name="query_view"),
    
    # New agent-based architecture endpoints
    path('', include("delapp.agent_urls")),

    # Authentication endpoints
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("api/register-user/", CreateUserView.as_view(), name="register"),

    # Subscription and checkout endpoints
    path('api/create-checkout/', views.create_checkout_view, name='create_checkout'),
    path('api/lemon-squeezy-webhook/', views.lemon_squeezy_webhook, name='lemon_squeezy_webhook'),
    path('api/check-subscription/', views.check_subscription, name='check_subscription'),

    # Email verification
    path('api/verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify_email'),
    
    # Legacy cart endpoints (will be deprecated)
    path('api/', include(cart_router.urls)),
    
    # Product search endpoint
    path('api/find-deals/', views.find_deals, name='find_deals'),
]
