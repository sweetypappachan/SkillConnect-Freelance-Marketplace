from .models import Notification


def navbar_notifications(request):
    """
    Injects `navbar_notifications` and `unread_notif_count` into every
    template context so the bell dropdown works on ALL pages, not just profile.
    """
    if not request.user.is_authenticated:
        return {
            'navbar_notifications': [],
            'unread_notif_count':   0,
        }

    notifications = (
        Notification.objects
        .filter(recipient=request.user)
        .order_by('-created_at')[:8]        # show latest 8 in dropdown
    )
    unread_count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    return {
        'navbar_notifications': notifications,
        'unread_notif_count':   unread_count,
    }