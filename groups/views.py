from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth import get_user_model
from accounts.permissions import role_required
from .models import Group, GroupMembership, JoinRequest, Pairing, Meeting, MeetingRequest
from notifications.services import notify
from progress.services import create_audit_log
from django.utils import timezone

User = get_user_model()

@role_required('coordinator', 'management', 'mentee', 'mentor')
def group_list(request):
    """
    Global list of tracks. 
    Mentees see join options; Leaders see management options.
    """
    groups = Group.objects.filter(status='active').order_by('name')
    user_memberships = []
    user_requests = []
    
    if request.user.is_authenticated:
        user_memberships = GroupMembership.objects.filter(user=request.user).values_list('group_id', flat=True)
        user_requests = JoinRequest.objects.filter(user=request.user, status='pending').values_list('group_id', flat=True)

    return render(request, 'groups/group_list.html', {
        'groups': groups,
        'user_memberships': user_memberships,
        'user_requests': user_requests
    })

@role_required('coordinator', 'management', 'mentor')
def group_detail(request, group_id):
    """
    The Operational Console for a group. 
    Strict Gating: Mentors can only access if they lead this specific group.
    """
    group = get_object_or_404(Group, id=group_id)
    
    # Permission Check for Mentors
    if request.user.role == 'mentor' and group.mentor != request.user:
        raise PermissionDenied("Access Denied: You do not lead this research track.")

    members = group.memberships.all().select_related('user')
    already_in_group = members.values_list('user_id', flat=True)
    
    # Data for Modals (Add Members / Assign Mentor)
    available_mentees = User.objects.filter(role='mentee').exclude(id__in=already_in_group)
    available_mentors = User.objects.filter(role__in=['mentor', 'coordinator', 'management'])
    
    return render(request, 'groups/group_detail.html', {
        'group': group,
        'members': members,
        'available_mentees': available_mentees,
        'available_mentors': available_mentors
    })

@role_required('coordinator', 'management', 'mentor')
def approve_request(request, request_id):
    """Approves a mentee's application to join a track."""
    join_req = get_object_or_404(JoinRequest, id=request_id)
    group = join_req.group
    
    # Leader Permission Check
    if request.user.role == 'mentor' and group.mentor != request.user:
        raise PermissionDenied

    if group.member_count >= group.capacity:
        messages.error(request, f"Capacity Alert: {group.name} is full.")
    else:
        GroupMembership.objects.get_or_create(group=group, user=join_req.user)
        join_req.status = 'approved'
        join_req.save()
        messages.success(request, f"Admission Confirmed: {join_req.user.username} is now a fellow of {group.name}.")
    
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:home'))

@role_required('coordinator', 'management', 'mentor')
def reject_request(request, request_id):
    """Declines a mentee's application."""
    join_req = get_object_or_404(JoinRequest, id=request_id)
    if request.user.role == 'mentor' and join_req.group.mentor != request.user:
        raise PermissionDenied
        
    join_req.status = 'rejected'
    join_req.save()
    messages.warning(request, f"Application for {join_req.user.username} was declined.")
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:home'))

@role_required('coordinator', 'management', 'mentor')
def remove_member(request, group_id, user_id):
    """Removes a member from a track roster."""
    group = get_object_or_404(Group, id=group_id)
    if request.user.role == 'mentor' and group.mentor != request.user:
        raise PermissionDenied
        
    membership = get_object_or_404(GroupMembership, group=group, user_id=user_id)
    username = membership.user.username
    membership.delete()
    messages.warning(request, f"Roster Updated: {username} removed from {group.name}.")
    return redirect('groups:group_detail', group_id=group_id)

@role_required('coordinator', 'management', 'mentor')
def add_members_logic(request, group_id):
    """Logic for manual and bulk addition of fellows."""
    group = get_object_or_404(Group, id=group_id)
    if request.user.role == 'mentor' and group.mentor != request.user:
        raise PermissionDenied
        
    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')
        if not user_ids:
            messages.info(request, "Selection required for bulk assignment.")
            return redirect('groups:group_detail', group_id=group_id)

        if group.member_count + len(user_ids) > group.capacity:
            messages.error(request, "Operation cancelled: Selection exceeds track capacity.")
        else:
            for u_id in user_ids:
                u = get_object_or_404(User, id=u_id)
                GroupMembership.objects.get_or_create(group=group, user=u)
            messages.success(request, f"Success: {len(user_ids)} fellows assigned to track.")
            
    return redirect('groups:group_detail', group_id=group_id)

@role_required('mentee')
def request_to_join(request, group_id):
    """Allows a mentee to apply for an active track."""
    group = get_object_or_404(Group, id=group_id)
    if group.join_status == 'open':
        GroupMembership.objects.get_or_create(group=group, user=request.user)
        messages.success(request, f"Welcome to the team! You joined {group.name} successfully.")
    else:
        JoinRequest.objects.get_or_create(group=group, user=request.user, status='pending')
        messages.success(request, f"Application for '{group.name}' submitted to track lead.")
    return redirect('groups:group_list')

@role_required('coordinator', 'management')
def assign_mentor(request, group_id):
    """Coordinator only: Assigns the Lead Mentor/Supervisor for a track."""
    if request.method == 'POST':
        group = get_object_or_404(Group, id=group_id)
        mentor_id = request.POST.get('mentor_id')
        mentor = get_object_or_404(User, id=mentor_id)
        group.mentor = mentor
        group.save()
        messages.success(request, f"Leadership Assigned: {mentor.get_full_name()} is now leading {group.name}.")
    return redirect('groups:group_detail', group_id=group_id)

@role_required('mentee', 'mentor', 'management', 'coordinator')
def mentee_group_view(request, group_id):
    """The private peer directory for group members."""
    group = get_object_or_404(Group, id=group_id)
    peers = GroupMembership.objects.filter(group=group).select_related('user')
    return render(request, 'groups/mentee_group_view.html', {'group': group, 'peers': peers})

@role_required('coordinator')
def create_group(request):
    """Allows Coordinator to initialize a brand new fellowship track."""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        capacity = request.POST.get('capacity', 20)
        join_status = request.POST.get('join_status', 'approval')
        
        new_group = Group.objects.create(
            name=name,
            description=description,
            capacity=capacity,
            join_status=join_status,
            coordinator=request.user,
            status='active'
        )
        
        messages.success(request, f"System Success: '{new_group.name}' track has been initialized.")
        return redirect('dashboard:coordinator_dashboard')
    
    return render(request, 'groups/group_form.html')


@role_required('coordinator')
def delete_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    name = group.name
    group.delete()
    create_audit_log(
        user=request.user,
        action="Group Deleted",
        details=f"Permanently terminated research track '{name}'."
    )
    messages.warning(request, f"System Action: Research track '{name}' has been permanently terminated.")
    return redirect('dashboard:coordinator_dashboard')


@role_required('coordinator', 'management')
def edit_group(request, group_id):
    """Allows Coordinator or Management to update group properties."""
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        group.name = request.POST.get('name', group.name)
        group.description = request.POST.get('description', group.description)
        group.capacity = int(request.POST.get('capacity', group.capacity))
        group.join_status = request.POST.get('join_status', group.join_status)
        group.status = request.POST.get('status', group.status)
        group.save()

        create_audit_log(
            user=request.user,
            action="Track Modified",
            details=f"Updated details for track {group.name}."
        )
        messages.success(request, f"Research Track '{group.name}' successfully updated.")
        return redirect('groups:group_detail', group_id=group.id)

    return redirect('groups:group_detail', group_id=group.id)


@role_required('coordinator', 'management')
def archive_group(request, group_id):
    """Toggles active/archived status for a track."""
    group = get_object_or_404(Group, id=group_id)
    group.status = 'archived' if group.status == 'active' else 'active'
    group.save()

    status_str = "archived" if group.status == 'archived' else "reactivated"
    create_audit_log(
        user=request.user,
        action="Track Status Toggle",
        details=f"Track '{group.name}' was {status_str}."
    )
    messages.info(request, f"Track '{group.name}' has been {status_str}.")
    return redirect('groups:group_list')


# ==============================================================================
# PAIRINGS MODULE — 1-to-1 & 1-to-Many Mentor-Mentee Relationships
# ==============================================================================

@role_required('coordinator', 'management', 'mentor')
def pairing_list(request):
    """
    Overview of active and terminated pairings across the programme.
    Mentors only see their own pairings; Coordinators and Management see all.
    """
    if request.user.role == 'mentor':
        pairings = Pairing.objects.filter(mentor=request.user).select_related('mentor', 'mentee', 'group')
    else:
        pairings = Pairing.objects.all().select_related('mentor', 'mentee', 'group')

    active_pairings = pairings.filter(status='active')
    terminated_pairings = pairings.filter(status='terminated')

    context = {
        'active_pairings': active_pairings,
        'terminated_pairings': terminated_pairings,
        'total_active': active_pairings.count(),
        'available_mentors': User.objects.filter(role='mentor', is_active=True),
        'available_mentees': User.objects.filter(role='mentee', is_active=True),
        'groups': Group.objects.filter(status='active'),
    }
    return render(request, 'groups/pairings.html', context)


@role_required('coordinator', 'management')
def create_pairing(request):
    """
    Assigns a Mentor to a Mentee (Pair & Notify).
    Dispatches automated notifications and email to both parties.
    """
    if request.method == 'POST':
        mentor_id = request.POST.get('mentor_id')
        mentee_id = request.POST.get('mentee_id')
        group_id = request.POST.get('group_id')

        mentor = get_object_or_404(User, id=mentor_id, role='mentor')
        mentee = get_object_or_404(User, id=mentee_id, role='mentee')
        group = Group.objects.filter(id=group_id).first() if group_id else None

        # Check for existing active pairing
        existing = Pairing.objects.filter(mentor=mentor, mentee=mentee, status='active').first()
        if existing:
            messages.warning(request, f"{mentor.get_full_name()} is already paired with {mentee.get_full_name()}.")
            return redirect('groups:pairing_list')

        pairing = Pairing.objects.create(
            mentor=mentor,
            mentee=mentee,
            group=group,
            status='active',
            created_by=request.user
        )

        # Notify Mentor
        notify(
            user=mentor,
            verb='pairing_created',
            title='New Mentee Assigned',
            message=f"You have been paired with fellow {mentee.get_full_name() or mentee.username}{f' in {group.name}' if group else ''}.",
            link=f'/accounts/users/{mentee.id}/detail/'
        )

        # Notify Mentee
        notify(
            user=mentee,
            verb='pairing_created',
            title='Mentor Assigned',
            message=f"You have been assigned to Mentor {mentor.get_full_name() or mentor.username} ({mentor.expertise or 'Faculty'}).",
            link=f'/accounts/users/{mentor.id}/detail/'
        )

        create_audit_log(
            user=request.user,
            action="Pairing Established",
            details=f"Paired mentor {mentor.username} with mentee {mentee.username}."
        )

        messages.success(request, f"Success: {mentor.get_full_name()} paired with {mentee.get_full_name()} and both parties notified!")
        return redirect('groups:pairing_list')

    return render(request, 'groups/pairing_form.html', {
        'mentors': User.objects.filter(role='mentor', is_active=True),
        'mentees': User.objects.filter(role='mentee', is_active=True),
        'groups': Group.objects.filter(status='active'),
    })


@role_required('coordinator', 'management')
def terminate_pairing(request, pairing_id):
    """
    Terminates a pairing while preserving all meeting, task, and achievement records.
    """
    pairing = get_object_or_404(Pairing, id=pairing_id)
    if request.method == 'POST':
        reason = request.POST.get('reason', 'Administrative unpairing')
        pairing.status = 'terminated'
        pairing.terminated_at = timezone.now()
        pairing.termination_reason = reason
        pairing.save()

        # Notify both parties
        notify(
            user=pairing.mentor,
            verb='pairing_terminated',
            title='Pairing Concluded',
            message=f"Mentorship pairing with {pairing.mentee.get_full_name() or pairing.mentee.username} has been concluded. Reason: {reason}",
            link='/groups/pairings/'
        )
        notify(
            user=pairing.mentee,
            verb='pairing_terminated',
            title='Pairing Concluded',
            message=f"Mentorship pairing with {pairing.mentor.get_full_name() or pairing.mentor.username} has been concluded.",
            link='/dashboard/'
        )

        create_audit_log(
            user=request.user,
            action="Pairing Terminated",
            details=f"Terminated pairing between {pairing.mentor.username} and {pairing.mentee.username}. Reason: {reason}"
        )

        messages.info(request, f"Pairing between {pairing.mentor.username} and {pairing.mentee.username} has been terminated.")
        return redirect('groups:pairing_list')

    return redirect('groups:pairing_list')


# ==============================================================================
# MEETINGS MODULE — Scheduling, Mentee Requests, Platform Links
# ==============================================================================

@role_required('mentee', 'mentor', 'management', 'coordinator')
def meeting_list(request):
    """
    Shows meetings relevant to the current user:
    - Mentees see their upcoming/past meetings and submitted requests.
    - Mentors see their upcoming/past meetings and pending mentee requests.
    - Management/Coordinators see all meetings and requests across the programme.
    """
    user = request.user
    today = timezone.now().date()

    if user.role == 'mentee':
        upcoming = Meeting.objects.filter(mentee=user, status='scheduled', meeting_date__gte=today).order_by('meeting_date', 'meeting_time')
        past = Meeting.objects.filter(mentee=user).exclude(id__in=upcoming.values_list('id', flat=True)).order_by('-meeting_date')
        requests = MeetingRequest.objects.filter(mentee=user).order_by('-created_at')
    elif user.role == 'mentor':
        upcoming = Meeting.objects.filter(mentor=user, status='scheduled', meeting_date__gte=today).order_by('meeting_date', 'meeting_time')
        past = Meeting.objects.filter(mentor=user).exclude(id__in=upcoming.values_list('id', flat=True)).order_by('-meeting_date')
        requests = MeetingRequest.objects.filter(mentor=user, status='pending').order_by('-created_at')
    else:
        upcoming = Meeting.objects.filter(status='scheduled', meeting_date__gte=today).order_by('meeting_date', 'meeting_time')
        past = Meeting.objects.filter().exclude(id__in=upcoming.values_list('id', flat=True)).order_by('-meeting_date')
        requests = MeetingRequest.objects.filter(status='pending').order_by('-created_at')

    context = {
        'upcoming_meetings': upcoming,
        'past_meetings': past,
        'meeting_requests': requests,
        'today': today,
    }
    return render(request, 'groups/meetings.html', context)


@role_required('mentor', 'coordinator', 'management')
def schedule_meeting(request):
    """
    Schedule a meeting between a Mentor and Mentee (or Group).
    Supplies the meeting link (Microsoft Teams, Zoom, Google Meet).
    """
    user = request.user
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        agenda = request.POST.get('agenda', '').strip()
        meeting_date = request.POST.get('meeting_date')
        meeting_time = request.POST.get('meeting_time')
        meeting_platform = request.POST.get('meeting_platform', 'Microsoft Teams')
        meeting_link = request.POST.get('meeting_link', '').strip()
        pairing_id = request.POST.get('pairing_id')

        pairing = None
        mentor = user
        mentee = None
        group = None

        if pairing_id:
            pairing = get_object_or_404(Pairing, id=pairing_id)
            mentor = pairing.mentor
            mentee = pairing.mentee
            group = pairing.group
        else:
            mentee_id = request.POST.get('mentee_id')
            if mentee_id:
                mentee = get_object_or_404(User, id=mentee_id)

        meeting = Meeting.objects.create(
            pairing=pairing,
            group=group,
            mentor=mentor,
            mentee=mentee,
            title=title,
            agenda=agenda,
            meeting_date=meeting_date,
            meeting_time=meeting_time,
            meeting_platform=meeting_platform,
            meeting_link=meeting_link,
            status='scheduled',
            created_by=user
        )

        # Notify Mentee
        if mentee:
            notify(
                user=mentee,
                verb='meeting_scheduled',
                title=f'Meeting: {title}',
                message=f"Meeting scheduled for {meeting_date} at {meeting_time} via {meeting_platform}. Join link: {meeting_link}",
                link='/groups/meetings/'
            )

        # If scheduled by Coordinator, also notify Mentor
        if user != mentor:
            notify(
                user=mentor,
                verb='meeting_scheduled',
                title=f'Meeting Scheduled: {title}',
                message=f"Meeting with {mentee.get_full_name() if mentee else 'Group'} on {meeting_date} at {meeting_time}.",
                link='/groups/meetings/'
            )

        create_audit_log(
            user=user,
            action="Meeting Scheduled",
            details=f"Scheduled '{title}' for {meeting_date} at {meeting_time} ({meeting_platform})."
        )

        messages.success(request, f"Meeting '{title}' successfully scheduled and participants notified!")
        return redirect('groups:meeting_list')

    # Data for scheduling form
    if user.role == 'mentor':
        pairings = Pairing.objects.filter(mentor=user, status='active').select_related('mentee', 'group')
        mentees = User.objects.filter(mentee_pairings__mentor=user, mentee_pairings__status='active').distinct()
    else:
        pairings = Pairing.objects.filter(status='active').select_related('mentor', 'mentee', 'group')
        mentees = User.objects.filter(role='mentee', is_active=True)

    return render(request, 'groups/meeting_form.html', {
        'pairings': pairings,
        'mentees': mentees,
    })


@role_required('mentee')
def request_meeting(request):
    """Allows a Mentee to request a meeting with their assigned Mentor."""
    user = request.user
    # Find active pairing
    pairing = Pairing.objects.filter(mentee=user, status='active').first()
    
    # If no explicit pairing, fallback to group mentor
    group_membership = GroupMembership.objects.filter(user=user, group__mentor__isnull=False).select_related('group__mentor').first()
    assigned_mentor = pairing.mentor if pairing else (group_membership.group.mentor if group_membership else None)

    if not assigned_mentor:
        messages.error(request, "You are not currently paired with a mentor. Please contact your Programme Coordinator.")
        return redirect('dashboard:mentee_dashboard')

    if request.method == 'POST':
        topic = request.POST.get('topic', '').strip()
        agenda = request.POST.get('agenda', '').strip()
        proposed_date = request.POST.get('proposed_date')
        proposed_time = request.POST.get('proposed_time')

        m_req = MeetingRequest.objects.create(
            pairing=pairing,
            mentee=user,
            mentor=assigned_mentor,
            topic=topic,
            agenda=agenda,
            proposed_date=proposed_date,
            proposed_time=proposed_time,
            status='pending'
        )

        # Notify Mentor
        notify(
            user=assigned_mentor,
            verb='meeting_request',
            title='Meeting Request from Mentee',
            message=f"{user.get_full_name() or user.username} requested a session: '{topic}' on {proposed_date} at {proposed_time}.",
            link='/groups/meetings/'
        )

        create_audit_log(
            user=user,
            action="Meeting Requested",
            details=f"Requested meeting '{topic}' with mentor {assigned_mentor.username}."
        )

        messages.success(request, f"Meeting request submitted to Mentor {assigned_mentor.get_full_name() or assigned_mentor.username}.")
        return redirect('groups:meeting_list')

    return render(request, 'groups/meeting_request_form.html', {
        'mentor': assigned_mentor,
        'pairing': pairing
    })


@role_required('mentor', 'coordinator', 'management')
def review_meeting_request(request, request_id):
    """Mentor or Admin accepts or declines a meeting request."""
    m_req = get_object_or_404(MeetingRequest, id=request_id)
    if request.user.role == 'mentor' and m_req.mentor != request.user:
        raise PermissionDenied

    if request.method == 'POST':
        action = request.POST.get('action') # 'approve' or 'reject'
        notes = request.POST.get('review_notes', '')

        if action == 'approve':
            meeting_link = request.POST.get('meeting_link', '').strip()
            meeting_platform = request.POST.get('meeting_platform', 'Microsoft Teams')

            m_req.status = 'approved'
            m_req.reviewed_by = request.user
            m_req.review_notes = notes
            m_req.save()

            # Create confirmed meeting
            meeting = Meeting.objects.create(
                pairing=m_req.pairing,
                mentor=m_req.mentor,
                mentee=m_req.mentee,
                title=m_req.topic,
                agenda=m_req.agenda,
                meeting_date=m_req.proposed_date,
                meeting_time=m_req.proposed_time,
                meeting_platform=meeting_platform,
                meeting_link=meeting_link or 'https://teams.microsoft.com',
                status='scheduled',
                created_by=request.user
            )

            notify(
                user=m_req.mentee,
                verb='meeting_approved',
                title='Meeting Request Approved!',
                message=f"Your meeting '{m_req.topic}' on {m_req.proposed_date} was approved. Link: {meeting.meeting_link}",
                link='/groups/meetings/'
            )

            messages.success(request, f"Meeting request confirmed! Session created on {m_req.proposed_date}.")
        else:
            m_req.status = 'rejected'
            m_req.reviewed_by = request.user
            m_req.review_notes = notes
            m_req.save()

            notify(
                user=m_req.mentee,
                verb='meeting_rejected',
                title='Meeting Request Update',
                message=f"Your meeting request '{m_req.topic}' could not be accommodated. Reason: {notes or 'Schedule conflict'}",
                link='/groups/meetings/'
            )
            messages.info(request, f"Meeting request from {m_req.mentee.username} declined.")

    return redirect('groups:meeting_list')


@role_required('mentor', 'coordinator', 'management')
def complete_meeting(request, meeting_id):
    """Marks a meeting as successfully completed."""
    meeting = get_object_or_404(Meeting, id=meeting_id)
    meeting.status = 'completed'
    meeting.save()

    create_audit_log(
        user=request.user,
        action="Meeting Completed",
        details=f"Marked meeting '{meeting.title}' as completed."
    )
    messages.success(request, f"Meeting '{meeting.title}' marked as completed.")
    return redirect('groups:meeting_list')


@role_required('mentor', 'coordinator', 'management')
def cancel_meeting(request, meeting_id):
    """Cancels a scheduled meeting."""
    meeting = get_object_or_404(Meeting, id=meeting_id)
    meeting.status = 'cancelled'
    meeting.save()

    # Notify participants
    if meeting.mentee:
        notify(
            user=meeting.mentee,
            verb='meeting_cancelled',
            title='Meeting Cancelled',
            message=f"Meeting '{meeting.title}' scheduled for {meeting.meeting_date} has been cancelled.",
            link='/groups/meetings/'
        )

    create_audit_log(
        user=request.user,
        action="Meeting Cancelled",
        details=f"Cancelled meeting '{meeting.title}'."
    )
    messages.warning(request, f"Meeting '{meeting.title}' has been cancelled.")
    return redirect('groups:meeting_list')