from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import SiteSettings, Recognition
from accounts.permissions import role_required
from progress.models import Achievement
from groups.models import Group
from tasks.models import Task
from announcements.models import Announcement
from django.contrib.auth import get_user_model
from progress.services import create_audit_log

User = get_user_model()

def home(request):
    """
    Public landing page for unauthenticated visitors.
    Authenticated users are redirected directly to their role dashboard.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    total_mentees = User.objects.filter(role='mentee').count()
    total_mentors = User.objects.filter(role='mentor').count()
    total_tracks = Group.objects.filter(status='active').count()
    total_achievements = Achievement.objects.filter(status='verified').count()
    recognitions = Recognition.objects.all()[:4]
    tracks = Group.objects.filter(status='active')[:6]

    context = {
        'total_mentees': total_mentees,
        'total_mentors': total_mentors,
        'total_tracks': total_tracks,
        'total_achievements': total_achievements,
        'recognitions': recognitions,
        'tracks': tracks,
    }
    return render(request, 'core/home.html', context)


def wall_of_fame(request):
    """
    Wall of Fame: Showcases Mentee of the Month, Mentor of the Month,
    Hall of Fame inductees, and top verified milestones.
    """
    recognitions = Recognition.objects.all().select_related('user')
    mentees_of_month = recognitions.filter(type='mentee_of_month')
    mentors_of_month = recognitions.filter(type='mentor_of_month')
    hall_of_fame = recognitions.filter(type='hall_of_fame')
    top_achievements = Achievement.objects.filter(status='verified')[:6]

    context = {
        'mentees_of_month': mentees_of_month,
        'mentors_of_month': mentors_of_month,
        'hall_of_fame': hall_of_fame,
        'top_achievements': top_achievements,
    }
    return render(request, 'core/wall_of_fame.html', context)


@role_required('management', 'coordinator')
def manage_wall_of_fame(request):
    """Allows Management or Coordinator to induct members into Wall of Fame."""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        rec_type = request.POST.get('type')
        period = request.POST.get('period', '').strip()
        badge_title = request.POST.get('badge_title', '').strip()
        note = request.POST.get('note', '').strip()

        target_user = get_object_or_404(User, id=user_id)

        rec = Recognition.objects.create(
            user=target_user,
            type=rec_type,
            period=period,
            badge_title=badge_title,
            note=note
        )

        create_audit_log(
            user=request.user,
            action="Wall of Fame Induction",
            details=f"Inducted {target_user.username} as {rec.get_type_display()} ({period})."
        )

        messages.success(request, f"{target_user.get_full_name() or target_user.username} successfully inducted into the Wall of Fame!")
        return redirect('core:wall_of_fame')

    users = User.objects.filter(is_active=True).order_by('first_name', 'username')
    return render(request, 'core/manage_wall_of_fame.html', {'users': users})


def global_search(request):
    """
    Global platform-wide search engine.
    Finds mentors, mentees, expertise, tracks, tasks, announcements, and achievements.
    """
    query = request.GET.get('q', '').strip()
    
    mentors = []
    mentees = []
    tracks = []
    tasks = []
    achievements = []
    announcements = []

    if query:
        # Search Mentors
        mentors = User.objects.filter(
            Q(role='mentor') & (
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(expertise__icontains=query) |
                Q(qualification__icontains=query) |
                Q(bio__icontains=query)
            )
        )

        # Search Mentees
        mentees = User.objects.filter(
            Q(role='mentee') & (
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(academic_status__icontains=query) |
                Q(interests__icontains=query) |
                Q(career_goal__icontains=query)
            )
        )

        # Search Tracks
        tracks = Group.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

        # Search Tasks
        tasks = Task.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(category__icontains=query)
        )

        # Search Achievements
        achievements = Achievement.objects.filter(
            Q(title__icontains=query) | Q(organisation__icontains=query) | Q(description__icontains=query)
        )

        # Search Announcements
        announcements = Announcement.objects.filter(
            Q(title__icontains=query) | Q(message__icontains=query)
        )

    context = {
        'query': query,
        'mentors': mentors,
        'mentees': mentees,
        'tracks': tracks,
        'tasks': tasks,
        'achievements': achievements,
        'announcements': announcements,
        'total_results': len(mentors) + len(mentees) + len(tracks) + len(tasks) + len(achievements) + len(announcements)
    }
    return render(request, 'core/search.html', context)
