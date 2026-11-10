from .models import Notification

def notification_context(request):
    """
    Context processor to make unread notification count and latest notifications
    available across all templates.
    """
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        latest = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        return {
            'unread_notifications_count': unread_count,
            'latest_notifications': latest
        }
    return {
        'unread_notifications_count': 0,
        'latest_notifications': []
    }
