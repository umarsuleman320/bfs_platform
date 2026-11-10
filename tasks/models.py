from django.db import models
from django.conf import settings
from groups.models import Group

class Task(models.Model):
    TARGET_CHOICES = [
        ('individual', 'Individual'),
        ('selected', 'Selected Mentees'),
        ('group', 'Entire Group'),
        ('population', 'Wider Population'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    # Fixed: Changed 'placeholder' to 'help_text'
    category = models.CharField(
        max_length=80, 
        blank=True, 
        help_text="e.g. Research, Coding, Design"
    )
    resources = models.TextField(blank=True, help_text="Links to helpful reading materials")
    submission_rules = models.TextField(blank=True, help_text="Specific rules for this submission")
    deadline = models.DateTimeField()
    points_possible = models.PositiveIntegerField(default=20)
    
    target_type = models.CharField(max_length=12, choices=TARGET_CHOICES)
    target_group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    selected_mentees = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='specially_assigned_tasks')
    
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='tasks_created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class TaskAssignment(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'), 
        ('submitted', 'Submitted'), 
        ('completed', 'Completed'),
        ('overdue', 'Overdue'), 
        ('resubmission', 'Resubmission Required'),
    ]
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments')
    mentee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='my_assignments')
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='todo')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('task', 'mentee')

    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.status in ['todo', 'resubmission'] and self.task.deadline < timezone.now()

    @property
    def latest_submission(self):
        return self.submissions.order_by('-submitted_at').first()

class Submission(models.Model):
    assignment = models.ForeignKey(TaskAssignment, on_delete=models.CASCADE, related_name='submissions')
    onedrive_link = models.URLField(verbose_name="OneDrive/SharePoint URL")
    mentee_notes = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.assignment.mentee.username} - {self.assignment.task.title} (v{self.version})"

class Review(models.Model):
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    score = models.PositiveIntegerField() 
    feedback = models.TextField(blank=True)
    requires_resubmission = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(auto_now_add=True)