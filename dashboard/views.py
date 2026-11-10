from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Count
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.permissions import role_required
from groups.models import Group, GroupMembership, JoinRequest, Pairing, Meeting, MeetingRequest
from tasks.models import Task, TaskAssignment, Submission
from progress.models import PointsRule, Escalation, Goal, Achievement, AuditLog
from announcements.models import Announcement
from helpdesk.models import HelpRequest
from core.models import Recognition
from progress.services import get_at_risk_mentees, get_consistency_streak

User = get_user_model()

def get_greeting():
    """Professional time-based greeting for welcome banners."""
    hour = timezone.now().hour
    if hour < 12:
        return "Good Morning"
    elif 12 <= hour < 16:
        return "Good Afternoon"
    else:
        return "Good Evening"

@login_required
def dashboard_home(request):
    """Supreme funnel logic: Strictly directs roles to their terminals."""
    if request.user.role == 'mentee':
        return redirect('dashboard:mentee_dashboard')
    elif request.user.role == 'mentor':
        return redirect('dashboard:mentor_dashboard')
    elif request.user.role == 'management':
        return redirect('dashboard:management_dashboard')
    elif request.user.role == 'coordinator':
        return redirect('dashboard:coordinator_dashboard')
    return redirect('accounts:login')

@role_required('mentee')
def mentee_dashboard(request):
    user = request.user
    today = timezone.now().date()
    
    # 1. Enrolments & Mentor Pairing
    memberships = GroupMembership.objects.filter(user=user).select_related('group', 'group__mentor')
    pending_requests = JoinRequest.objects.filter(user=user, status='pending')
    active_pairing = Pairing.objects.filter(mentee=user, status='active').select_related('mentor').first()

    # 2. XP & Rank Calculation
    total_xp = user.my_assignments.aggregate(
        total=Coalesce(Sum('submissions__review__score'), 0)
    )['total']

    all_mentee_scores = User.objects.filter(role='mentee').annotate(
        score_sum=Coalesce(Sum('my_assignments__submissions__review__score'), 0)
    )
    my_rank = all_mentee_scores.filter(score_sum__gt=total_xp).count() + 1

    # 3. Tasks & Progress
    my_tasks = TaskAssignment.objects.filter(mentee=user).select_related('task')
    total_assigned = my_tasks.count()
    completed_count = my_tasks.filter(status='completed').count()
    progress_percentage = int((completed_count / total_assigned * 100)) if total_assigned > 0 else 0

    # 4. Goals & Achievements
    goals = Goal.objects.filter(mentee=user).order_by('-created_at')[:4]
    verified_achievements = Achievement.objects.filter(mentee=user, status='verified').count()

    # 5. Upcoming Sessions & Announcements
    upcoming_meetings = Meeting.objects.filter(mentee=user, status='scheduled', meeting_date__gte=today).order_by('meeting_date', 'meeting_time')[:3]
    recent_announcements = Announcement.objects.filter(
        Q(audience__in=['all', 'mentees']) | Q(is_priority=True)
    ).order_by('-is_priority', '-created_at')[:3]
    open_tickets = HelpRequest.objects.filter(mentee=user, status__in=['open', 'in_progress', 'awaiting_mentee']).count()

    context = {
        'greeting': get_greeting(),
        'memberships': memberships,
        'pending_requests': pending_requests,
        'active_pairing': active_pairing,
        'my_tasks': my_tasks.order_by('task__deadline')[:5],
        'goals': goals,
        'upcoming_meetings': upcoming_meetings,
        'recent_announcements': recent_announcements,
        'open_tickets_count': open_tickets,
        'stats': {
            'points': total_xp,
            'rank': my_rank,
            'streak': get_consistency_streak(user),
            'completed': completed_count,
            'total_assigned': total_assigned,
            'todo': my_tasks.filter(status__in=['todo', 'resubmission']).count(),
            'overdue': my_tasks.filter(status='overdue').count(),
            'progress': progress_percentage,
            'achievements': verified_achievements,
        }
    }
    return render(request, 'dashboard/mentee.html', context)

@role_required('mentor')
def mentor_dashboard(request):
    user = request.user
    today = timezone.now().date()

    my_groups = Group.objects.filter(mentor=user, status='active')
    group_ids = my_groups.values_list('id', flat=True)
    
    # Paired fellows
    my_pairings = Pairing.objects.filter(mentor=user, status='active').select_related('mentee', 'group')
    mentee_ids = my_pairings.values_list('mentee_id', flat=True)

    # Submission Queue: ungraded work
    pending_submissions = Submission.objects.filter(
        assignment__task__assigned_by=user
    ).exclude(review__isnull=False).select_related('assignment', 'assignment__task', 'assignment__mentee')

    # Risk Engine
    at_risk_list = get_at_risk_mentees().filter(
        Q(group_membership__group_id__in=group_ids) | Q(id__in=mentee_ids)
    ).distinct()

    # Meetings & Requests
    upcoming_meetings = Meeting.objects.filter(mentor=user, status='scheduled', meeting_date__gte=today).order_by('meeting_date', 'meeting_time')[:3]
    pending_meeting_requests = MeetingRequest.objects.filter(mentor=user, status='pending').count()

    # Pending achievements for paired mentees
    pending_achievements = Achievement.objects.filter(mentee_id__in=mentee_ids, status='pending').count()
    open_tickets = HelpRequest.objects.filter(assigned_to=user, status__in=['open', 'in_progress']).count()

    context = {
        'greeting': get_greeting(),
        'my_groups': my_groups,
        'my_pairings': my_pairings,
        'pending_submissions': pending_submissions[:5],
        'pending_reviews_count': pending_submissions.count(),
        'at_risk_count': at_risk_list.count(),
        'upcoming_meetings': upcoming_meetings,
        'pending_meeting_requests_count': pending_meeting_requests,
        'pending_achievements_count': pending_achievements,
        'open_tickets_count': open_tickets,
        'is_leader': my_groups.exists() or my_pairings.exists(),
    }
    return render(request, 'dashboard/mentor.html', context)

@role_required('management')
def management_dashboard(request):
    total_mentees = User.objects.filter(role='mentee').count()
    total_mentors = User.objects.filter(role='mentor').count()
    total_assignments = TaskAssignment.objects.count()
    total_completed = TaskAssignment.objects.filter(status='completed').count()
    global_completion_rate = int((total_completed / total_assignments * 100)) if total_assignments > 0 else 0

    global_at_risk = get_at_risk_mentees().count()
    pending_reviews = Submission.objects.exclude(review__isnull=False).count()
    open_escalations = Escalation.objects.filter(status='open').count()
    active_pairings = Pairing.objects.filter(status='active').count()

    context = {
        'greeting': get_greeting(),
        'total_groups': Group.objects.count(),
        'active_groups': Group.objects.filter(status='active').count(),
        'total_mentees': total_mentees,
        'total_mentors': total_mentors,
        'active_pairings': active_pairings,
        'completion_rate': global_completion_rate,
        'at_risk_count': global_at_risk,
        'pending_reviews_count': pending_reviews,
        'open_escalations_count': open_escalations,
        'global_inbox': JoinRequest.objects.filter(status='pending').order_by('-created_at')[:5],
        'recent_logs': AuditLog.objects.all()[:5],
    }
    return render(request, 'dashboard/management.html', context)

@role_required('coordinator')
def coordinator_dashboard(request):
    """The Operational Command terminal."""
    recent_groups = Group.objects.all().order_by('-created_at')[:6]
    pending_requests = JoinRequest.objects.filter(status='pending').select_related('user', 'group')
    active_pairings = Pairing.objects.filter(status='active').count()
    total_users = User.objects.count()
    
    context = {
        'greeting': get_greeting(),
        'recent_groups': recent_groups,
        'pending_requests': pending_requests,
        'active_pairings_count': active_pairings,
        'total_users': total_users,
        'recent_logs': AuditLog.objects.all()[:6],
    }
    return render(request, 'dashboard/coordinator.html', context)