from django.db import models
from django.conf import settings

class SiteSettings(models.Model):
    programme_name = models.CharField(max_length=120, default='BFS Mentorship Programme')
    contact_email = models.EmailField(blank=True, default='contact@bfs-platform.org')
    management_can_review = models.BooleanField(default=False, help_text="Enable if Management Team is allowed to grade tasks")

    class Meta:
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.programme_name


class Recognition(models.Model):
    """
    Wall of Fame / Recognition system: Mentee of the Month, Mentor of the Month, Hall of Fame.
    """
    TYPE_CHOICES = [
        ('mentee_of_month', 'Mentee of the Month'),
        ('mentor_of_month', 'Mentor of the Month'),
        ('hall_of_fame', 'Hall of Fame Inductee'),
    ]

    from django.conf import settings
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recognitions')
    type = models.CharField(max_length=25, choices=TYPE_CHOICES, default='mentee_of_month')
    period = models.CharField(max_length=40, help_text="e.g. October 2026")
    badge_title = models.CharField(max_length=100, default="Excellence in Fellowship")
    note = models.TextField(blank=True, help_text="Commendation and citation")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_type_display()}: {self.user.username} ({self.period})"