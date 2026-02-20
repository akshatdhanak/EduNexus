"""
Session handling middleware for EduNexus.

Features:
- Session timeout enforcement (uses SESSION_COOKIE_AGE from settings)
- Single active session per user (new login invalidates old session)
- Role-based URL access control (admin/faculty/student)
- Session activity tracking (last activity timestamp)
- Auto-logout on session expiry with message
"""

import time
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin


class SessionTimeoutMiddleware(MiddlewareMixin):
    """
    Tracks last activity time and logs out users whose session has been
    idle beyond SESSION_COOKIE_AGE seconds.
    """

    # Paths that don't require session checks
    EXEMPT_PATHS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/admin/',
        '/health/',
    ]

    def _is_exempt(self, path):
        return any(path.startswith(p) for p in self.EXEMPT_PATHS) or path == '/'

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        if self._is_exempt(request.path):
            return None

        last_activity = request.session.get('last_activity')
        if last_activity is not None:
            idle = time.time() - last_activity
            max_idle = getattr(settings, 'SESSION_COOKIE_AGE', 1800)
            if idle > max_idle:
                logout(request)
                messages.warning(request, 'Your session has expired due to inactivity. Please log in again.')
                return redirect('registration:login')

        # Update last activity timestamp
        request.session['last_activity'] = time.time()
        return None


class SingleSessionMiddleware(MiddlewareMixin):
    """
    Ensures only one active session per user.
    If the session key doesn't match the one stored for this user,
    it means the user logged in from somewhere else – this session is invalidated.
    """

    EXEMPT_PATHS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/admin/',
        '/health/',
    ]

    def _is_exempt(self, path):
        return any(path.startswith(p) for p in self.EXEMPT_PATHS) or path == '/'

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        if self._is_exempt(request.path):
            return None

        # Check if the current session matches what the user was assigned at login
        stored_session_key = request.session.get('session_key')
        if stored_session_key and stored_session_key != request.session.session_key:
            logout(request)
            messages.info(request, 'You have been logged out because your account was logged in from another location.')
            return redirect('registration:login')

        return None


class RoleBasedAccessMiddleware(MiddlewareMixin):
    """
    Restricts URL paths by user role:
    - /admin_app/* → admin/superuser only (except shared routes like database-chat)
    - /faculty_app/* → faculty only
    - /student_app/* → student only

    If someone manually types a URL for a different role, they are
    redirected to their own dashboard.
    """

    ROLE_PATH_MAP = {
        '/admin_app/': ['admin'],
        '/faculty_app/': ['faculty'],
        '/student_app/': ['student'],
    }

    ROLE_DASHBOARD = {
        'admin': 'admin_app:admin_dashboard',
        'faculty': 'faculty_app:faculty_dashboard',
        'student': 'student_app:student_dashboard',
    }

    # Paths accessible to ALL authenticated users regardless of role
    SHARED_PATHS = [
        '/admin_app/database-chat/',
    ]

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        # Allow shared paths for any authenticated user
        if any(request.path.startswith(p) for p in self.SHARED_PATHS):
            return None

        user = request.user
        user_role = 'admin' if user.is_superuser else getattr(user, 'role', None)

        for path_prefix, allowed_roles in self.ROLE_PATH_MAP.items():
            if request.path.startswith(path_prefix):
                if user_role not in allowed_roles:
                    dashboard = self.ROLE_DASHBOARD.get(user_role)
                    if dashboard:
                        messages.warning(request, 'You do not have permission to access that page.')
                        return redirect(dashboard)
                    else:
                        logout(request)
                        return redirect('registration:login')

        return None
