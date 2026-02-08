from django.core.management.base import BaseCommand
from admin_app.models import Student, FeeStructure
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create sample fee structure for all students'

    def add_arguments(self, parser):
        parser.add_argument(
            '--amount',
            type=float,
            default=5,
            help='Fee amount per semester (default: 5)'
        )

    def handle(self, *args, **options):
        amount = Decimal(str(options['amount']))
        
        students = Student.objects.all()
        
        if not students.exists():
            self.stdout.write(self.style.ERROR('No students found. Please add students first.'))
            return
        
        created_count = 0
        skipped_count = 0
        
        for student in students:
            self.stdout.write(f'\nProcessing student: {student.user.username} - {student.name}')
            
            for semester in range(1, 9):
                # Check if fee structure already exists
                existing = FeeStructure.objects.filter(
                    student=student,
                    semester=semester
                ).exists()
                
                if existing:
                    self.stdout.write(f'  Semester {semester}: Already exists (skipped)')
                    skipped_count += 1
                    continue
                
                # Create fee structure
                FeeStructure.objects.create(
                    student=student,
                    semester=semester,
                    fees_to_be_collected=amount,
                    refunded=0,
                    previously_paid=0,
                    paid=0,
                    outstanding=amount
                )
                
                self.stdout.write(self.style.SUCCESS(f'  Semester {semester}: Created (₹{amount})'))
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully created {created_count} fee structures'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠ Skipped {skipped_count} existing records'))
