from django.contrib import admin
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include("delapp.urls")),
    path('accounts/', include('allauth.urls')),
    path('api-auth/', include('rest_framework.urls')),

    
]
