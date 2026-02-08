from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import check_password
from django.middleware.csrf import get_token

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
            
            # Role matches - login user
            login(request, user)

            if user.is_superuser:
                return redirect("admin_app:admin_dashboard")
            elif user.role == "faculty":
                return redirect("faculty_app:faculty_dashboard")
            else:
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
        # Ensure CSRF token is generated for GET requests
        get_token(request)
        form = CustomLoginForm()

    return render(request, "registration/login.html", {"form": form})


def user_logout(request):
    logout(request)
    return redirect('registration:login')
