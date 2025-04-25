from django.contrib import admin
from .models import UserQuery, CustomUser, UserSubscription
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from products.models import StoredProduct
# Register your models here.

admin.site.register(UserQuery)
admin.site.register(UserSubscription)
admin.site.register(StoredProduct)



# admin.site.register(Waitlist)


class CustomUserAdmin(UserAdmin):
    # Define the fields that will be used in the admin interface
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Verification'), {'fields': ('email_verified', 'verification_token')}),
        # (_('Important dates'), {'fields': ('last_login', )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'email_verified', 'verification_token')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)
