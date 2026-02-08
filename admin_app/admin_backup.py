from django.contrib import admin, messages
from django import forms
from .models import *

# Register your models here.

class StudentAdmin(admin.ModelAdmin):
    list_display = ("get_username", "get_email", "get_role", "name", "degree", "graduation_date")
    search_fields = ("user__username", "user__email", "id_no")
    readonly_fields = ("get_email", "get_role")

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = "Username"

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = "Email"

    def get_role(self, obj):
        return obj.user.role
    get_role.short_description = "Role"

    def save_model(self, request, obj, form, change):
        # Ensure that only students are added to Student table
        if obj.user.role != "student":
            messages.error(request, "Only users with the 'Student' role can be added to Students.")
            return
        super().save_model(request, obj, form, change)


class FacultyAdminForm(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = "__all__"
        widgets = {
            "subject": forms.CheckboxSelectMultiple,  # show checkboxes with labels aligned
        }


class FacultyAdmin(admin.ModelAdmin):
    list_display = ("get_username", "get_email", "get_role", "name", "department")
    search_fields = ("user__username", "user__email", "faculty_id")
    readonly_fields = ("get_email", "get_role")
    form = FacultyAdminForm

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = "Username"

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = "Email"

    def get_role(self, obj):
        return obj.user.role
    get_role.short_description = "Role"

    def save_model(self, request, obj, form, change):
        # Ensure that only faculty members are added to Faculty table
        if obj.user.role != "faculty":
            messages.error(request, "Only users with the 'Faculty' role can be added to Faculty.")
            return    
        super().save_model(request, obj, form, change)

class LeaveAdmin(admin.ModelAdmin):
    list_display = ("user", "reason", "status")
    ordering = ["status"]

class TimetableAdmin(admin.ModelAdmin):
    list_display = ("department", "semester", "day", "subject", "faculty", "start_time", "end_time", "slot_type", "room_number", "get_actions_display")
    list_filter = ("department", "semester", "day", "slot_type")
    search_fields = ("subject__name", "faculty__name", "room_number")
    ordering = ["department", "semester", "day", "start_time"]
    fieldsets = (
        ('Basic Info', {
            'fields': ('department', 'semester', 'day')
        }),
        ('Subject & Faculty', {
            'fields': ('subject', 'faculty', 'slot_type')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time')
        }),
        ('Room', {
            'fields': ('room_number',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subject', 'faculty')
    
    def get_actions_display(self, obj):
        return "Edit / Delete"
    get_actions_display.short_description = "Actions"

class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

class ExamAdmin(admin.ModelAdmin):
    list_display = ("subject", "semester", "exam_type", "max_marks")
    list_filter = ("semester", "exam_type", "subject")
    search_fields = ("subject__name",)
    fieldsets = (
        ('Exam Details', {
            'fields': ('subject', 'semester', 'exam_type', 'max_marks')
        }),
    )


class StudentExamMarksAdmin(admin.ModelAdmin):
    list_display = ("student", "exam", "marks_obtained", "entered_by")
    list_filter = ("exam__semester", "exam__exam_type")
    search_fields = ("student__user__username", "exam__subject__name")
    readonly_fields = ("entered_at",)
    fieldsets = (
        ('Student & Exam', {
            'fields': ('student', 'exam')
        }),
        ('Marks', {
            'fields': ('marks_obtained', 'entered_by')
        }),
        ('Meta', {
            'fields': ('entered_at',),
            'classes': ('collapse',)
        }),
    )


class StudentResultAdmin(admin.ModelAdmin):
    list_display = ("student", "semester", "subject", "total_marks", "grade", "gpa")
    list_filter = ("semester", "grade", "subject")
    search_fields = ("student__user__username", "subject__name")
    readonly_fields = ("grade", "gpa", "created_at", "updated_at")
    fieldsets = (
        ('Student & Subject', {
            'fields': ('student', 'semester', 'subject')
        }),
        ('Marks', {
            'fields': ('internal_marks', 'external_marks', 'practical_marks', 'total_marks')
        }),
        ('Result', {
            'fields': ('grade', 'gpa')
        }),
        ('Meta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


admin.site.register(Student, StudentAdmin)
admin.site.register(Faculty, FacultyAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Notification)
admin.site.register(Leave, LeaveAdmin)
admin.site.register(Attendance)
admin.site.register(Lecture)
admin.site.register(AttendanceFaculty)
admin.site.register(FeeStructure)
admin.site.register(FeeReceipt)
admin.site.register(Timetable, TimetableAdmin)
admin.site.register(Exam, ExamAdmin)
admin.site.register(StudentExamMarks, StudentExamMarksAdmin)
admin.site.register(StudentResult, StudentResultAdmin)
