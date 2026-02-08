from django.core.management.base import BaseCommand
from admin_app.models import (
    Student, Faculty, Attendance, AttendanceFaculty, 
    Lecture, Timetable, Leave, Notification, FeeReceipt, FeeStructure
)
from registration.models import CustomUser


class Command(BaseCommand):
    help = 'Clear all user data, attendance data, and timetable entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will delete ALL user data, attendance records, and timetable entries. '
                    'Use --confirm flag to proceed.'
                )
            )
            return

        try:
            # Delete all attendance records
            deleted_count, _ = Attendance.objects.all().delete()
            self.stdout.write(f'Deleted {deleted_count} attendance records')

            # Delete all attendance faculty records
            deleted_count, _ = AttendanceFaculty.objects.all().delete()
            self.stdout.write(f'Deleted {deleted_count} faculty attendance records')

            # Delete all lecture records
            deleted_count, _ = Lecture.objects.all().delete()
            self.stdout.write(f'Deleted {deleted_count} lecture records')

            # Delete all timetable entries
            deleted_count, _ = Timetable.objects.all().delete()
            self.stdout.write(f'Deleted {deleted_count} timetable entries')

            # Delete all fee receipts
            deleted_count, _ = FeeReceipt.objects.all().delete()
            self.stdout.write(f'Deleted {deleted_count} fee receipt records')

            # Delete all fee structures
            deleted_count, _ = FeeStructure.objects.all().delete()
            self.stdout.write(f'Deleted {deleted_count} fee structure records')

            # Delete all leaves
            deleted_count, _ = Leave.objects.all().delete()
            self.stdout.write(f'Deleted {deleted_count} leave records')

            # Delete all notifications
            deleted_count, _ = Notification.objects.all().delete()
            self.stdout.write(f'Deleted {deleted_count} notification records')

            # Delete all students
            deleted_count, _ = Student.objects.all().delete()
            self.stdout.write(f'Deleted {deleted_count} student records')

            # Delete all faculty
            deleted_count, _ = Faculty.objects.all().delete()
            self.stdout.write(f'Deleted {deleted_count} faculty records')

            # Delete all custom users (except superusers)
            non_superusers = CustomUser.objects.filter(is_superuser=False)
            deleted_count = non_superusers.count()
            non_superusers.delete()
            self.stdout.write(f'Deleted {deleted_count} user accounts (preserved superusers)')

            self.stdout.write(self.style.SUCCESS('All data cleared successfully!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error occurred: {str(e)}'))
