import os
import sys
import django

# Ensure project root is on sys.path so Django settings can be imported
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project1.settings')
django.setup()

from admin_app.models import ExamSchedule, StudentEnrollment, Student

EXAM_ID = 1

try:
    exam = ExamSchedule.objects.get(id=EXAM_ID)
    subj = exam.subject
    sem = getattr(subj, 'semester', None)
    print('Exam:', exam.id, str(exam))
    print('Subject:', getattr(subj, 'id', None), getattr(subj, 'name', repr(subj)))
    print('Subject semester:', sem)

    enroll_qs = StudentEnrollment.objects.filter(subject_offering__subject=subj)
    print('Enrollments for subject (count):', enroll_qs.count())
    for e in enroll_qs.select_related('student')[:50]:
        s = e.student
        print('ENROLL:', s.id, s.name, 'semester=', s.semester, 'division=', s.division, 'degree_program_id=', getattr(s.degree_program, 'id', None))

    # Now replicate the view fallback logic exactly as in views.enter_marks
    print('\n-- Replicating view fallback logic --')
    student_enrollments = StudentEnrollment.objects.filter(subject_offering__subject=subj, student__semester=sem).select_related('student')
    print('Explicit enrollments count:', student_enrollments.count())
    if student_enrollments.exists():
        for e in student_enrollments[:50]:
            s = e.student
            print('ENROLL:', s.id, s.name, 'semester=', s.semester, 'division=', s.division, 'degree_program_id=', getattr(s.degree_program, 'id', None))
    else:
        fallback_qs = Student.objects.filter(semester=sem, status='active')
        subj_dept = getattr(subj, 'department', None)
        print('Subject department:', getattr(subj_dept, 'id', None))
        if subj_dept:
            filtered_by_dept = fallback_qs.filter(degree_program__department=subj_dept)
            print('Filtered by dept count:', filtered_by_dept.count())
            if filtered_by_dept.exists():
                fallback_qs = filtered_by_dept
        print('Final fallback students count:', fallback_qs.count())
        for s in fallback_qs[:50]:
            print('STUD:', s.id, s.name, 'division=', s.division, 'degree_program_id=', getattr(s.degree_program, 'id', None))

except Exception as ex:
    print('ERROR:', ex)
