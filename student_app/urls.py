from django.urls import path, include
from . import views


app_name = "student_app" 

urlpatterns = [
    path("student_dashboard/", views.student_dashboard, name="student_dashboard"),
    path("profile/", views.profile, name="profile"),
    path("edit_profile/", views.edit_profile, name="edit_profile"),
    path("fee_dashboard/", views.fee_dashboard, name="fee_dashboard"),
    path("attendance_summary/", views.attendance_summary, name="attendance_summary"),
    path("view_timetable/", views.view_timetable, name="view_timetable"),
    # path("show_attendance/", views.show_attendance, name="show_attendance"),
    path("daily_attendance/", views.daily_attendance, name="daily_attendance"),
    path("subject_wise_attendance/", views.subject_wise_attendance, name="subject_wise_attendance"),
    path("generate_report/", views.generate_report, name="generate_report"),
    path("download_attendance/", views.generate_report, name="download_attendance"),
    path("show_notification/", views.show_notification, name="show_notification"),
    path("request_leave/", views.request_leave, name="request_leave"),
    path("view_leave/", views.view_leave, name="view_leave"),
    path("pay_fees/", views.pay_fees, name="pay_fees"),
    path("payment_success/", views.payment_success, name="payment_success"),
    path("download_receipt/<int:receipt_id>/", views.download_receipt, name="download_receipt"),
    path("view_marks/", views.view_marks, name="view_marks"),
    path("view_results/", views.view_results, name="view_results"),
    path("download_result/<int:semester>/", views.download_result, name="download_result"),
]
