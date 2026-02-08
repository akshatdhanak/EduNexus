from django.urls import path, include

from . import views
from . import exam_views

app_name = "admin_app" 

urlpatterns = [
    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin_dashboard/manage_user/", views.manage_user, name="manage_user"),
    
    path("admin_dashboard/manage_user/faculty_info", views.faculty_info, name="faculty_info"),
    path("admin_dashboard/manage_user/faculty_add", views.faculty_add, name="faculty_add"),
    path("admin_dashboard/manage_user/<int:f_id>/faculty_edit", views.faculty_edit, name="faculty_edit"),
    path("admin_dashboard/manage_user/<int:f_id>/faculty_delete", views.faculty_delete, name="faculty_delete"),

    path("admin_dashboard/manage_user/student_info", views.student_info, name="student_info"),
    path("admin_dashboard/manage_user/student_add", views.student_add, name="student_add"),
    path("admin_dashboard/manage_user/<int:s_id>/student_edit", views.student_edit, name="student_edit"),
    path("admin_dashboard/manage_user/<int:s_id>/student_delete", views.student_delete, name="student_delete"),

    path("admin_dashboard/mark_faculty_attendance", views.mark_faculty_attendance, name="mark_faculty_attendance"),

    path("admin_dashboard/manage_user/notification", views.notification, name="notification"),
    path("admin_dashboard/manage_user/leave", views.leave, name="leave"),
    path("admin_dashboard/manage_user/update_leave_status", views.update_leave_status, name="update_leave_status"),
    path("admin_dashboard/manage_timetable", views.manage_timetable, name="manage_timetable"),
    path("admin_dashboard/add_timetable", views.add_timetable, name="add_timetable"),
    
    # Subject Management
    path("admin_dashboard/manage_subjects/", views.manage_subjects, name="manage_subjects"),
    path("admin_dashboard/manage_subjects/add/", views.add_subject, name="add_subject"),
    path("admin_dashboard/manage_subjects/<int:subject_id>/edit/", views.edit_subject, name="edit_subject"),
    path("admin_dashboard/manage_subjects/<int:subject_id>/delete/", views.delete_subject, name="delete_subject"),
    
    # Exam Management
    path("admin_dashboard/manage_exams/", exam_views.manage_exams, name="manage_exams"),
    path("admin_dashboard/manage_exams/add/", exam_views.add_exam, name="add_exam"),
    path("admin_dashboard/manage_exams/<int:exam_id>/delete/", exam_views.delete_exam, name="delete_exam"),

]
