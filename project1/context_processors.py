"""
Custom context processors for EduNexus.
"""
from django.conf import settings


def session_timeout(request):
    """Make session timeout available in all templates."""
    return {
        'SESSION_TIMEOUT_SECONDS': getattr(settings, 'SESSION_COOKIE_AGE', 1800),
    }
