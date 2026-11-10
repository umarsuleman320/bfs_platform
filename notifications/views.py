from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notification

@login_required
def notification_list(request):
    """Notification centre UI listing all in-platform notifications for current user."""
    notifications = Notification.objects.filter(user=request.user)
    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'unread_count': notifications.filter(is_read=False).count()
    })

@login_required
def mark_as_read(request, notification_id):
    """Marks a single notification as read and redirects to its link or back to list."""
    notif = get_object_or_404(Notification, id=notification_id, user=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('notifications:notification_list')

@login_required
def mark_all_read(request):
    """Marks all notifications as read for current user."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('notifications:notification_list')
