#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project1.settings')
django.setup()

from admin_app.models import Department, Subject

# Check if departments exist
depts = Department.objects.all()
print(f"Existing departments: {depts.count()}")

# Create a default department if none exist
if depts.count() == 0:
    dept = Department.objects.create(name="Computer Science", code="CS")
    print(f"Created department: {dept.name} ({dept.code})")
else:
    dept = depts.first()
    print(f"Using existing department: {dept.name} ({dept.code})")

# Create sample subjects
subjects_data = [
    {"code": "CS101", "name": "Introduction to Programming", "semester": 1, "credits": 3, "is_elective": False},
    {"code": "CS102", "name": "Data Structures", "semester": 1, "credits": 4, "is_elective": False},
    {"code": "CS201", "name": "Database Management", "semester": 2, "credits": 3, "is_elective": False},
    {"code": "CS202", "name": "Web Development", "semester": 2, "credits": 4, "is_elective": True},
    {"code": "CS301", "name": "Operating Systems", "semester": 3, "credits": 4, "is_elective": False},
    {"code": "CS401", "name": "Advanced Algorithms", "semester": 4, "credits": 3, "is_elective": True},
]

for subject_data in subjects_data:
    subject, created = Subject.objects.get_or_create(
        code=subject_data["code"],
        defaults={
            "name": subject_data["name"],
            "semester": subject_data["semester"],
            "credits": subject_data["credits"],
            "is_elective": subject_data["is_elective"],
            "department": dept
        }
    )
    status = "✓ Created" if created else "✓ Already exists"
    print(f"{status}: {subject.code} - {subject.name}")

print(f"\nTotal subjects in database: {Subject.objects.count()}")
