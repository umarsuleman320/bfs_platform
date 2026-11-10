from django.urls import path
from . import views

app_name = 'progress'

urlpatterns = [
    # Global Fellow Rankings
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    
    # Private Goal Management
    path('goals/', views.mentee_goals, name='goals'),
    path('goals/add/', views.add_goal, name='add_goal'),
    path('goals/<int:goal_id>/toggle/', views.toggle_goal, name='toggle_goal'),
    
    # Mentor/Management Escalations
    path('escalations/', views.escalation_list, name='escalation_list'),
    path('escalate/<int:mentee_id>/', views.raise_escalation, name='raise_escalation'),
    path('escalations/<int:escalation_id>/resolve/', views.resolve_escalation, name='resolve_escalation'),

    # Security Audit & At-Risk Engine
    path('audit-log/', views.audit_log_view, name='audit_log'),
    path('at-risk/', views.at_risk_directory, name='at_risk_list'),

    # Achievements & Milestones
    path('achievements/', views.achievements_list, name='achievements'),
    path('achievements/submit/', views.submit_achievement, name='submit_achievement'),
    path('achievements/<int:achievement_id>/review/', views.review_achievement, name='review_achievement'),

    # Feedback & Evaluation
    path('feedback/', views.feedback_list, name='feedback'),
    path('feedback/submit/', views.submit_feedback, name='submit_feedback'),

    # Points Rule Configurator (Management/Coordinator)
    path('points-rules/', views.points_rules_admin, name='points_rules'),
]