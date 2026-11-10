from django.contrib import admin
from .models import Group

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    # This controls which columns you see in the list view
    list_display = ('name', 'join_status', 'capacity', 'status', 'created_at')
    
    # This adds a sidebar to filter groups by status or join type
    list_filter = ('status', 'join_status')
    
    # This allows you to search groups by name
    search_fields = ('name',)