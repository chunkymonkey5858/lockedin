from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import UserActivity

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login activity"""
    try:
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            ip_address=request.META.get('REMOTE_ADDR') if request else None,
            details='User logged in'
        )
    except Exception:
        # Silently fail if logging fails to avoid breaking user experience
        pass

