from django.db import models
from django.conf import settings

class Goal(models.Model):
    """Private objectives set by Mentees for their own growth."""
    STATUS_CHOICES = [
        ('active', 'Active'), 
        ('completed', 'Completed'), 
        ('abandoned', 'Abandoned')
    ]
    mentee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='personal_goals')
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    is_private = models.BooleanField(default=True) # Per brief: Private by default
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.mentee.username} - {self.title}"

class PointsRule(models.Model):
    """
    Configurable points logic. 
    Example: action='task_completed', points=50
    Management can change these values anytime.
    """
    action_key = models.CharField(max_length=80, unique=True, help_text="Unique key like 'task_on_time'")
    label = models.CharField(max_length=120) # Human readable name
    points = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.label} ({self.points} XP)"

class Escalation(models.Model):
    """Mentor flags for disengaged or defaulting mentees."""
    STATUS_CHOICES = [
        ('open', 'Open Investigation'), 
        ('reviewing', 'Under Management Review'), 
        ('resolved', 'Resolved')
    ]
    mentee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='escalations')
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='escalations_raised')
    reason = models.TextField(help_text="Detailed reason for flagging this fellow")
    recommended_action = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Flag: {self.mentee.username} ({self.get_status_display()})"

class AuditLog(models.Model):
    """Immutable record of every important system action for accountability."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255) # e.g. 'Grade Published', 'Group Deleted'
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        return f"{self.timestamp} - {self.user.username}: {self.action}"


class Achievement(models.Model):
    """
    Mentees submit verifiable milestones (Job offers, scholarships, awards, publications, certifications).
    Requires mentor verification before becoming part of verified portfolio.
    """
    CATEGORY_CHOICES = [
        ('employment', 'Employment / Job Offer'),
        ('scholarship', 'Scholarship'),
        ('award', 'Award / Honour'),
        ('publication', 'Published Research Paper'),
        ('certification', 'Professional Certification'),
        ('project', 'Completed Practical Project'),
        ('other', 'Other Milestone'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    mentee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achievements')
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    organisation = models.CharField(max_length=150, blank=True, help_text="e.g. NNPC, Microsoft, University, Journal")
    description = models.TextField(help_text="Detailed description of the achievement")
    achievement_date = models.DateField()
    evidence_link = models.URLField(blank=True, verbose_name="Evidence / Document Link (OneDrive/Web)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_achievements')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-achievement_date']

    def __str__(self):
        return f"{self.mentee.username} - {self.title} ({self.get_status_display()})"


class Feedback(models.Model):
    """
    Permanent, immutable evaluation submitted by mentors and mentees
    on sessions, communication, programme experience, and learning progress.
    """
    CATEGORY_CHOICES = [
        ('session', 'Mentorship Session Feedback'),
        ('communication', 'Communication & Collaboration'),
        ('programme', 'Programme Experience & Support'),
        ('learning', 'Learning Progress & Goals'),
        ('general', 'General Satisfaction & Suggestions'),
    ]

    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feedbacks_submitted')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks_received')
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES)
    rating = models.PositiveIntegerField(default=5, help_text="Rating out of 5 stars")
    content = models.TextField(help_text="Constructive feedback (immutable after submission)")
    is_permanent = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback by {self.submitted_by.username} ({self.get_category_display()})"