from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Q, Max
from .models import AuditLog, PointsRule

def create_audit_log(user, action, details=""):
    """
    Creates a permanent system record of an action for accountability.
    Usage: create_audit_log(request.user, "Group Deleted", "Deleted track Unit A")
    """
    AuditLog.objects.create(user=user, action=action, details=details)

def get_at_risk_mentees():
    """
    SUPREME DEFINITION OF 'AT-RISK':
    1. A fellow who has 2 or more 'Overdue' tasks.
    2. OR a fellow who hasn't submitted ANY work in the last 10 days.
    This uses advanced annotations to keep the dashboard fast.
    """
    from accounts.models import User # Local import to prevent circular errors
    
    ten_days_ago = timezone.now() - timedelta(days=10)
    
    return User.objects.filter(role='mentee').annotate(
        overdue_count=Count(
            'my_assignments', 
            filter=Q(my_assignments__status='overdue')
        ),
        last_submission_date=Max('my_assignments__submissions__submitted_at')
    ).filter(
        Q(overdue_count__gte=2) | 
        Q(last_submission_date__lt=ten_days_ago) | 
        Q(last_submission_date__isnull=True, date_joined__lt=ten_days_ago)
    ).distinct()

def get_consistency_streak(user):
    """
    Calculates the 'On-Time' streak for a fellow.
    Returns the number of consecutive 'completed' tasks before the first 
    'overdue' or 'resubmission' break.
    """
    assignments = user.my_assignments.all().order_by('-assigned_at')
    streak = 0
    for a in assignments:
        if a.status == 'completed':
            streak += 1
        elif a.status == 'todo':
            continue # Haven't reached this yet, don't break streak
        else:
            break # Streak broken by overdue or resubmission
    return streak

def award_bonus_points(user, action_key):
    """
    Allows the system to award bonus XP based on the PointsRule table.
    Usage: award_bonus_points(mentee, 'on_time_bonus')
    """
    try:
        rule = PointsRule.objects.get(action_key=action_key, is_active=True)
        # In a real scenario, you might save these to a specific 'Bonus' model
        # For now, we use AuditLog to track that points were 'earned'
        create_audit_log(user, "Bonus XP Earned", f"Earned {rule.points} XP for {rule.label}")
        return rule.points
    except PointsRule.DoesNotExist:
        return 0