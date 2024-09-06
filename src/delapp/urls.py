from django.urls import path
from . import views

from .views import user_query_api_view

urlpatterns = [
    path("api/user-query/", user_query_api_view, name="query_view"),
    path('api/waitlist/submit/', views.waitlist_submit, name='waitlist_submit'),
    path('api/waitlist/url/', views.get_waitlist_url, name='get_waitlist_url'),

]
