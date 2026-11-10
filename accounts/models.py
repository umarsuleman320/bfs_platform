from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('mentee', 'Mentee'),
        ('mentor', 'Mentor'),
        ('management', 'Management Team'),
        ('coordinator', 'Programme Coordinator'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='mentee')
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)   # Link to OneDrive/SharePoint photo
    is_verified = models.BooleanField(default=False)

     # Professional Links (Section 10 of Brief: Research Tracker Support)
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn Profile")
    github_url = models.URLField(blank=True, verbose_name="GitHub/Portfolio")
    cv_url = models.URLField(blank=True, verbose_name="CV/Resume (OneDrive Link)")
    # Professional / Academic Background (per BFS Specification)
    qualification = models.CharField(max_length=120, blank=True, help_text="e.g. B.Sc, M.Sc, Ph.D, Professional Fellow")
    expertise = models.CharField(max_length=150, blank=True, help_text="e.g. Software Engineering, AI, Cloud, Research")
    academic_status = models.CharField(max_length=100, blank=True, help_text="e.g. Student, Recent Graduate, Professional")
    interests = models.TextField(blank=True, help_text="Areas of interest or specialization")
    career_goal = models.TextField(blank=True, help_text="Mentee primary career and learning goal")

    def is_mentee(self): return self.role == 'mentee'
    def is_mentor(self): return self.role == 'mentor'
    def is_management(self): return self.role == 'management'
    def is_coordinator(self): return self.role == 'coordinator'
    def can_review(self): return self.role in ('mentor', 'coordinator', 'management')
    def can_manage_groups(self): return self.role in ('coordinator', 'management')

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"