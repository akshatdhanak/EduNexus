from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from collections import defaultdict
from datetime import datetime
from django.utils import timezone
from .models import ExamSchedule, ExamMarks, ExamType, Subject, Student


@staff_member_required
def manage_exams(request):
    """View and manage exams organized by semester and type"""
    
    exams = ExamSchedule.objects.all().select_related('subject', 'exam_type').order_by('subject__semester', 'exam_type', 'subject__name')
    
    # Organize exams by semester and exam type
    exams_by_semester = defaultdict(lambda: defaultdict(list))
    
    for exam in exams:
        exams_by_semester[exam.subject.semester][exam.exam_type.name].append(exam)
    
    # Get statistics
    total_exams = exams.count()
    total_marks_entered = ExamMarks.objects.filter(marks_obtained__isnull=False).count()
    total_students = Student.objects.count()
    
    # Convert defaultdict to regular dict for template
    exams_by_semester = {sem: dict(types) for sem, types in exams_by_semester.items()}
    semesters = sorted(exams_by_semester.keys()) if exams_by_semester else []

    # Precompute counts to avoid complex template math
    semester_counts = {}
    for sem, types in exams_by_semester.items():
        total_count = sum(len(exams_list) for exams_list in types.values())
        semester_counts[sem] = {
            'total': total_count,
            'types': {exam_type: len(exams_list) for exam_type, exams_list in types.items()}
        }
    
    # Get all subjects and exam types for adding new exams
    subjects = Subject.objects.all().order_by('name')
    exam_types = ExamType.objects.all().order_by('name')
    
    context = {
        'exams_by_semester': exams_by_semester,
        'semesters': semesters,
        'total_exams': total_exams,
        'total_marks_entered': total_marks_entered,
        'total_students': total_students,
        'subjects': subjects,
        'exam_types': exam_types,
        'semester_range': range(1, 9),
        'semester_counts': semester_counts,
    }
    
    return render(request, 'admin_app/manage_exams.html', context)


@staff_member_required
def add_exam(request):
    """Add a new exam"""
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        exam_type_id = request.POST.get('exam_type')
        max_marks = request.POST.get('max_marks', 100)
        passing_marks = request.POST.get('passing_marks', 40)
        
        try:
            subject = Subject.objects.get(id=subject_id)
            exam_type = ExamType.objects.get(id=exam_type_id)
            
            # Get default values for exam schedule
            academic_year = '2025-26'
            exam_date = datetime.now().date()
            start_time = datetime.now().time()
            end_time = datetime.now().time()
            duration_minutes = 120
            
            # Check if exam already exists
            exam_schedule, created = ExamSchedule.objects.get_or_create(
                subject=subject,
                exam_type=exam_type,
                academic_year=academic_year,
                defaults={
                    'exam_date': exam_date,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_minutes': duration_minutes,
                    'max_marks': int(max_marks),
                    'passing_marks': int(passing_marks),
                    'status': 'scheduled'
                }
            )
            
            if created:
                messages.success(request, f'✓ Exam scheduled successfully for {subject.name} ({exam_type.name})')
            else:
                # Update existing exam
                exam_schedule.max_marks = int(max_marks)
                exam_schedule.passing_marks = int(passing_marks)
                exam_schedule.save()
                messages.info(request, f'ℹ Exam already exists for {subject.name} ({exam_type.name}). Updated marks.')
                
        except Subject.DoesNotExist:
            messages.error(request, 'Subject not found')
        except ExamType.DoesNotExist:
            messages.error(request, 'Exam type not found')
        except Exception as e:
            messages.error(request, f'Error creating exam: {str(e)}')
    
    return redirect('admin_app:manage_exams')


@staff_member_required
def delete_exam(request, exam_id):
    """Delete an exam"""
    
    try:
        exam = ExamSchedule.objects.get(id=exam_id)
        exam_name = f"{exam.subject.name} - {exam.exam_type.name}"
        exam.delete()
        messages.success(request, f'✓ Exam "{exam_name}" deleted successfully')
    except ExamSchedule.DoesNotExist:
        messages.error(request, 'Exam not found')
    except Exception as e:
        messages.error(request, f'Error deleting exam: {str(e)}')
    
    return redirect('admin_app:manage_exams')
