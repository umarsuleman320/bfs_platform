from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

def notify(user, verb, message, link="", title=""):
    """
    Creates an in-platform notification and dispatches an email notification.
    Usage: notify(mentee, 'task_assigned', 'New assignment is ready', link='/tasks/1/', title='New Task')
    """
    if not title:
        title = verb.replace('_', ' ').title()

    notification = Notification.objects.create(
        user=user,
        verb=verb,
        title=title,
        message=message,
        link=link
    )

    # Email notification (console backend in development, SMTP in production)
    if user.email:
        subject = f"[BFS Platform] {title}"
        email_body = f"Hello {user.get_full_name() or user.username},\n\n{message}\n\nView details: {link}\n\nBFS Mentorship Programme"
        try:
            send_mail(
                subject=subject,
                message=email_body,
                from_email='noreply@bfs-platform.org',
                recipient_list=[user.email],
                fail_silently=True
            )
        except Exception:
            pass

    return notification
