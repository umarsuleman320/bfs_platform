from django.db import models
from django.conf import settings

class Announcement(models.Model):
    AUDIENCE_CHOICES = [
        ('all', 'All Fellows & Faculty'),
        ('mentees', 'Mentees Only'),
        ('mentors', 'Mentors Only'),
        ('group', 'Specific Research Track'),
    ]

    title = models.CharField(max_length=150)
    message = models.TextField()
    audience = models.CharField(max_length=15, choices=AUDIENCE_CHOICES, default='all')
    group = models.ForeignKey('groups.Group', on_delete=models.SET_NULL, null=True, blank=True)
    is_priority = models.BooleanField(default=False, help_text="Priority announcements are highlighted across all dashboards")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_priority', '-created_at']

    def __str__(self):
        return f"{'[PRIORITY] ' if self.is_priority else ''}{self.title} ({self.created_at.strftime('%Y-%m-%d')})"
