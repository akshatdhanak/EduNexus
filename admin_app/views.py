from functools import wraps
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from datetime import date


from registration.models import CustomUser

from .forms import FacultyForm, StudentForm, NotificationForm
from .models import Attendance, Faculty, Student, Notification, LeaveRequest, AttendanceFaculty, Timetable, Department, DegreeProgram, Subject, SubjectOffering

@staff_member_required
def admin_dashboard(request):
    student_count = Student.objects.count()
    faculty_count = Faculty.objects.count()
    
    # Get count of pending leave requests
    pending_leaves = LeaveRequest.objects.filter(status='pending').count()

    return render(request, "admin_app/dashboard.html", {
        "student_count": student_count,
        "faculty_count": faculty_count,
        "pending_leaves": pending_leaves
})

@staff_member_required
def manage_user(request):
    return render(request, "admin_app/manage_user.html")
        
@staff_member_required
def student_info(request):
    students = Student.objects.all()
    return render(request, "admin_app/student_info.html", {"students": students})

@staff_member_required
def student_add(request):
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES)   # for upload image in html file
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not username or not email or not password:
            messages.error(request, "Username, Email, and Password are required.")
            return redirect("admin_app:student_add")

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("admin_app:student_add")

        if form.is_valid():
            # Create CustomUser
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                role="student"
            )

            # Create Student and associate it with the user
            student = form.save(commit=False)
            student.user = user
            student.save()

            messages.success(request, "Student added successfully!")
            return redirect("admin_app:student_info")
    else:
        form = StudentForm()
    return render(request, "admin_app/register.html", {"form": form})


@staff_member_required
def student_edit(request, s_id):
    student = get_object_or_404(Student, pk=s_id)
    user = get_object_or_404(CustomUser, pk=student.user.id)
    student.user = user
    
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student_obj = form.save(commit=False)
            if form.cleaned_data.get("password"):
                student.user.set_password(form.cleaned_data["password"])
                student.user.save()
            student_obj.save()
            
            return redirect("admin_app:student_info")
    else:
        form = StudentForm(instance=student)
    return render(request, "admin_app/register.html", {"form": form})
        
@staff_member_required
def student_delete(request, s_id):
    student = get_object_or_404(Student, pk=s_id)
    student.delete()
    return redirect("admin_app:student_info")


@staff_member_required
def faculty_info(request):
    faculties = Faculty.objects.all()
    return render(request, "admin_app/faculty_info.html", {"faculties": faculties})

@staff_member_required
def faculty_add(request):
    if request.method == "POST":
        form = FacultyForm(request.POST, request.FILES)     # for upload image in html file
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not username:
            form.add_error("username", "Username is required.")
        if not email:
            form.add_error("email", "Email is required.")
        if not password:
            form.add_error("password", "Password is required.")

        if username and CustomUser.objects.filter(username=username).exists():
            form.add_error("username", "Username already exists")

        if form.is_valid():
            # Create CustomUser
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                role="faculty"
            )

            faculty = form.save(commit=False)
            faculty.user = user
            faculty.save()
            faculty.subjects.set(form.cleaned_data.get("subjects", []))

            messages.success(request, "faculty added successfully!")
            return redirect("admin_app:faculty_info")
    else:
        form = FacultyForm()
    return render(request, "admin_app/register.html", {"form": form})

@staff_member_required
def faculty_edit(request, f_id):
    faculty = get_object_or_404(Faculty, pk=f_id)
    user = get_object_or_404(CustomUser, pk=faculty.user.id)
    faculty.user = user
    
    if request.method == "POST":
        form = FacultyForm(request.POST, request.FILES, instance=faculty)
        if form.is_valid():
            faculty_obj = form.save(commit=False)
            
            # Update user email and password
            faculty_obj.user.email = form.cleaned_data['email']
            if form.cleaned_data.get("password"):
                faculty_obj.user.set_password(form.cleaned_data["password"])
            faculty_obj.user.save()
            
            # Save faculty and many-to-many relationships
            faculty_obj.save()
            faculty_obj.subjects.set(form.cleaned_data.get("subjects", []))
            
            return redirect("admin_app:faculty_info")
    else:
        form = FacultyForm(instance=faculty)

    return render(request, "admin_app/register.html", {"form": form})
        
@staff_member_required
def faculty_delete(request, f_id):
    faculty = get_object_or_404(Faculty, pk=f_id)
    faculty.delete()
    return redirect("admin_app:faculty_info")

@staff_member_required
def notification(request):
    if request.method == "POST":
        form = NotificationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("admin_app:admin_dashboard")
    else: 
        form = NotificationForm()
    return render(request, "admin_app/notification.html", {"form": form})

@staff_member_required
def leave(request):
    leaves = LeaveRequest.objects.all()
    return render(request, "admin_app/leave.html", {"leaves": leaves})

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def update_leave_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            leave_id = data.get("leave_id")
            new_status = data.get("status")

            leave = LeaveRequest.objects.get(id=leave_id)
            leave.status = new_status
            leave.save()

            return JsonResponse({"success": True})
        except Leave.DoesNotExist:
            return JsonResponse({"success": False, "error": "Leave not found"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


# Optional imports for barcode scanning
try:
    import cv2 # type: ignore
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

try:
    from pyzbar.pyzbar import decode # type: ignore
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
    decode = None

def scan_barcode(camera_index=0):
    """Scans a barcode and returns the student ID."""
    if not CV2_AVAILABLE or not PYZBAR_AVAILABLE:
        print("❌ Error: cv2 or pyzbar library not available. Please install them first.")
        return None
    
    print("📷 Starting camera...")

    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print("❌ Error: Camera not found or cannot be opened.")
        return None

    print("🔍 Scanning for student barcode... Press 'q' to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to capture frame. Exiting.")
            break

        barcodes = decode(frame)
        for barcode in barcodes:
            barcode_data = barcode.data.decode('utf-8')  # Extract student ID
            print(f"✅ Detected Barcode: {barcode_data}")

            # Draw a rectangle around the barcode
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"ID: {barcode_data}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cap.release()
            cv2.destroyAllWindows()
            return barcode_data  # Return scanned ID and exit loop

        # Display the frame with barcode detection
        cv2.imshow("Barcode Scanner", frame)

        # Press 'q' to exit scanning
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("👋 Exiting barcode scanner.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

@staff_member_required
def mark_faculty_attendance(request):
    """
    Faculty attendance marking for today
    Tracks faculty present/absent status during the session
    """
    # Initialize today's attendance tracking in session
    today_str = str(date.today())
    if 'faculty_attendance' not in request.session:
        request.session['faculty_attendance'] = {}
    
    if today_str not in request.session['faculty_attendance']:
        request.session['faculty_attendance'][today_str] = {}
    
    if request.method == 'POST':
        faculty_username = request.POST.get('faculty_username', '').strip().lower()
        action = request.POST.get('action', 'mark')
        
        if faculty_username:
            try:
                user = CustomUser.objects.get(username=faculty_username)
                faculty = Faculty.objects.get(user=user)
                
                # Handle mark or unmark action
                today_attendance = request.session['faculty_attendance'][today_str]
                faculty_key = str(faculty.id)
                
                if action == 'unmark':
                    # Remove attendance record
                    if faculty_key in today_attendance:
                        del today_attendance[faculty_key]
                    messages.success(request, f"Attendance unmarked for {faculty.name}")
                else:
                    # Mark as present
                    today_attendance[faculty_key] = {
                        'status': 'present',
                        'time': str(date.today())
                    }
                    messages.success(request, f"Faculty attendance noted for {faculty.name}")
                
                request.session['faculty_attendance'][today_str] = today_attendance
                request.session.modified = True
            except CustomUser.DoesNotExist:
                messages.error(request, f"No user found with username: {faculty_username}")
            except Faculty.DoesNotExist:
                messages.error(request, f"No faculty record found for username: {faculty_username}")
        else:
            messages.warning(request, "Please enter a faculty username")
        
        return redirect("admin_app:mark_faculty_attendance")
    
    # GET request - display the form with attendance list
    faculties = Faculty.objects.all().select_related('user').order_by('name')
    
    # Prepare attendance records with status from session
    attendance_dict = request.session['faculty_attendance'][today_str]
    attendances = []
    for faculty in faculties:
        faculty_key = str(faculty.id)
        status = attendance_dict.get(faculty_key, {}).get('status', 'absent')
        attendances.append({
            'faculty': faculty,
            'status': status
        })
    
    return render(request, "admin_app/mark_faculty_attendance.html", {
        "attendances": attendances,
        "date": date.today()
    })


@staff_member_required
def manage_timetable(request):
    """View and manage timetables for all departments and semesters"""
    from .models import Timetable
@staff_member_required
def manage_timetable(request):
    """Manage class timetables by department and semester"""
    
    # Get filter parameters
    selected_dept_id = request.GET.get('department')
    selected_sem = int(request.GET.get('semester', 1))
    
    # Get all departments from subjects
    departments = Department.objects.filter(subjects__isnull=False).distinct()
    
    # Set default department
    if selected_dept_id:
        try:
            dept = Department.objects.get(id=selected_dept_id)
        except Department.DoesNotExist:
            dept = departments.first()
    else:
        dept = departments.first()
    
    department_id = dept.id if dept else None
    
    # Get timetable entries through subject_offering -> subject -> department
    if department_id:
        timetable = Timetable.objects.filter(
            subject_offering__subject__department_id=department_id,
            subject_offering__subject__semester=selected_sem
        ).select_related('subject_offering', 'subject_offering__subject', 'subject_offering__faculty').order_by('day', 'start_time')
    else:
        timetable = Timetable.objects.none()
    
    # Organize by day
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    organized_timetable = {}
    
    for day in days:
        organized_timetable[day] = timetable.filter(day=day)
    
    # Get all semesters, subjects, and faculties for the modal
    semesters = range(1, 9)
    subject_offerings = SubjectOffering.objects.select_related('subject', 'faculty').order_by('subject__code')
    # Get all subjects from the department (not filtered by semester) so JS can filter them dynamically
    subjects = Subject.objects.filter(
        department_id=department_id
    ).order_by('semester', 'code') if department_id else Subject.objects.none()
    faculties = Faculty.objects.all().order_by('name')
    
    context = {
        'organized_timetable': organized_timetable,
        'days': days,
        'selected_dept': department_id,
        'selected_sem': selected_sem,
        'departments': departments,
        'semesters': semesters,
        'subject_offerings': subject_offerings,
        'subjects': subjects,
        'faculties': faculties,
    }
    
    return render(request, "admin_app/manage_timetable.html", context)


@staff_member_required
def add_timetable(request):
    """Add new timetable entry"""
    if request.method == 'POST':
        try:
            subject_offering_id = request.POST.get('subject_offering')
            subject_id = request.POST.get('subject')
            faculty_id = request.POST.get('faculty')
            academic_year = request.POST.get('academic_year')
            division = request.POST.get('division')
            day = request.POST.get('day')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            lecture_type = request.POST.get('lecture_type')
            room_number = request.POST.get('room_number', '')

            subject_offering = None
            if subject_offering_id:
                subject_offering = SubjectOffering.objects.get(id=subject_offering_id)
            else:
                if not all([subject_id, faculty_id, academic_year, division]):
                    messages.error(request, "Please select subject, faculty, academic year, and division.")
                    return redirect('admin_app:manage_timetable')

                subject = Subject.objects.get(id=subject_id)
                faculty = Faculty.objects.get(id=faculty_id)
                subject_offering, _ = SubjectOffering.objects.get_or_create(
                    subject=subject,
                    academic_year=academic_year,
                    division=division,
                    defaults={'faculty': faculty}
                )
            
            timetable = Timetable.objects.create(
                subject_offering=subject_offering,
                day=day,
                start_time=start_time,
                end_time=end_time,
                lecture_type=lecture_type,
                room_number=room_number
            )
            
            messages.success(request, f"Timetable entry added for {subject_offering.subject.code}")
        except SubjectOffering.DoesNotExist:
            messages.error(request, "Subject offering not found")
        except Exception as e:
            messages.error(request, f"Error adding timetable entry: {str(e)}")
        
        # Redirect back to manage_timetable
        return redirect('admin_app:manage_timetable')
    
    return redirect('admin_app:manage_timetable')


# Subject Management Views
@staff_member_required
@staff_member_required
def manage_subjects(request):
    """View all subjects organized by semester"""
    from .forms import SubjectForm
    
    subjects_by_semester = {}
    for i in range(1, 9):
        subjects_by_semester[i] = Subject.objects.filter(semester=i).order_by('code')
    
    return render(request, 'admin_app/manage_subjects.html', {
        'subjects_by_semester': subjects_by_semester
    })


@staff_member_required
def add_subject(request):
    """Add a new subject"""
    from .forms import SubjectForm
    
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f"Subject {subject.code} added successfully!")
            return redirect('admin_app:manage_subjects')
        else:
            messages.error(request, "Error adding subject. Please check the form.")
    else:
        form = SubjectForm()
    
    return render(request, 'admin_app/add_subject.html', {'form': form})


@staff_member_required
def edit_subject(request, subject_id):
    """Edit an existing subject"""
    from .forms import SubjectForm
    
    subject = get_object_or_404(Subject, pk=subject_id)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f"Subject {subject.code} updated successfully!")
            return redirect('admin_app:manage_subjects')
        else:
            messages.error(request, "Error updating subject. Please check the form.")
    else:
        form = SubjectForm(instance=subject)
    
    return render(request, 'admin_app/edit_subject.html', {'form': form, 'subject': subject})


@staff_member_required
def delete_subject(request, subject_id):
    """Delete a subject"""
    subject = get_object_or_404(Subject, pk=subject_id)
    
    if request.method == 'POST':
        subject_code = subject.code
        subject.delete()
        messages.success(request, f"Subject {subject_code} deleted successfully!")
        return redirect('admin_app:manage_subjects')
    
    return render(request, 'admin_app/delete_subject.html', {'subject': subject})