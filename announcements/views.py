from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Announcement
from accounts.permissions import role_required
from groups.models import Group, GroupMembership
from notifications.services import notify
from progress.services import create_audit_log
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def announcement_list(request):
    """
    Renders announcements relevant to the current user:
    - Mentees see 'all', 'mentees', and announcements for their enrolled groups.
    - Mentors see 'all', 'mentors', and their led groups.
    - Management & Coordinators see all announcements.
    """
    user = request.user
    if user.role == 'mentee':
        my_group_ids = GroupMembership.objects.filter(user=user).values_list('group_id', flat=True)
        announcements = Announcement.objects.filter(
            Q(audience__in=['all', 'mentees']) |
            Q(audience='group', group_id__in=my_group_ids)
        )
    elif user.role == 'mentor':
        my_group_ids = Group.objects.filter(mentor=user).values_list('id', flat=True)
        announcements = Announcement.objects.filter(
            Q(audience__in=['all', 'mentors']) |
            Q(audience='group', group_id__in=my_group_ids)
        )
    else:
        announcements = Announcement.objects.all()

    return render(request, 'announcements/announcement_list.html', {
        'announcements': announcements,
    })


@role_required('management', 'coordinator')
def create_announcement(request):
    """Broadcast an announcement across the programme or to targeted tracks."""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        audience = request.POST.get('audience', 'all')
        group_id = request.POST.get('group_id')
        is_priority = request.POST.get('is_priority') == 'on'

        group = Group.objects.filter(id=group_id).first() if group_id else None

        announcement = Announcement.objects.create(
            title=title,
            message=message,
            audience=audience,
            group=group,
            is_priority=is_priority,
            created_by=request.user
        )

        # Notify relevant audience
        recipients = User.objects.filter(is_active=True)
        if audience == 'mentees':
            recipients = recipients.filter(role='mentee')
        elif audience == 'mentors':
            recipients = recipients.filter(role='mentor')
        elif audience == 'group' and group:
            recipients = recipients.filter(group_membership__group=group)

        for u in recipients[:50]: # Fan out notifications safely
            notify(
                user=u,
                verb='announcement',
                title=f"{'[PRIORITY] ' if is_priority else ''}Announcement: {title}",
                message=message[:120] + "...",
                link='/announcements/'
            )

        create_audit_log(
            user=request.user,
            action="Announcement Broadcast",
            details=f"Broadcasted '{title}' to audience: {audience}."
        )

        messages.success(request, f"Announcement '{title}' published and broadcasted!")
        return redirect('announcements:list')

    groups = Group.objects.filter(status='active')
    return render(request, 'announcements/announcement_form.html', {'groups': groups})


@role_required('management', 'coordinator')
def delete_announcement(request, announcement_id):
    """Deletes an announcement."""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    title = announcement.title
    announcement.delete()

    create_audit_log(
        user=request.user,
        action="Announcement Removed",
        details=f"Removed announcement: '{title}'"
    )
    messages.warning(request, f"Announcement '{title}' removed.")
    return redirect('announcements:list')
