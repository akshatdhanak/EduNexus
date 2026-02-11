from django.core.management.base import BaseCommand
from admin_app.models import Student, FeeStructure
from decimal import Decimal
from datetime import date


class Command(BaseCommand):
    help = "Populate fee structure for all students based on their current semester"

    def add_arguments(self, parser):
        parser.add_argument(
            '--amount',
            type=float,
            default=50000,
            help='Base fee amount per semester (default: 50000)'
        )

    def handle(self, *args, **options):
        base_amount = Decimal(str(options['amount']))
        students = Student.objects.all()
        today = date.today()
        academic_year = f"{today.year}-{str(today.year + 1)[-2:]}"
        
        if not students.exists():
            self.stdout.write(self.style.WARNING("No students found in database."))
            return
        
        created_count = 0
        updated_count = 0
        
        for student in students:
            current_semester = student.semester
            
            # Create fee structure for all semesters up to current semester
            for sem in range(1, current_semester + 1):
                # Check if fee structure already exists
                fee_structure, created = FeeStructure.objects.get_or_create(
                    student=student,
                    semester=sem,
                    academic_year=academic_year,
                    defaults={
                        'fees_to_be_collected': base_amount,
                        'refunded': Decimal('0'),
                        'previously_paid': Decimal('0'),
                        'paid': Decimal('0'),
                        'outstanding': base_amount,
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created fee structure for {student.user.username} - Semester {sem}"
                        )
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Fee structure already exists for {student.user.username} - Semester {sem}"
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Summary: {created_count} fee structures created, {updated_count} already existed."
            )
        )
