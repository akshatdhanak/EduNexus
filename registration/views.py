from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import check_password
from django.contrib.sessions.models import Session
from django.middleware.csrf import get_token
from django.contrib import messages
import time

from .forms import CustomLoginForm

# Login View
@csrf_protect
def custom_login(request):
    if request.method == "POST":
        selected_role = request.POST.get('role')
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if selected role matches user's actual role
            user_role = 'admin' if user.is_superuser else user.role
            
            if user_role != selected_role:
                # Role mismatch - show generic message
                form = CustomLoginForm()
                error_message = "Invalid username or password"
                return render(request, "registration/login.html", {
                    "form": form, 
                    "error_message": error_message,
                    "submitted_role": selected_role, 
                    "submitted_username": username
                })
            
            # ── Invalidate any existing sessions for this user ──
            # Delete all previous sessions for this user (single-session enforcement)
            all_sessions = Session.objects.filter(expire_date__gte=__import__('django.utils.timezone', fromlist=['now']).now())
            for s in all_sessions:
                try:
                    data = s.get_decoded()
                    if str(data.get('_auth_user_id')) == str(user.pk):
                        s.delete()
                except Exception:
                    pass
            
            # Role matches - login user
            login(request, user)
            
            # ── Store session metadata ──
            request.session['user_role'] = user_role
            request.session['login_time'] = time.time()
            request.session['last_activity'] = time.time()
            request.session['session_key'] = request.session.session_key

            if user.is_superuser:
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect("admin_app:admin_dashboard")
            elif user.role == "faculty":
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect("faculty_app:faculty_dashboard")
            else:
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect("student_app:student_dashboard")
        else:
            # User not found or wrong password
            form = CustomLoginForm()
            error_message = "Invalid username or password"
            return render(request, "registration/login.html", {
                "form": form, 
                "error_message": error_message,
                "submitted_role": selected_role, 
                "submitted_username": username
            })
    else:
        # If already authenticated, redirect to appropriate dashboard
        if request.user.is_authenticated:
            user_role = 'admin' if request.user.is_superuser else request.user.role
            if user_role == 'admin':
                return redirect("admin_app:admin_dashboard")
            elif user_role == 'faculty':
                return redirect("faculty_app:faculty_dashboard")
            else:
                return redirect("student_app:student_dashboard")
        
        # Ensure CSRF token is generated for GET requests
        get_token(request)
        form = CustomLoginForm()

    return render(request, "registration/login.html", {"form": form})


def user_logout(request):
    if request.user.is_authenticated:
        # Clear all session data
        request.session.flush()
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('registration:login')
