from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .models import HelpRequest, HelpResponse
from accounts.permissions import role_required
from notifications.services import notify
from progress.services import create_audit_log
from groups.models import Pairing, GroupMembership

@login_required
def helpdesk_home(request):
    """
    Shows help desk tickets:
    - Mentees see tickets they submitted.
    - Mentors see tickets assigned to them.
    - Management & Coordinators see all tickets, especially escalated ones.
    """
    user = request.user
    if user.role == 'mentee':
        tickets = HelpRequest.objects.filter(mentee=user)
    elif user.role == 'mentor':
        tickets = HelpRequest.objects.filter(assigned_to=user)
    else:
        tickets = HelpRequest.objects.all()

    status_filter = request.GET.get('status', 'all')
    if status_filter and status_filter != 'all':
        tickets = tickets.filter(status=status_filter)

    context = {
        'tickets': tickets,
        'current_status': status_filter,
        'open_count': tickets.filter(status='open').count(),
        'in_progress_count': tickets.filter(status='in_progress').count(),
        'escalated_count': tickets.filter(status='escalated').count(),
    }
    return render(request, 'helpdesk/ticket_list.html', context)


@role_required('mentee')
def ticket_create(request):
    """Mentee submits a new help desk ticket."""
    user = request.user
    # Route to assigned mentor
    pairing = Pairing.objects.filter(mentee=user, status='active').first()
    assigned_mentor = pairing.mentor if pairing else None

    if not assigned_mentor:
        membership = GroupMembership.objects.filter(user=user, group__mentor__isnull=False).first()
        if membership:
            assigned_mentor = membership.group.mentor

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        priority = request.POST.get('priority', 'normal')

        ticket = HelpRequest.objects.create(
            mentee=user,
            assigned_to=assigned_mentor,
            subject=subject,
            message=message,
            priority=priority,
            status='open'
        )

        if assigned_mentor:
            notify(
                user=assigned_mentor,
                verb='help_ticket_opened',
                title=f'Help Desk: {subject}',
                message=f"Fellow {user.get_full_name() or user.username} submitted inquiry: '{subject}'.",
                link=f'/helpdesk/{ticket.id}/'
            )

        create_audit_log(
            user=user,
            action="Help Desk Ticket Created",
            details=f"Created ticket #{ticket.id}: '{subject}'"
        )

        messages.success(request, f"Help request #{ticket.id} submitted! Your mentor will be notified.")
        return redirect('helpdesk:ticket_detail', ticket_id=ticket.id)

    return render(request, 'helpdesk/ticket_create.html', {'assigned_mentor': assigned_mentor})


@login_required
def ticket_detail(request, ticket_id):
    """Discussion thread view of a support ticket."""
    ticket = get_object_or_404(HelpRequest, id=ticket_id)
    user = request.user

    # Permission check: mentee who created it, assigned mentor, or leader
    if user.role == 'mentee' and ticket.mentee != user:
        raise PermissionDenied
    if user.role == 'mentor' and ticket.assigned_to != user:
        raise PermissionDenied

    responses = ticket.responses.all().select_related('responder')

    return render(request, 'helpdesk/ticket_detail.html', {
        'ticket': ticket,
        'responses': responses,
    })


@login_required
def respond_ticket(request, ticket_id):
    """Posts a message to the help desk ticket discussion thread."""
    ticket = get_object_or_404(HelpRequest, id=ticket_id)
    user = request.user

    if user.role == 'mentee' and ticket.mentee != user:
        raise PermissionDenied
    if user.role == 'mentor' and ticket.assigned_to != user:
        raise PermissionDenied

    if request.method == 'POST':
        msg = request.POST.get('message', '').strip()
        if msg:
            HelpResponse.objects.create(
                request=ticket,
                responder=user,
                message=msg
            )

            # Update ticket status
            if user == ticket.mentee:
                ticket.status = 'in_progress'
                if ticket.assigned_to:
                    notify(
                        user=ticket.assigned_to,
                        verb='help_ticket_response',
                        title=f'Reply on Ticket #{ticket.id}',
                        message=f"{user.get_full_name() or user.username} replied on: {ticket.subject}",
                        link=f'/helpdesk/{ticket.id}/'
                    )
            else:
                ticket.status = 'awaiting_mentee'
                notify(
                    user=ticket.mentee,
                    verb='help_ticket_response',
                    title=f'Reply on Ticket #{ticket.id}',
                    message=f"{user.get_full_name() or user.username} replied on: {ticket.subject}",
                    link=f'/helpdesk/{ticket.id}/'
                )

            ticket.save()
            messages.success(request, "Your message has been posted.")

    return redirect('helpdesk:ticket_detail', ticket_id=ticket.id)


@login_required
def update_ticket_status(request, ticket_id):
    """Allows Mentor or Management to update ticket status or escalate to Management."""
    ticket = get_object_or_404(HelpRequest, id=ticket_id)
    new_status = request.POST.get('status')

    if new_status in ['open', 'in_progress', 'awaiting_mentee', 'resolved', 'escalated']:
        ticket.status = new_status
        ticket.save()

        create_audit_log(
            user=request.user,
            action="Ticket Status Updated",
            details=f"Ticket #{ticket.id} status changed to {ticket.get_status_display()} by {request.user.username}."
        )

        if new_status == 'resolved':
            notify(
                user=ticket.mentee,
                verb='help_ticket_resolved',
                title=f'Ticket #{ticket.id} Resolved',
                message=f"Your inquiry '{ticket.subject}' has been marked as resolved.",
                link=f'/helpdesk/{ticket.id}/'
            )
            messages.success(request, f"Ticket #{ticket.id} marked as resolved.")
        elif new_status == 'escalated':
            messages.warning(request, f"Ticket #{ticket.id} escalated to Management Team.")

    return redirect('helpdesk:ticket_detail', ticket_id=ticket.id)