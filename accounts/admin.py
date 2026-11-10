from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# This tells Django to use our custom User model in the admin site
# and to show the 'role' field when editing a user
class CustomUserAdmin(UserAdmin):
    model = User
    # This adds the 'role' and 'avatar_url' fields to the admin interface
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'avatar_url', 'linkedin_url', 'github_url', 'cv_url', 'social_url', 'is_verified')}),
    )
    # This shows the 'role' in the list of users
    list_display = ['username', 'email', 'role', 'is_staff']

admin.site.register(User, CustomUserAdmin)