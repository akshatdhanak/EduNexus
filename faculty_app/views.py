import csv
from collections import defaultdict
from datetime import datetime, date as date_type
from functools import wraps
from time import localtime
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from admin_app.models import Attendance, AttendanceFaculty, Faculty, Leave, Lecture, Notification, Student, Subject, Timetable, SubjectOffering, StudentEnrollment, ExamSchedule, ExamMarks
from admin_app.forms import AttendanceEditForm, LeaveForm, LectureForm, AttendanceFilterForm
from django.contrib import messages

from registration.models import CustomUser

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

# Create your views here.

def faculty_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("registration:login")  # Redirect unauthenticated users to login page

        if request.user.role == "faculty":
            return view_func(request, *args, **kwargs)

        logout(request)  # Log out unauthorized users
        return redirect("registration:login")  # Redirect unauthorized users
    return wrapper

@faculty_required
def faculty_dashboard(request):
    faculty = Faculty.objects.get(user=request.user)
    
    # Get last viewed timestamps from session
    last_notif_view = request.session.get('last_notification_view')
    last_leave_view = request.session.get('last_leave_view')
    
    # Count notifications created after last view
    if last_notif_view:
        from django.utils.dateparse import parse_datetime
        last_view_time = parse_datetime(last_notif_view)
        new_notifications = Notification.objects.filter(recipient_role='faculty', created_at__gt=last_view_time).count()
    else:
        # If never viewed, count recent ones (last 7 days)
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        new_notifications = Notification.objects.filter(recipient_role='faculty', created_at__gte=week_ago).count()
    
    # Count leave status updates after last view (faculty approves leaves, so no personal leaves)
    new_leave_updates = 0
    
    return render(request, "faculty_app/dashboard.html", {
        "username": request.user.username, 
        "faculty": faculty,
        "new_notifications": new_notifications,
        "new_leave_updates": new_leave_updates
    })

@faculty_required
@faculty_required
def profile(request):
    faculty = Faculty.objects.get(user=request.user)
    return render(request, "profile.html", {"obj": faculty})

@faculty_required
def edit_profile(request):
    """Allow faculty to edit their profile"""
    try:
        faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        messages.error(request, "Faculty profile not found.")
        return redirect("faculty_app:faculty_dashboard")
    
    if request.method == 'POST':
        # Update basic info
        faculty.name = request.POST.get('name', faculty.name)
        faculty.phone = request.POST.get('phone', faculty.phone)
        
        # Handle profile image
        if 'image' in request.FILES:
            faculty.image = request.FILES['image']
        
        faculty.save()
        
        # Update user email if provided
        user = request.user
        if request.POST.get('email'):
            user.email = request.POST.get('email')
            user.save()
        
        messages.success(request, "Profile updated successfully!")
        return redirect("faculty_app:profile")
    
    context = {
        'faculty': faculty,
        'user': request.user,
    }
    
    return render(request, "faculty_app/edit_profile.html", context)
    
@faculty_required
def view_attendance(request):
    faculty = Faculty.objects.get(user=request.user)
    attendance = Attendance.objects.filter(marked_by=faculty).order_by("-marked_date")
    return render(request, "faculty_app/view_attendance.html", {"attendance": attendance})



def scan_barcode(camera_index=0):
    print("Starting camera...")

    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print("Error: Camera not found or cannot be opened.")
        return None

    print("Scanning for student barcode... Press 'q' to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame. Exiting.")
            break

        barcodes = decode(frame)
        for barcode in barcodes:
            barcode_data = barcode.data.decode('utf-8')  # Extract student ID
            print(f"Detected Barcode: {barcode_data}")


            cap.release()
            cv2.destroyAllWindows()
            return barcode_data  # Return scanned ID and exit loop

        # Display the frame with barcode detection
        cv2.imshow("Barcode Scanner", frame)

        # Press 'q' to exit scanning
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting barcode scanner.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return None


@faculty_required
def mark_student_attendance(request):
    faculty = Faculty.objects.get(user=request.user)
    lectures_by_day = {}
    selected_subject = None
    selected_type = None
    selected_date = None

    if request.method == "POST":
        form = AttendanceFilterForm(request.POST, faculty=faculty)
        if form.is_valid():
            selected_subject = form.cleaned_data.get("subject")
            selected_type = form.cleaned_data.get("session_type") or None
            selected_date = form.cleaned_data.get("date")
            
            if selected_subject:
                # Find all timetable entries for this subject and faculty
                timetable_query = Timetable.objects.filter(
                    subject_offering__faculty=faculty,
                    subject_offering__subject=selected_subject
                )
                
                # Filter by session type if specified
                if selected_type:
                    timetable_query = timetable_query.filter(lecture_type=selected_type)
                
                # Group by day
                from collections import defaultdict
                by_day = defaultdict(list)
                
                for slot in timetable_query:
                    by_day[slot.day].append(slot)
                
                # Now create/get Lecture objects for these timetable slots
                lectures_by_day = {}
                for day, slots in by_day.items():
                    lectures = []
                    
                    # Get date range if selected_date is provided
                    if selected_date:
                        # Create lectures for that specific date if it matches the day
                        target_weekday = selected_date.strftime("%A").lower()
                        if target_weekday == day:
                            date_to_use = selected_date
                        else:
                            continue  # Skip this day if it doesn't match selected date
                    else:
                        # Use today's date or nearest upcoming date for this day
                        date_to_use = date_type.today()
                    
                    for slot in slots:
                        lecture, _ = Lecture.objects.get_or_create(
                            subject_offering=slot.subject_offering,
                            faculty=faculty,
                            date=date_to_use,
                            start_time=slot.start_time,
                            end_time=slot.end_time,
                            lecture_type=slot.lecture_type,
                            room_number=slot.room_number,
                        )
                        lectures.append(lecture)
                    
                    if lectures:
                        lectures_by_day[day] = lectures
    else:
        form = AttendanceFilterForm(faculty=faculty)
    
    return render(request, "faculty_app/mark_student_attendance.html", {
        "form": form,
        "lectures_by_day": lectures_by_day,
        "selected_subject": selected_subject,
        "selected_type": selected_type,
        "selected_date": selected_date,
    })


@faculty_required
def mark_student_attendance2(request, lecture_id):
    lecture = Lecture.objects.get(id=lecture_id)
    attendances = Attendance.objects.filter(lecture=lecture).select_related('student', 'student__user')
    
    if request.method == "POST":
        student_username = request.POST.get('student_username', '').strip().lower()
        
        if student_username:
            try:
                user = CustomUser.objects.get(username=student_username)
                student = Student.objects.get(user=user)
                
                # Check if student is enrolled in this subject offering
                if not student.enrollments.filter(
                    subject_offering=lecture.subject_offering,
                    status='active'
                ).exists():
                    messages.error(
                        request,
                        f"✗ {student.name} is not enrolled in {lecture.subject_offering.subject.name}"
                    )
                else:
                    attendance, created = Attendance.objects.get_or_create(
                        lecture=lecture,
                        student=student,
                        defaults={
                            "marked_by": request.user.faculty_profile if hasattr(request.user, 'faculty_profile') else None,
                            "status": "present",
                        },
                    )

                    if created:
                        messages.success(request, f"✓ Attendance created and marked for {student.name} ({student_username})")
                    else:
                        attendance.status = "present"
                        attendance.save(update_fields=["status"])
                        messages.success(request, f"✓ Attendance marked for {student.name} ({student_username})")

            except CustomUser.DoesNotExist:
                messages.error(request, f"✗ No user found with username {student_username}")
            except Student.DoesNotExist:
                messages.error(request, f"✗ No student record found for {student_username}")
            
            return redirect("faculty_app:mark_student_attendance2", lecture_id)
    
    # Get slot type information
    slot_type = lecture.lecture_type
    slot_type_display = lecture.get_lecture_type_display()
    
    context = {
        'lecture': lecture,
        'attendances': attendances,
        'slot_type': slot_type,
        'slot_type_display': slot_type_display,
    }
    return render(request, "faculty_app/mark_student_attendance2.html", context)


@faculty_required
def show_student_attendance(request):
    faculty = Faculty.objects.get(user=request.user)
    
    # Get filter parameters
    filter_type = request.GET.get('filter', 'all')  # all, theory, practical, tutorial
    selected_lecture_id = request.GET.get('lecture_id')
    
    # Get all lectures for this faculty
    lectures = Lecture.objects.filter(faculty=faculty).select_related('subject_offering', 'subject_offering__subject').order_by('-date')
    
    # Apply slot type filter
    if filter_type != 'all' and filter_type in ['theory', 'practical', 'tutorial']:
        lectures = lectures.filter(lecture_type=filter_type)
    
    # If a specific lecture is selected, show only that lecture's attendance
    if selected_lecture_id:
        lectures = lectures.filter(id=selected_lecture_id)
    
    # Build lecture data with attendance grouped by semester
    lecture_data = []
    for lecture in lectures:
        attendances = (
            Attendance.objects
            .filter(lecture=lecture)
            .select_related('student', 'student__user')
            .order_by('student__semester', 'student__name')
        )
        present_count = attendances.filter(status='present').count()
        total_count = attendances.count()

        # Group attendances by student semester
        semester_groups = defaultdict(list)
        for att in attendances:
            semester_groups[att.student.semester].append(att)

        ordered_groups = sorted(semester_groups.items(), key=lambda x: x[0])
        
        lecture_data.append({
            'lecture': lecture,
            'slot_type': lecture.lecture_type,
            'slot_type_display': lecture.get_lecture_type_display(),
            'attendances': attendances,
            'semester_groups': ordered_groups,
            'present_count': present_count,
            'total_count': total_count,
            'attendance_percentage': (present_count / total_count * 100) if total_count > 0 else 0,
        })
    
    context = {
        'lecture_data': lecture_data,
        'filter_type': filter_type,
        'selected_lecture_id': selected_lecture_id,
        'faculty': faculty,
    }
    return render(request, "faculty_app/show_student_attendance.html", context)


@faculty_required
def edit_student_attendance(request, attendance_id):
    attendance = get_object_or_404(Attendance, id=attendance_id)
    if request.method == "POST":
        form = AttendanceEditForm(request.POST)
        if(form.is_valid()):
            attendance.status = request.POST.get("status")
            attendance.save()
            return redirect("faculty_app:show_student_attendance")  # Redirect after update
    else:
        form = AttendanceEditForm(instance=attendance)
        return render(request, "faculty_app/edit_student_attendance.html", {"form": form, "attendance": attendance})

@faculty_required
def generate_report(request):
    faculty = Faculty.objects.get(user=request.user)
    
    # Prepare the HTTP response with CSV content
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{faculty.name}_attendance_report.csv"'

    # Create CSV writer
    writer = csv.writer(response)
    writer.writerow(["Student", "Roll Number", "Subject", "Date", "Lecture Time", "Status", "Marked On"])  # CSV Headers

    # Fetch attendance records marked by this faculty
    attendance_records = Attendance.objects.filter(marked_by=faculty).order_by("-marked_date")

    for record in attendance_records:
        writer.writerow([
            record.student.name,
            record.student.roll_number,
            record.lecture.subject_offering.subject.name,
            record.lecture.date.strftime("%Y-%m-%d"),
            f"{record.lecture.start_time.strftime('%H:%M')}-{record.lecture.end_time.strftime('%H:%M')}",
            record.status.capitalize(),
            record.marked_date.strftime("%Y-%m-%d %H:%M"),
        ])

    return response

@faculty_required
def show_notification(request):
    notifications = Notification.objects.filter(recipient_role="faculty").order_by("-created_at")
    # Mark notifications as viewed by storing current timestamp
    request.session['last_notification_view'] = timezone.now().isoformat()
    return render(request, "notifications.html", {"notifications": notifications})

@faculty_required
def request_leave(request):
    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.user = request.user
            leave.save()

            messages.success(request, "Leave request submitted successfully!")
            return redirect("faculty_app:faculty_dashboard")  
    else:
        form = LeaveForm()

    return render(request, "request_leave.html", {"form": form})

@faculty_required
def view_leave(request):
    faculty = Faculty.objects.get(user=request.user)
    # Faculty see all student leaves they can approve
    leaves = Leave.objects.all().order_by("-requested_date")
    # Mark leave status as viewed
    request.session['last_leave_view'] = timezone.now().isoformat()
    # Store IDs of viewed leaves to track which ones have been seen
    viewed_ids = [leave.id for leave in leaves.filter(status__in=['approved', 'rejected'])]
    request.session['viewed_leave_ids'] = viewed_ids
    return render(request, "view_leave.html", {"leaves": leaves})

@faculty_required
def view_timetable(request):
    """Display timetable for the logged-in faculty member"""
    from admin_app.models import Timetable
    
    try:
        faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        messages.error(request, "Faculty profile not found.")
        return redirect("faculty_app:faculty_dashboard")
    
    # Get timetable entries for this faculty member
    timetable = Timetable.objects.filter(
        faculty=faculty
    ).select_related('subject').order_by('day', 'start_time')
    
    # Organize by day
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    organized_timetable = {}
    
    for day in days:
        organized_timetable[day] = timetable.filter(day=day)
    
    context = {
        'faculty': faculty,
        'organized_timetable': organized_timetable,
        'days': days,
        'timetable_entries': timetable,
    }
    
    return render(request, "faculty_app/timetable.html", context)

@faculty_required
def enter_marks(request):
    """Faculty can enter exam marks for students"""
    try:
        faculty = Faculty.objects.get(user=request.user)

        # Get all exam schedules for subjects taught by this faculty
        subject_offerings = SubjectOffering.objects.filter(faculty=faculty)
        subjects = Subject.objects.filter(offerings__in=subject_offerings).distinct()
        exam_schedules = ExamSchedule.objects.filter(subject__in=subjects).order_by('-exam_date', 'subject')

        # Get selected exam and optional filters
        exam_id = request.GET.get('exam_id')
        exam = None
        students = []
        selected_division = request.GET.get('division') or None
        selected_degree = request.GET.get('degree_program') or None
        # UI filters: subject and exam type (for selection step)
        selected_subject_id = request.GET.get('subject_id') or None
        selected_exam_type_id = request.GET.get('exam_type_id') or None

        if exam_id:
            try:
                exam = ExamSchedule.objects.get(id=exam_id, subject__in=subjects)

                # Get students enrolled in this subject in the same semester
                semester = exam.subject.semester
                student_enrollments = StudentEnrollment.objects.filter(
                    subject_offering__subject=exam.subject,
                    student__semester=semester
                ).select_related('student')

                # If explicit enrollments exist, use them. Otherwise fall back to all students in that semester
                if student_enrollments.exists():
                    # apply optional filters to enrollments
                    if selected_division:
                        student_enrollments = student_enrollments.filter(student__division=selected_division)
                    if selected_degree:
                        student_enrollments = student_enrollments.filter(student__degree_program_id=selected_degree)
                    enrollment_iter = (enrollment.student for enrollment in student_enrollments)
                else:
                    # fallback: students in the same semester
                    fallback_qs = Student.objects.filter(semester=semester, status='active')
                    # If subject has a department, prefer students from that department only
                    subj_dept = getattr(exam.subject, 'department', None)
                    if subj_dept:
                        filtered_by_dept = fallback_qs.filter(degree_program__department=subj_dept)
                        # only apply department restriction if it yields results
                        if filtered_by_dept.exists():
                            fallback_qs = filtered_by_dept
                    if selected_division:
                        fallback_qs = fallback_qs.filter(division=selected_division)
                    if selected_degree:
                        fallback_qs = fallback_qs.filter(degree_program_id=selected_degree)
                    enrollment_iter = fallback_qs

                # Get or create marks for these students
                for student in enrollment_iter:
                    exam_mark, _ = ExamMarks.objects.get_or_create(
                        student=student,
                        exam_schedule=exam,
                        defaults={}
                    )
                    students.append({
                        'id': student.id,
                        'user': student.user,
                        'name': student.name,
                        'roll_number': student.roll_number,
                        'marks': exam_mark
                    })

            except ExamSchedule.DoesNotExist:
                messages.error(request, "Exam not found.")

        # Handle form submission for marks
        if request.method == 'POST' and exam:
            updated_count = 0
            for key, value in request.POST.items():
                if key.startswith('marks_'):
                    student_id = key.split('_', 1)[1]
                    marks = value.strip()
                    if marks:
                        try:
                            marks_val = float(marks)
                            if 0 <= marks_val <= exam.max_marks:
                                exam_mark = ExamMarks.objects.get(
                                    student_id=student_id,
                                    exam_schedule_id=exam.id
                                )
                                exam_mark.marks_obtained = marks_val
                                exam_mark.marked_by = faculty
                                exam_mark.marked_date = timezone.now()
                                exam_mark.is_marked = True
                                exam_mark.save()
                                updated_count += 1
                            else:
                                messages.warning(request, f"Marks for student must be between 0 and {exam.max_marks}")
                        except ValueError:
                            messages.warning(request, "Invalid marks value provided")

            if updated_count > 0:
                messages.success(request, f"✓ Successfully updated marks for {updated_count} student(s)")
                return redirect(f"{request.path}?exam_id={exam.id}")

        # prepare filter options: divisions and degree programs
        if exam:
            divisions = Student.objects.filter(semester=exam.subject.semester).values_list('division', flat=True).distinct()
            subj_dept = getattr(exam.subject, 'department', None)
            degree_programs = subj_dept.degree_programs.all() if subj_dept is not None else []
        else:
            divisions = Student.objects.none()
            degree_programs = []

        # Provide subject and exam type options for the selection step
        subjects_for_faculty = subjects
        exam_types_for_selected = []
        exams_for_display = exam_schedules
        if selected_subject_id:
            try:
                selected_subject_id = int(selected_subject_id)
                exams_for_display = exam_schedules.filter(subject_id=selected_subject_id)
                # gather available exam types for this subject
                exam_types_for_selected = exams_for_display.values_list('exam_type__id', 'exam_type__name').distinct()
            except ValueError:
                pass

        context = {
            'faculty': faculty,
            'exams': exams_for_display,
            'all_exams': exam_schedules,
            'exam': exam,
            'exam_id': exam_id,
            'students': students,
            'divisions': divisions,
            'degree_programs': degree_programs,
            'selected_division': selected_division,
            'selected_degree': selected_degree,
            'subjects': subjects_for_faculty,
            'selected_subject_id': selected_subject_id,
            'exam_types_for_selected': list(exam_types_for_selected),
            'selected_exam_type_id': selected_exam_type_id,
        }

        return render(request, 'faculty_app/enter_marks.html', context)

    except Faculty.DoesNotExist:
        messages.error(request, "Faculty profile not found.")
        return redirect("faculty_app:dashboard")