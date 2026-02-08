from django.core.management.base import BaseCommand
from admin_app.models import Student, assign_subjects_by_semester

class Command(BaseCommand):
    help = 'Reassign all students to their proper semester-wise subjects'

    def handle(self, *args, **options):
        try:
            students = Student.objects.all()
            total = students.count()
            updated = 0
            
            for student in students:
                try:
                    assign_subjects_by_semester(student)
                    updated += 1
                    self.stdout.write(f"✓ Updated: {student.name} (Semester {student.semester})")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Error updating {student.name}: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully updated {updated}/{total} students!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
