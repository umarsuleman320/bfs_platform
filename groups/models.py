from django.db import models
from django.conf import settings

class Group(models.Model):
    JOIN_CHOICES = [('open', 'Open'), ('approval', 'Approval Required'), ('closed', 'Closed')]
    STATUS_CHOICES = [('active', 'Active'), ('archived', 'Archived')]

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(default=20)
    join_status = models.CharField(max_length=15, choices=JOIN_CHOICES, default='approval')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='mentored_groups'
    )
    
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='coordinated_groups'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    # ADVANCED LOGIC: Dynamic counting
    @property
    def member_count(self):
        return self.memberships.count()

    @property
    def remaining_slots(self):
        return max(0, self.capacity - self.member_count)

    @property
    def is_full(self):
        return self.member_count >= self.capacity

class GroupMembership(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_membership')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')

class JoinRequest(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='join_requests')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Pairing(models.Model):
    """
    Independent mentor-mentee pairing record.
    Supports 1-to-1 and 1-to-many pairings within research groups or programmes.
    """
    STATUS_CHOICES = [('active', 'Active'), ('terminated', 'Terminated')]

    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_pairings')
    mentee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentee_pairings')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='pairings')
    pairing_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_pairings')
    terminated_at = models.DateTimeField(null=True, blank=True)
    termination_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-pairing_date']

    def __str__(self):
        return f"{self.mentor.username} ↔ {self.mentee.username} ({self.status})"


class Meeting(models.Model):
    """
    Mentorship meeting session scheduled by Admin, Mentor, or confirmed from a Mentee request.
    Stores external platform URL (e.g. Microsoft Teams, Zoom, Google Meet).
    """
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    pairing = models.ForeignKey(Pairing, on_delete=models.SET_NULL, null=True, blank=True, related_name='meetings')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='group_meetings')
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_meetings')
    mentee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='mentee_meetings')
    title = models.CharField(max_length=200)
    agenda = models.TextField(blank=True)
    meeting_date = models.DateField()
    meeting_time = models.TimeField()
    meeting_platform = models.CharField(max_length=80, default='Microsoft Teams', help_text="e.g. Microsoft Teams, Zoom, Google Meet")
    meeting_link = models.URLField(verbose_name="Meeting Link")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='meetings_scheduled')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['meeting_date', 'meeting_time']

    def __str__(self):
        return f"{self.title} on {self.meeting_date} ({self.get_status_display()})"


class MeetingRequest(models.Model):
    """
    Mentee-initiated meeting request with an assigned mentor.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    pairing = models.ForeignKey(Pairing, on_delete=models.SET_NULL, null=True, blank=True, related_name='meeting_requests')
    mentee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requested_meetings')
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_meeting_requests')
    topic = models.CharField(max_length=200)
    agenda = models.TextField(blank=True)
    proposed_date = models.DateField()
    proposed_time = models.TimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Request by {self.mentee.username}: {self.topic} ({self.get_status_display()})"