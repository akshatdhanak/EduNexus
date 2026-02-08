from django.core.management.base import BaseCommand
from registration.models import CustomUser
from admin_app.models import Faculty, Student, Subject, SubjectOffering, Semester, AcademicYear
from datetime import datetime


class Command(BaseCommand):
    help = 'Create test users for the system'

    def handle(self, *args, **options):
        # Create Academic Year
        academic_year, _ = AcademicYear.objects.get_or_create(
            year='2025-26',
            defaults={'start_date': datetime(2025, 1, 1), 'end_date': datetime(2026, 12, 31)}
        )
        
        # Create Semester
        semester, _ = Semester.objects.get_or_create(
            number=1,
            academic_year=academic_year
        )

        # Create Admin User
        admin_user, created = CustomUser.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user: admin / admin123'))
        else:
            self.stdout.write(self.style.WARNING('Admin user already exists'))

        # Create Teacher User
        teacher_user, created = CustomUser.objects.get_or_create(
            username='teacher',
            defaults={
                'email': 'teacher@example.com',
                'role': 'faculty',
                'first_name': 'John',
                'last_name': 'Doe'
            }
        )
        if created:
            teacher_user.set_password('teacher123')
            teacher_user.save()
            Faculty.objects.get_or_create(
                user=teacher_user,
                defaults={
                    'name': 'John Doe',
                    'email': 'teacher@example.com',
                    'department': 'Computer Science'
                }
            )
            self.stdout.write(self.style.SUCCESS('Created teacher user: teacher / teacher123'))
        else:
            self.stdout.write(self.style.WARNING('Teacher user already exists'))

        # Create Student User
        student_user, created = CustomUser.objects.get_or_create(
            username='student',
            defaults={
                'email': 'student@example.com',
                'role': 'student',
                'first_name': 'Jane',
                'last_name': 'Smith'
            }
        )
        if created:
            student_user.set_password('student123')
            student_user.save()
            Student.objects.get_or_create(
                user=student_user,
                defaults={
                    'name': 'Jane Smith',
                    'roll_number': 'CSE001',
                    'email': 'student@example.com',
                    'semester': 1
                }
            )
            self.stdout.write(self.style.SUCCESS('Created student user: student / student123'))
        else:
            self.stdout.write(self.style.WARNING('Student user already exists'))

        # Create Sample Subject
        subject, _ = Subject.objects.get_or_create(
            code='CS101',
            defaults={
                'name': 'Computer Networks',
                'credits': 4,
                'semester': 1
            }
        )

        # Create Subject Offering
        teacher_obj = Faculty.objects.filter(user__username='teacher').first()
        if teacher_obj:
            SubjectOffering.objects.get_or_create(
                subject=subject,
                semester=semester,
                faculty=teacher_obj
            )

        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))
