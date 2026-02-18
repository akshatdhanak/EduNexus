import csv  
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from admin_app.models import Leave, Student, Attendance, Lecture, Faculty, Subject, Notification, Timetable
from django.http import HttpResponse
from django.utils.timezone import localtime
from admin_app.forms import LeaveForm
from .forms import StudentProfileForm
from django.db.models import Sum, Count, Q
# Create your views here.




# decoraters
def student_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("registration:login")  # Redirect unauthenticated users to login page

        if request.user.role == "student":
            return view_func(request, *args, **kwargs)

        logout(request)  # Log out unauthorized users
        return redirect("registration:login")  # Redirect unauthorized users
    return wrapper



@student_required
def student_dashboard(request):
    student = Student.objects.get(user=request.user)
    
    # Get last viewed timestamps from session
    last_notif_view = request.session.get('last_notification_view')
    last_leave_view = request.session.get('last_leave_view')
    
    # Count notifications created after last view
    if last_notif_view:
        from django.utils.dateparse import parse_datetime
        last_view_time = parse_datetime(last_notif_view)
        new_notifications = Notification.objects.filter(recipient_role='student', created_at__gt=last_view_time).count()
    else:
        # If never viewed, count recent ones (last 7 days)
        from datetime import timedelta
        from django.utils import timezone
        week_ago = timezone.now() - timedelta(days=7)
        new_notifications = Notification.objects.filter(recipient_role='student', created_at__gte=week_ago).count()
    
    # Count leave status updates after last view
    if last_leave_view:
        from django.utils.dateparse import parse_datetime
        last_view_time = parse_datetime(last_leave_view)
        # Count leaves that were updated (status changed) after last view
        new_leave_updates = Leave.objects.filter(
            student=student, 
            status__in=['approved', 'rejected']
        ).exclude(
            id__in=request.session.get('viewed_leave_ids', [])
        ).count()
    else:
        # If never viewed, show all approved/rejected
        new_leave_updates = Leave.objects.filter(student=student, status__in=['approved', 'rejected']).count()
    
    return render(request, "student_app/dashboard.html", {
        "username": request.user.username, 
        "student": student,
        "new_notifications": new_notifications,
        "new_leave_updates": new_leave_updates
    })

@student_required
def profile(request):
    student = Student.objects.get(user=request.user)
    return render(request, "profile.html", {"obj": student})

# @student_required
# def show_attendance(request):
#     attendance = Attendance.objects.filter(student=Student.objects.get(user=request.user))
#     return render(request, "student_app/show_attendance.html", {"attendance": attendance})

@student_required
def daily_attendance(request):
    student = Student.objects.get(user=request.user)
    
    attendance_records = Attendance.objects.filter(student=student).order_by("-lecture__date")

    daily_attendance = {}
    for record in attendance_records:
        date_key = record.lecture.date
        if date_key not in daily_attendance:
            daily_attendance[date_key] = []
        daily_attendance[date_key].append({
            "subject": record.lecture.subject_offering.subject.name,
            "status": record.status
        })

    return render(request, "student_app/daily_attendance.html", {
        "daily_attendance": daily_attendance
    })
@student_required
def subject_wise_attendance(request):
    student = Student.objects.get(user=request.user)
    subject_attendance = []

    # Get the subjects the student is enrolled in via subject offerings
    enrollments = student.enrollments.select_related("subject_offering__subject").filter(status="active")
    subjects = []
    seen_subject_ids = set()
    for enrollment in enrollments:
        subject = enrollment.subject_offering.subject
        if subject and subject.id not in seen_subject_ids:
            subjects.append(subject)
            seen_subject_ids.add(subject.id)

    for subject in subjects:
        lectures = Lecture.objects.filter(subject_offering__subject=subject)  # Get all lectures for the subject
        total_lectures = lectures.count()
        # print(total_lectures)
        attended_lectures = Attendance.objects.filter(
            student=student,
            lecture__subject_offering__subject=subject,
            status="present"
        ).count()

        # print(attended_lectures)

        attendance_percentage = round((attended_lectures / total_lectures) * 100, 2) if total_lectures > 0 else 0

        subject_attendance.append({
            'subject': subject.name,
            'attendance_percentage': attendance_percentage
        })
    
    return render(request, "student_app/subject_wise_attendance.html", {"subject_attendance": subject_attendance})


@student_required
def generate_report(request):
    student = Student.objects.get(user=request.user)
    
    # Prepare the HTTP response with CSV content
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{student.name}_attendance_report.csv"'

    # Create CSV writer
    writer = csv.writer(response)
    writer.writerow(["Date", "Subject", "Status"])  # CSV Headers

    # Fetch attendance records for the student
    attendance_records = Attendance.objects.filter(student=student).order_by("lecture__date")

    for record in attendance_records:
        writer.writerow([
            record.lecture.date.strftime("%Y-%m-%d"),  # Format date
            record.lecture.subject_offering.subject.name,
            record.status.capitalize(),
        ])

    return response

@student_required
def show_notification(request):
    notifications = Notification.objects.filter(recipient_role="student").order_by("-created_at")
    # Mark notifications as viewed by storing current timestamp
    from django.utils import timezone
    request.session['last_notification_view'] = timezone.now().isoformat()
    return render(request, "notifications.html", {"notifications": notifications})

@student_required
def request_leave(request):
    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.student = Student.objects.get(user=request.user)
            leave.save()

            messages.success(request, "Leave request submitted successfully!")
            return redirect("student_app:student_dashboard")  
    else:
        form = LeaveForm()

    return render(request, "request_leave.html", {"form": form})

@student_required
def view_leave(request):
    student = Student.objects.get(user=request.user)
    leaves = Leave.objects.filter(student=student).order_by("status")
    # Mark leave status as viewed
    from django.utils import timezone
    request.session['last_leave_view'] = timezone.now().isoformat()
    # Store IDs of viewed leaves to track which ones have been seen
    viewed_ids = [leave.id for leave in leaves.filter(status__in=['approved', 'rejected'])]
    request.session['viewed_leave_ids'] = viewed_ids
    return render(request, "view_leave.html", {"leaves": leaves})

@student_required
def edit_profile(request):
    """Allow students to edit their profile except username/ID"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect("student_app:student_dashboard")
    
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=student, user=request.user)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, "Profile updated successfully!")
            return redirect("student_app:profile")
    else:
        form = StudentProfileForm(instance=student, user=request.user)
    
    return render(request, "student_app/edit_profile.html", {"form": form, "student": student})

@student_required
def fee_dashboard(request):
    """Display fee dashboard with semester-wise breakdown and receipts"""
    from admin_app.models import FeeStructure, FeeReceipt
    from django.db.models import Sum
    from decimal import Decimal
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect("student_app:student_dashboard")
    
    # Get fee structure for all semesters
    fee_structure_qs = FeeStructure.objects.filter(student=student).order_by('semester')
    fee_structure = list(fee_structure_qs)

    # Compute display-only previously paid values across semesters
    running_paid = Decimal('0.00')
    for fee in fee_structure:
        fee.display_previously_paid = running_paid
        current_paid_total = (fee.previously_paid or 0) + (fee.paid or 0) - (fee.refunded or 0)
        running_paid += current_paid_total
    
    # Calculate totals
    totals = fee_structure_qs.aggregate(
        total_fees=Sum('fees_to_be_collected'),
        total_refunded=Sum('refunded'),
        total_previously_paid=Sum('previously_paid'),
        total_paid=Sum('paid'),
        total_outstanding=Sum('outstanding')
    )
    
    # Get all receipts
    receipts = FeeReceipt.objects.filter(student=student).order_by('-payment_date')
    
    context = {
        'student': student,
        'fee_structure': fee_structure,
        'totals': totals,
        'receipts': receipts,
    }
    
    return render(request, "student_app/fee_dashboard.html", context)


@student_required
def attendance_summary(request):
    """Display attendance summary with semester selector"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect("student_app:student_dashboard")
    
    # Get all subjects for the student via subject offerings
    enrollments = student.enrollments.select_related("subject_offering__subject").filter(status="active")
    subjects = []
    seen_subject_ids = set()
    for enrollment in enrollments:
        subject = enrollment.subject_offering.subject
        if subject and subject.id not in seen_subject_ids:
            subjects.append(subject)
            seen_subject_ids.add(subject.id)
    
    # Find which semesters have attendance data
    semesters_with_data = set()
    for subject in subjects:
        lectures = Lecture.objects.filter(subject_offering__subject=subject)
        if lectures.exists():
            # Check if student has any attendance records for this subject
            attendance_exists = Attendance.objects.filter(
                student=student,
                lecture__subject_offering__subject=subject
            ).exists()
            if attendance_exists:
                if subject.semester:
                    semesters_with_data.add(subject.semester)
    
    # If no semester data found, use student's current semester or default to 7
    if not semesters_with_data:
        if hasattr(student, 'semester') and student.semester:
            semesters_with_data.add(student.semester)
        else:
            semesters_with_data.add(7)  # Default to semester 7
    
    # Build semester list only for semesters with data
    all_semesters = []
    for sem in sorted(semesters_with_data):
        all_semesters.append({
            'number': sem,
            'label': f"Semester - {sem}"
        })
    
    # Get selected semester or default to highest semester with data
    selected_semester = request.GET.get('semester', None)
    if selected_semester is None:
        selected_semester = str(max(semesters_with_data))
    
    selected_semester = int(selected_semester)

    subjects_for_semester = [
        subject for subject in subjects
        if subject.semester == selected_semester
    ]
    
    # Build attendance data for each subject
    attendance_data = []
    total_conducted = 0
    total_present = 0
    total_absent = 0
    
    for subject in subjects_for_semester:
        # Get all lectures for this subject
        lectures = Lecture.objects.filter(subject_offering__subject=subject)
        
        # Get theory and practical lectures separately
        theory_lectures = lectures.count()  # Assume all are theory for now
        practical_lectures = 0  # Can be extended based on lecture type
        
        # Get attendance records for theory
        theory_attendance = Attendance.objects.filter(
            student=student,
            lecture__subject_offering__subject=subject
        )
        
        theory_conducted = theory_lectures
        theory_present = theory_attendance.filter(status='present').count()
        theory_absent = theory_attendance.filter(Q(status='absent') | Q(status='late')).count()
        theory_percentage = (theory_present / theory_conducted * 100) if theory_conducted > 0 else 0
        
        if theory_conducted > 0:
            attendance_data.append({
                'slot_type': 'Theory',
                'subject_name': subject.name,
                'conducted': theory_conducted,
                'present': theory_present,
                'absent': theory_absent,
                'percentage': round(theory_percentage, 2)
            })
            
            total_conducted += theory_conducted
            total_present += theory_present
            total_absent += theory_absent
        
        # Add practical if exists (placeholder for future implementation)
        # You can add logic here to separate practical lectures
    
    # Calculate overall percentage
    overall_percentage = (total_present / total_conducted * 100) if total_conducted > 0 else 0
    
    context = {
        'student': student,
        'all_semesters': all_semesters,
        'selected_semester': selected_semester,
        'attendance_data': attendance_data,
        'total_conducted': total_conducted,
        'total_present': total_present,
        'total_absent': total_absent,
        'overall_percentage': round(overall_percentage, 2),
    }
    
    return render(request, "student_app/attendance_summary.html", context)


@student_required
def view_timetable(request):
    """Display semester-wise timetable for student's department"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect("student_app:student_dashboard")

    if not student.degree_program:
        messages.warning(request, "Degree program not set. Please contact the administrator.")
        return redirect("student_app:student_dashboard")
    
    # Get selected semester or default to current
    selected_semester = student.semester
    
    # Get timetable for student's department and semester
    from django.db.models import Q

    division_value = student.division
    batch_value = student.batch or student.division
    timetable = Timetable.objects.filter(
        subject_offering__subject__semester=selected_semester,
        subject_offering__subject__department=student.degree_program.department,
    ).filter(
        Q(lecture_type__in=['theory', 'tutorial'], subject_offering__division=division_value) |
        Q(lecture_type='practical', subject_offering__division=batch_value)
    ).select_related("subject_offering__subject", "subject_offering__faculty").order_by('day', 'start_time')
    
    # Organize by day
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    organized_timetable = {}
    
    for day in days:
        organized_timetable[day] = timetable.filter(day=day)

    # Build grid-friendly time slots
    time_slot_keys = set()
    for slot in timetable:
        time_slot_keys.add(f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}")

    def _slot_sort_key(key):
        return key.split('-')[0]

    time_slots = []
    for key in sorted(time_slot_keys, key=_slot_sort_key):
        start_str, end_str = key.split('-')
        time_slots.append({
            'key': key,
            'start': start_str,
            'end': end_str,
        })

    timetable_grid = {day: {slot['key']: [] for slot in time_slots} for day in days}
    for slot in timetable:
        key = f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}"
        timetable_grid[slot.day][key].append(slot)
    
    # Only show the student's current semester
    all_semesters = [student.semester]
    
    context = {
        'student': student,
        'organized_timetable': organized_timetable,
        'days': days,
        'selected_semester': selected_semester,
        'all_semesters': all_semesters,
        'has_slots': timetable.exists(),
        'time_slots': time_slots,
        'timetable_grid': timetable_grid,
    }
    
    return render(request, "student_app/timetable.html", context)


@student_required
def pay_fees(request):
    """Show payment confirmation page"""
    from admin_app.models import FeeStructure
    
    if request.method == 'POST':
        try:
            student = Student.objects.get(user=request.user)
            semester = int(request.POST.get('semester'))
            amount = float(request.POST.get('amount'))
            
            # Get fee structure
            fee_structure = FeeStructure.objects.get(student=student, semester=semester)
            
            # Format amount for display
            amount = float(fee_structure.outstanding)
            
            context = {
                'amount': amount,
                'semester': semester,
                'student': student,
                'fee_structure': fee_structure,
            }
            
            return render(request, 'student_app/payment_page.html', context)
            
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found.")
            return redirect("student_app:fee_dashboard")
        except FeeStructure.DoesNotExist:
            messages.error(request, f"Fee structure not found for semester {request.POST.get('semester')}.")
            return redirect("student_app:fee_dashboard")
        except ValueError as e:
            messages.error(request, f"Invalid data: {str(e)}")
            return redirect("student_app:fee_dashboard")
        except Exception as e:
            messages.error(request, f"Error processing payment: {str(e)}")
            return redirect("student_app:fee_dashboard")
    
    messages.warning(request, "Invalid request method.")
    return redirect("student_app:fee_dashboard")


@student_required
def payment_success(request):
    """Process payment and mark as paid"""
    from admin_app.models import FeeStructure, FeeReceipt
    from datetime import datetime
    from decimal import Decimal
    import random
    
    if request.method == 'POST':
        try:
            student = Student.objects.get(user=request.user)
            semester = int(request.POST.get('semester'))
            amount = Decimal(str(request.POST.get('amount')))
            payment_method = request.POST.get('payment_method', 'online')
            
            # Get fee structure
            fee_structure = FeeStructure.objects.get(student=student, semester=semester)
            
            # Validate amount
            if amount <= 0:
                messages.error(request, "Invalid payment amount.")
                return redirect("student_app:fee_dashboard")
            
            if amount > fee_structure.outstanding:
                messages.error(request, "Payment amount exceeds outstanding balance.")
                return redirect("student_app:fee_dashboard")
            
            # Update paid amount
            fee_structure.paid += amount
            fee_structure.save()  # This will auto-calculate outstanding in model save()
            
            # Generate receipt number and transaction ID
            receipt_no = f"RCP{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
            txn_id = f"TXN{random.randint(100000000, 999999999)}"
            
            # Determine payment mode based on method
            payment_mode_map = {
                'card': 'online',
                'upi': 'online',
                'netbanking': 'online',
            }
            payment_mode = payment_mode_map.get(payment_method, 'online')
            
            # Create receipt
            FeeReceipt.objects.create(
                student=student,
                fee_structure=fee_structure,
                receipt_number=receipt_no,
                payment_date=datetime.now().date(),
                payment_mode=payment_mode,
                transaction_id=txn_id,
                bank_name='College Payment Gateway',
                amount=amount,
            )
            
            messages.success(request, f"✓ Payment Successful! Amount: ₹{amount:,.0f} | Receipt: {receipt_no} | Transaction: {txn_id}")
            return redirect("student_app:fee_dashboard")
            
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found.")
            return redirect("student_app:fee_dashboard")
        except FeeStructure.DoesNotExist:
            messages.error(request, f"Fee structure not found for semester {semester}.")
            return redirect("student_app:fee_dashboard")
        except ValueError as e:
            messages.error(request, "Invalid payment data provided.")
            return redirect("student_app:fee_dashboard")
        except Exception as e:
            messages.error(request, f"Payment processing failed: {str(e)}")
            return redirect("student_app:fee_dashboard")
    
    return redirect("student_app:fee_dashboard")


@student_required
def download_receipt(request, receipt_id):
    """Generate and download receipt as PDF"""
    from admin_app.models import FeeReceipt
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from io import BytesIO
    
    try:
        student = Student.objects.get(user=request.user)
        receipt = FeeReceipt.objects.get(id=receipt_id, student=student)
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Container for the PDF elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        # Header
        elements.append(Paragraph("COLLEGE PAYMENT RECEIPT", title_style))
        elements.append(Paragraph("Official Fee Payment Confirmation", subtitle_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Verified badge
        badge_style = ParagraphStyle(
            'Badge',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#2e7d32'),
            backColor=colors.HexColor('#e8f5e9'),
            borderColor=colors.HexColor('#2e7d32'),
            borderWidth=1,
            borderPadding=8,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph("✓ Payment Verified", badge_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Receipt details table
        data = [
            ['Receipt Number:', receipt.receipt_number, 'Transaction ID:', receipt.transaction_id or 'N/A'],
            ['Student Name:', student.name, 'Student ID:', student.user.username],
            ['Semester:', f'Semester {receipt.fee_structure.semester}', 'Payment Date:', receipt.payment_date.strftime('%d %B %Y')],
            ['Payment Mode:', receipt.get_payment_mode_display(), 'Payment Gateway:', receipt.bank_name or 'N/A'],
        ]
        
        table = Table(data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#666666')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#202124')),
            ('TEXTCOLOR', (3, 0), (3, -1), colors.HexColor('#202124')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.4*inch))
        
        # Amount section
        amount_style = ParagraphStyle(
            'Amount',
            parent=styles['Normal'],
            fontSize=36,
            textColor=colors.HexColor('#0d47a1'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=5
        )
        amount_label_style = ParagraphStyle(
            'AmountLabel',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#1565c0'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceBefore=10
        )
        
        # Amount box
        amount_data = [[Paragraph("AMOUNT PAID", amount_label_style)], [Paragraph(f"₹{receipt.amount:,.0f}", amount_style)]]
        amount_table = Table(amount_data, colWidths=[6*inch])
        amount_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e3f2fd')),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#1a73e8')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ]))
        
        elements.append(amount_table)
        elements.append(Spacer(1, 0.4*inch))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER
        )
        elements.append(Paragraph("<b>Note:</b> This is a computer-generated receipt and does not require a signature.", footer_style))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("For any queries, please contact the accounts department.", footer_style))
        elements.append(Spacer(1, 0.2*inch))
        
        timestamp_style = ParagraphStyle(
            'Timestamp',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#999999'),
            alignment=TA_CENTER
        )
        elements.append(Paragraph(f"Generated on {receipt.created_at.strftime('%d %B %Y at %I:%M %p')}", timestamp_style))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF data
        pdf = buffer.getvalue()
        buffer.close()
        
        # Return PDF response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Receipt_{receipt.receipt_number}.pdf"'
        return response
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect("student_app:fee_dashboard")
    except FeeReceipt.DoesNotExist:
        messages.error(request, "Receipt not found.")
        return redirect("student_app:fee_dashboard")
    except Exception as e:
        messages.error(request, f"Error generating receipt: {str(e)}")
        return redirect("student_app:fee_dashboard")


@student_required
def view_marks(request):
    """View exam marks for all subjects in all semesters"""
    from admin_app.models import ExamMarks
    
    try:
        student = Student.objects.get(user=request.user)
        
        # Get all marks for this student organized by semester
        all_marks = ExamMarks.objects.filter(student=student).select_related(
            'exam_schedule',
            'exam_schedule__subject',
            'exam_schedule__exam_type'
        ).order_by(
            '-exam_schedule__subject__semester',
            'exam_schedule__subject__name',
            'exam_schedule__exam_type__name'
        )
        
        # Organize by semester
        marks_by_semester = {}
        for mark in all_marks:
            sem = mark.exam_schedule.subject.semester
            if sem not in marks_by_semester:
                marks_by_semester[sem] = []
            marks_by_semester[sem].append(mark)
        
        # Get current semester
        current_semester = student.semester
        semesters = sorted(marks_by_semester.keys(), reverse=True)
        
        context = {
            'student': student,
            'marks_by_semester': marks_by_semester,
            'semesters': semesters,
            'current_semester': current_semester,
        }
        
        return render(request, 'student_app/view_marks.html', context)
    
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect("student_app:student_dashboard")


@student_required
def view_results(request):
    """View semester results with grades"""
    from admin_app.models import SemesterResult
    
    try:
        student = Student.objects.get(user=request.user)
        
        # Get all semester results for this student
        semester_results = SemesterResult.objects.filter(student=student).prefetch_related(
            'subject_results',
            'subject_results__subject'
        ).order_by('-semester')

        # Organize by semester
        results_by_semester = {}
        for sem_result in semester_results:
            results_by_semester[sem_result.semester] = {
                'subjects': list(sem_result.subject_results.all()),
                'semester_gpa': sem_result.sgpa,
                'total_subjects': sem_result.subject_results.count(),
            }
        
        semesters = sorted(results_by_semester.keys(), reverse=True)
        current_semester = student.semester
        
        context = {
            'student': student,
            'results_by_semester': results_by_semester,
            'semesters': semesters,
            'current_semester': current_semester,
        }
        
        return render(request, 'student_app/view_results.html', context)
    
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect("student_app:student_dashboard")


@student_required
def download_result(request, semester):
    """Download semester result as PDF"""
    from admin_app.models import SemesterResult
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from io import BytesIO
    
    try:
        student = Student.objects.get(user=request.user)
        sem_result = SemesterResult.objects.filter(student=student, semester=semester).prefetch_related(
            'subject_results',
            'subject_results__subject'
        ).first()

        if not sem_result or not sem_result.subject_results.exists():
            messages.error(request, "No results found for this semester.")
            return redirect("student_app:view_results")
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Header
        elements.append(Paragraph(f"SEMESTER {semester} RESULTS", title_style))
        elements.append(Paragraph(f"Student: {student.name} | ID: {student.user.username}", styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Results table
        data = [['Subject', 'Internal', 'External', 'Practical', 'Total', 'Grade', 'GPA']]
        
        total_gpa = 0
        for result in sem_result.subject_results.all():
            internal = f"{result.internal_marks:.1f}" if result.internal_marks else "-"
            external = f"{result.external_marks:.1f}" if result.external_marks else "-"
            practical = f"{result.practical_marks:.1f}" if result.practical_marks else "-"
            
            data.append([
                result.subject.name,
                internal,
                external,
                practical,
                f"{result.total_marks:.1f}",
                result.grade,
                str(result.gpa)
            ])
            total_gpa += result.gpa
        
        # Add GPA row
        total_subjects = sem_result.subject_results.count()
        avg_gpa = round(total_gpa / total_subjects, 2) if total_subjects else 0
        data.append(['', '', '', '', 'Average GPA:', '', str(avg_gpa)])
        
        table = Table(data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f0f0f0')]),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e3f2fd')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Result_Semester_{semester}_{student.user.username}.pdf"'
        return response
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect("student_app:student_dashboard")
    except Exception as e:
        messages.error(request, f"Error generating result: {str(e)}")
        return redirect("student_app:view_results")
