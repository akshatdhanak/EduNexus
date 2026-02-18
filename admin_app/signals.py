"""
Auto-enrollment signal: whenever a Student is saved, ensure they are
enrolled in all SubjectOfferings that match their current semester,
division, and department.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='admin_app.Student')
def auto_enroll_student(sender, instance, created, **kwargs):
    """Auto-enroll student in semester subjects on create or update."""
    from admin_app.models import assign_subjects_by_semester
    try:
        if instance.degree_program and instance.semester:
            assign_subjects_by_semester(instance)
    except Exception:
        # Don't break student save if enrollment fails
        pass
