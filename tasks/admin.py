from django.contrib import admin
from .models import Task, TaskAssignment, Submission, Review

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'target_type', 'deadline', 'assigned_by')

@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ('task', 'mentee', 'status')
    list_filter = ('status',)

admin.site.register(Submission)
admin.site.register(Review)