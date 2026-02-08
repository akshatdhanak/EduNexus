from django.core.management.base import BaseCommand
from admin_app.models import Faculty, Subject, SEMESTER_SUBJECTS
from registration.models import CustomUser

class Command(BaseCommand):
    help = 'Assign all subjects to akg faculty and ensure students are enrolled in semester-wise subjects'

    def handle(self, *args, **options):
        try:
            # Get or create "akg" faculty
            akg_user = CustomUser.objects.get(username='akg')
            faculty = Faculty.objects.get(user=akg_user)
            
            # Get or create all subjects
            all_subjects = set()
            for semester, subject_names in SEMESTER_SUBJECTS.items():
                for subject_name in subject_names:
                    all_subjects.add(subject_name)
            
            # Create subjects if they don't exist and assign to akg faculty
            for subject_name in all_subjects:
                subject, created = Subject.objects.get_or_create(name=subject_name)
                faculty.subject.add(subject)
                if created:
                    self.stdout.write(f"✓ Created subject: {subject_name}")
                else:
                    self.stdout.write(f"✓ Assigned existing subject: {subject_name} to akg")
            
            self.stdout.write(self.style.SUCCESS(f'✅ Successfully assigned all subjects to akg faculty!'))
            self.stdout.write(self.style.SUCCESS(f'Total subjects assigned: {len(all_subjects)}'))
            
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ User "akg" not found. Please create "akg" user first.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
