from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Sum
from .models import Goal, Escalation, AuditLog, PointsRule
from .services import create_audit_log # Crucial Phase 4 Import
from groups.models import GroupMembership
from django.contrib.auth import get_user_model
from accounts.permissions import role_required
from .services import get_at_risk_mentees


User = get_user_model()

# --- THE SUPREME LEADERBOARD ---
@role_required('mentee', 'mentor', 'management', 'coordinator')
def leaderboard_view(request):
    """
    Calculates points and ranks fellows.
    The template uses these to build the Cinematic Podium.
    """
    # Annotate mentees with their total points from the Review model
    # We look through submissions -> reviews -> scores
    fellows = User.objects.filter(role='mentee').annotate(
        total_xp=Sum('my_assignments__submissions__review__score')
    ).order_by('-total_xp')
    
    context = {
        'fellows': fellows,
        'greeting': "Hall of Fame",
    }
    return render(request, 'progress/leaderboard.html', context)


# --- MENTEE GOAL STRATEGY ---
@role_required('mentee')
def mentee_goals(request):
    """View personal growth milestones."""
    goals = Goal.objects.filter(mentee=request.user).order_by('-created_at')
    return render(request, 'progress/goals.html', {'goals': goals})

@role_required('mentee')
def add_goal(request):
    """Initialize a new private milestone."""
    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            Goal.objects.create(mentee=request.user, title=title)
            messages.success(request, "Personal milestone initialized.")
            
            # Audit the self-improvement action
            create_audit_log(
                user=request.user,
                action="Goal Created",
                details=f"Mentee created private goal: {title}"
            )
    return redirect('progress:goals')

@role_required('mentee')
def toggle_goal(request, goal_id):
    """Flip the status of a personal objective."""
    goal = get_object_or_404(Goal, id=goal_id, mentee=request.user)
    if goal.status == 'active':
        goal.status = 'completed'
        messages.success(request, f"Objective achieved: {goal.title}")
    else:
        goal.status = 'active'
    goal.save()
    return redirect('progress:goals')


# --- ESCALATION CONTROL CENTER ---
@role_required('mentor', 'management', 'coordinator')
def escalation_list(request):
    """
    High-stakes oversight. 
    Coordinators see all flags; Mentors only see those they raised.
    """
    if request.user.role in ['management', 'coordinator']:
        escalations = Escalation.objects.all().select_related('mentee', 'raised_by').order_by('-created_at')
    else:
        escalations = Escalation.objects.filter(raised_by=request.user).select_related('mentee').order_by('-created_at')
    
    return render(request, 'progress/escalations.html', {
        'escalations': escalations,
        'greeting': "Risk Oversight"
    })

@role_required('mentor')
def raise_escalation(request, mentee_id):
    """Mentor flags a fellow for Management intervention."""
    mentee = get_object_or_404(User, id=mentee_id)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        flag = Escalation.objects.create(
            mentee=mentee,
            raised_by=request.user,
            reason=reason
        )
        
        # --- PHASE 4 AUDIT ---
        create_audit_log(
            user=request.user,
            action="System Escalation",
            details=f"Mentor {request.user.username} flagged {mentee.username} for: {reason[:50]}..."
        )
        
        messages.warning(request, f"Flag Raised: {mentee.get_full_name()} has been reported to Management.")
        return redirect('dashboard:home')
        
    return render(request, 'progress/raise_escalation.html', {'mentee': mentee})

@role_required('management', 'coordinator')
def resolve_escalation(request, escalation_id):
    """Allows management to close a case once resolved."""
    flag = get_object_or_404(Escalation, id=escalation_id)
    flag.status = 'resolved'
    flag.save()
    
    # --- PHASE 4 AUDIT ---
    create_audit_log(
        user=request.user,
        action="Escalation Resolved",
        details=f"Case closed for {flag.mentee.username} by {request.user.username}."
    )
    
    messages.success(request, f"Case Resolved: {flag.mentee.username} is back on track.")
    return redirect('progress:escalation_list')


@role_required('coordinator', 'management')
def audit_log_view(request):
    """The 'System Black Box' - View every action taken on the platform."""
    logs = AuditLog.objects.all().select_related('user').order_by('-timestamp')
    return render(request, 'progress/audit_log.html', {
        'logs': logs,
        'greeting': "Security Audit"
    })
    

@role_required('mentor', 'coordinator', 'management')
def at_risk_directory(request):
    """Detailed list of fellows currently flagged by the At-Risk Engine."""
    at_risk_fellows = get_at_risk_mentees()
    
    # If Mentor, only show their specific students
    if request.user.role == 'mentor':
        at_risk_fellows = at_risk_fellows.filter(my_assignments__task__assigned_by=request.user).distinct()
        
    return render(request, 'progress/at_risk_list.html', {
        'fellows': at_risk_fellows,
        'greeting': "Risk Intervention"
    })


# ==============================================================================
# ACHIEVEMENTS & MILESTONES MODULE
# ==============================================================================
from .models import Achievement, Feedback
from notifications.services import notify
from django.utils import timezone
from groups.models import Pairing

@role_required('mentee', 'mentor', 'management', 'coordinator')
def achievements_list(request):
    """
    Shows verified achievements and pending submissions.
    Mentees see their own achievements; Mentors see assigned mentee achievements;
    Management & Coordinator see all.
    """
    user = request.user
    if user.role == 'mentee':
        my_achievements = Achievement.objects.filter(mentee=user)
        pending = my_achievements.filter(status='pending')
        verified = my_achievements.filter(status='verified')
    elif user.role == 'mentor':
        # Mentees paired with this mentor
        mentee_ids = Pairing.objects.filter(mentor=user, status='active').values_list('mentee_id', flat=True)
        my_achievements = Achievement.objects.filter(mentee_id__in=mentee_ids)
        pending = my_achievements.filter(status='pending')
        verified = Achievement.objects.filter(status='verified')
    else:
        pending = Achievement.objects.filter(status='pending')
        verified = Achievement.objects.filter(status='verified')

    context = {
        'pending_achievements': pending,
        'verified_achievements': verified,
    }
    return render(request, 'progress/achievements.html', context)


@role_required('mentee')
def submit_achievement(request):
    """Mentee submits an achievement for verification."""
    user = request.user
    if request.method == 'POST':
        category = request.POST.get('category')
        title = request.POST.get('title', '').strip()
        organisation = request.POST.get('organisation', '').strip()
        description = request.POST.get('description', '').strip()
        achievement_date = request.POST.get('achievement_date')
        evidence_link = request.POST.get('evidence_link', '').strip()

        ach = Achievement.objects.create(
            mentee=user,
            category=category,
            title=title,
            organisation=organisation,
            description=description,
            achievement_date=achievement_date,
            evidence_link=evidence_link,
            status='pending'
        )

        # Notify assigned mentor
        pairing = Pairing.objects.filter(mentee=user, status='active').first()
        if pairing and pairing.mentor:
            notify(
                user=pairing.mentor,
                verb='achievement_submitted',
                title='New Achievement for Verification',
                message=f"{user.get_full_name() or user.username} submitted: '{title}' ({ach.get_category_display()}).",
                link='/progress/achievements/'
            )

        create_audit_log(
            user=user,
            action="Achievement Submitted",
            details=f"Submitted achievement '{title}' ({category}) for verification."
        )

        messages.success(request, f"Achievement '{title}' submitted for mentor verification!")
        return redirect('progress:achievements')

    return render(request, 'progress/achievement_form.html')


@role_required('mentor', 'coordinator', 'management')
def review_achievement(request, achievement_id):
    """Mentor verifies or rejects an achievement submission."""
    achievement = get_object_or_404(Achievement, id=achievement_id)
    if request.method == 'POST':
        action = request.POST.get('action') # 'approve' or 'reject'
        notes = request.POST.get('review_notes', '').strip()

        if action == 'approve':
            achievement.status = 'verified'
            achievement.reviewed_by = request.user
            achievement.reviewed_at = timezone.now()
            achievement.review_notes = notes
            achievement.save()

            notify(
                user=achievement.mentee,
                verb='achievement_verified',
                title='Achievement Verified!',
                message=f"Congratulations! Your achievement '{achievement.title}' has been verified by {request.user.get_full_name() or request.user.username}.",
                link='/progress/achievements/'
            )
            create_audit_log(
                user=request.user,
                action="Achievement Verified",
                details=f"Verified achievement '{achievement.title}' for {achievement.mentee.username}."
            )
            messages.success(request, f"Achievement '{achievement.title}' verified successfully!")
        else:
            achievement.status = 'rejected'
            achievement.reviewed_by = request.user
            achievement.reviewed_at = timezone.now()
            achievement.review_notes = notes
            achievement.save()

            notify(
                user=achievement.mentee,
                verb='achievement_rejected',
                title='Achievement Verification Update',
                message=f"Your achievement '{achievement.title}' was reviewed. Notes: {notes or 'Insufficient documentation'}",
                link='/progress/achievements/'
            )
            messages.info(request, f"Achievement '{achievement.title}' declined.")

    return redirect('progress:achievements')


# ==============================================================================
# FEEDBACK & EVALUATION MODULE
# ==============================================================================

@role_required('mentee', 'mentor', 'management', 'coordinator')
def feedback_list(request):
    """Feedback repository with immutable submission history."""
    feedbacks = Feedback.objects.all().select_related('submitted_by', 'recipient').order_by('-created_at')
    return render(request, 'progress/feedback.html', {
        'feedbacks': feedbacks,
    })


@role_required('mentee', 'mentor', 'management', 'coordinator')
def submit_feedback(request):
    """Submits permanent, immutable evaluation."""
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        category = request.POST.get('category')
        rating = int(request.POST.get('rating', 5))
        content = request.POST.get('content', '').strip()

        recipient = User.objects.filter(id=recipient_id).first() if recipient_id else None

        fb = Feedback.objects.create(
            submitted_by=request.user,
            recipient=recipient,
            category=category,
            rating=rating,
            content=content,
            is_permanent=True
        )

        create_audit_log(
            user=request.user,
            action="Feedback Submitted",
            details=f"Permanent feedback submitted for category: {category} (Rating: {rating}/5)."
        )

        messages.success(request, "Thank you! Your evaluation has been permanently recorded.")
        return redirect('progress:feedback')

    # Available recipients
    recipients = User.objects.exclude(id=request.user.id).filter(is_active=True)
    return render(request, 'progress/feedback_form.html', {'recipients': recipients})


@role_required('coordinator', 'management')
def points_rules_admin(request):
    """Configurable scoring engine: adjust points per action."""
    if request.method == 'POST':
        for rule in PointsRule.objects.all():
            new_val = request.POST.get(f'rule_{rule.id}')
            if new_val is not None:
                rule.points = int(new_val)
                rule.save()
        messages.success(request, "Scoring rules successfully updated!")
        create_audit_log(
            user=request.user,
            action="Points Rules Updated",
            details="Configured programme scoring weights in PointsRule."
        )
        return redirect('progress:points_rules')

    rules = PointsRule.objects.all().order_by('label')
    return render(request, 'progress/points_rules.html', {'rules': rules})