# decorators.py
from django.http import HttpResponseForbidden
from .models import UserSubscription

def subscription_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return HttpResponseForbidden("You must be logged in to access this page.")
        try:
            subscription = UserSubscription.objects.get(user=user)
            if not subscription.is_active:
                return HttpResponseForbidden("You must have an active subscription to access this page.")
        except UserSubscription.DoesNotExist:
            return HttpResponseForbidden("You must have an active subscription to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
