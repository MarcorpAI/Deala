from django.urls import path
from . import views
from .views import VerifyEmailView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


from .views import user_query_api_view, CreateUserView

urlpatterns = [
    path("api/user-query/", user_query_api_view, name="query_view"),


    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # path("api/register-user/", register_user, name="register"),
    path("api/register-user/", CreateUserView.as_view(), name="register"),

    path('api/create-checkout/', views.create_checkout_view, name='create_checkout'),
    path('api/lemon-squeezy-webhook/', views.lemon_squeezy_webhook, name='lemon_squeezy_webhook'),
    path('api/check-subscription/', views.check_subscription, name='check_subscription'),

    ############ ALLLAUTH URLS ######
    path('api/verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify_email'),

]
