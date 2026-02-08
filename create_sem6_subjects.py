#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project1.settings')
django.setup()

from admin_app.models import Department, Subject

# Get Computer Science department
dept = Department.objects.get(name='Computer Science')

# Create semester 6 subjects with unique names
subjects = [
    ('CS601', 'Deep Learning Applications', 6, 4, False),
    ('CS602', 'Distributed Systems', 6, 3, False),
    ('CS603', 'AI Fundamentals', 6, 4, True),
    ('CS604', 'Network Security', 6, 3, False),
    ('CS605', 'Advanced Databases', 6, 3, False),
    ('CS606', 'Cloud Infrastructure', 6, 4, True),
]

print("Creating Semester 6 subjects...")
for code, name, sem, creds, elec in subjects:
    s, created = Subject.objects.get_or_create(
        code=code,
        defaults={'name': name, 'semester': sem, 'credits': creds, 'is_elective': elec, 'department': dept}
    )
    status = 'Created' if created else 'Exists'
    print(f'  {status}: {code} - {name}')

print(f'\nTotal subjects: {Subject.objects.count()}')
print(f'\nSemester 6 subjects ({Subject.objects.filter(semester=6).count()}):')
for s in Subject.objects.filter(semester=6).order_by('code'):
    print(f'  - {s.code}: {s.name}')
