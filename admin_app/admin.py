"""
Admin interface configuration for all unified database models
"""

from django.contrib import admin
from .models import (
    # Academic Structure
    Department, DegreeProgram, Subject, SubjectOffering,
    # Users & Profiles
    Student, Faculty,
    # Enrollment
    StudentEnrollment,
    # Exam Management
    ExamType, ExamSchedule, AdmitCard, ExamMarks,
    # Assessment
    InternalAssessment,
    # Attendance
    Lecture, Attendance,
    # Timetable
    Timetable,
    # Results
    SemesterResult, SubjectResult,
    # Finance
    FeeStructure, FeeReceipt,
    # Other
    LeaveRequest, Notification, AcademicCalendar
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'head', 'created_at')
    search_fields = ('name', 'code')


@admin.register(DegreeProgram)
class DegreeProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'department', 'duration_semesters')
    list_filter = ('department',)
    search_fields = ('name', 'code')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'semester', 'credits', 'is_elective')
    list_filter = ('semester', 'is_elective')
    search_fields = ('code', 'name')


@admin.register(SubjectOffering)
class SubjectOfferingAdmin(admin.ModelAdmin):
    list_display = ('subject', 'academic_year', 'division', 'faculty')
    list_filter = ('academic_year', 'division')
    search_fields = ('subject__code', 'academic_year')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('roll_number', 'name', 'semester', 'status')
    list_filter = ('semester', 'status')
    search_fields = ('roll_number', 'name', 'phone')


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'specialization', 'status')
    list_filter = ('status',)
    search_fields = ('name', 'email')


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject_offering', 'status', 'enrollment_date')
    list_filter = ('status', 'subject_offering__academic_year')
    search_fields = ('student__roll_number', 'subject_offering__subject__code')


@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_mandatory')


@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ('subject', 'exam_type', 'exam_date', 'start_time', 'status')
    list_filter = ('exam_type', 'exam_date', 'status')
    search_fields = ('subject__code', 'academic_year')
    date_hierarchy = 'exam_date'


@admin.register(AdmitCard)
class AdmitCardAdmin(admin.ModelAdmin):
    list_display = ('admit_number', 'student', 'exam_schedule', 'is_valid')
    list_filter = ('is_valid', 'exam_schedule__exam_date')
    search_fields = ('admit_number', 'student__roll_number')


@admin.register(ExamMarks)
class ExamMarksAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam_schedule', 'marks_obtained', 'is_marked')
    list_filter = ('is_marked', 'exam_schedule__exam_type')
    search_fields = ('student__roll_number', 'exam_schedule__subject__code')


@admin.register(InternalAssessment)
class InternalAssessmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject_offering', 'session_number', 'theory_marks', 'practical_marks')
    list_filter = ('session_number', 'academic_year')
    search_fields = ('student__roll_number', 'subject_offering__subject__code')


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ('subject_offering', 'date', 'lecture_type', 'faculty')
    list_filter = ('date', 'lecture_type')
    search_fields = ('subject_offering__subject__code', 'faculty__name')
    date_hierarchy = 'date'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'lecture', 'status', 'marked_by')
    list_filter = ('status', 'lecture__date')
    search_fields = ('student__roll_number', 'lecture__subject_offering__subject__code')
    date_hierarchy = 'lecture__date'


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('subject_offering', 'day', 'start_time', 'end_time', 'lecture_type')
    list_filter = ('day', 'lecture_type')
    search_fields = ('subject_offering__subject__code',)


@admin.register(SemesterResult)
class SemesterResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'academic_year', 'sgpa', 'status')
    list_filter = ('semester', 'academic_year', 'status')
    search_fields = ('student__roll_number', 'student__name')


@admin.register(SubjectResult)
class SubjectResultAdmin(admin.ModelAdmin):
    list_display = ('semester_result', 'subject', 'grade', 'gpa', 'status')
    list_filter = ('grade', 'status')
    search_fields = ('semester_result__student__roll_number', 'subject__code')


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'academic_year', 'fees_to_be_collected', 'paid', 'outstanding')
    list_filter = ('semester', 'academic_year')
    search_fields = ('student__roll_number', 'student__name')
    readonly_fields = ('outstanding',)


@admin.register(FeeReceipt)
class FeeReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'student', 'amount', 'payment_date', 'payment_mode')
    list_filter = ('payment_date', 'payment_mode')
    search_fields = ('receipt_number', 'student__roll_number', 'transaction_id')
    date_hierarchy = 'payment_date'


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'start_date', 'end_date', 'status', 'approved_by')
    list_filter = ('status', 'start_date')
    search_fields = ('student__roll_number', 'reason')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient_role', 'priority', 'created_at')
    list_filter = ('recipient_role', 'priority')
    search_fields = ('title', 'message')
    date_hierarchy = 'created_at'


@admin.register(AcademicCalendar)
class AcademicCalendarAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'semester', 'start_date', 'end_date')
    list_filter = ('academic_year', 'semester')
    search_fields = ('academic_year',)
