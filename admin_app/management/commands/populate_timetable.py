from django.core.management.base import BaseCommand
from admin_app.models import Subject, Faculty, Timetable
from datetime import time

class Command(BaseCommand):
    help = 'Populate timetable for all semesters of Computer Engineering'

    def handle(self, *args, **kwargs):
        # Clear existing timetable
        Timetable.objects.filter(department='CE').delete()
        
        # Get or create subjects for each semester
        # Semester 1
        sem1_subjects = {
            'Mathematics I': self.get_or_create_subject('Mathematics I'),
            'Basic Electrical Engineering for ICT': self.get_or_create_subject('Basic Electrical Engineering for ICT'),
            'Programming for Problem Solving I': self.get_or_create_subject('Programming for Problem Solving I'),
            'Engineering Graphics & Design for ICT': self.get_or_create_subject('Engineering Graphics & Design for ICT'),
            'Software Workshop': self.get_or_create_subject('Software Workshop'),
        }
        
        # Semester 2
        sem2_subjects = {
            'Mathematics II': self.get_or_create_subject('Mathematics II'),
            'Programming for Problem Solving II': self.get_or_create_subject('Programming for Problem Solving II'),
            'Physics for ICT': self.get_or_create_subject('Physics for ICT'),
            'Hardware Workshop': self.get_or_create_subject('Hardware Workshop'),
            'English': self.get_or_create_subject('English'),
            'Environmental Sciences': self.get_or_create_subject('Environmental Sciences'),
        }
        
        # Semester 3
        sem3_subjects = {
            'Data Structure and Algorithms': self.get_or_create_subject('Data Structure and Algorithms'),
            'Database Management Systems': self.get_or_create_subject('Database Management Systems'),
            'Design of Digital Circuit': self.get_or_create_subject('Design of Digital Circuit'),
            'Probability and Statistics': self.get_or_create_subject('Probability and Statistics'),
            'Universal Human Values': self.get_or_create_subject('Universal Human Values/ Financial and Managerial Accounting'),
            'Web Development Workshop': self.get_or_create_subject('Web Development Workshop'),
        }
        
        # Semester 4
        sem4_subjects = {
            'Discrete Mathematics': self.get_or_create_subject('Discrete Mathematics'),
            'Design and Analysis of Algorithm': self.get_or_create_subject('Design and Analysis of Algorithm'),
            'Computer System Architecture': self.get_or_create_subject('Computer System Architecture'),
            'Java Technology': self.get_or_create_subject('Java Technology / Visual Technology'),
            'Software Engineering Principles and Practices': self.get_or_create_subject('Software Engineering Principles and Practices'),
            'Software Project': self.get_or_create_subject('Software Project'),
        }
        
        # Semester 5
        sem5_subjects = {
            'Microprocessor Fundamental and Programming': self.get_or_create_subject('Microprocessor Fundamental and Programming'),
            'Web Development in .NET': self.get_or_create_subject('Web Development in .NET'),
            'Operating Systems': self.get_or_create_subject('Operating Systems'),
            'Advanced Algorithms': self.get_or_create_subject('Advanced Algorithms'),
            'Advanced Technologies': self.get_or_create_subject('Advanced Technologies'),
        }
        
        # Semester 6
        sem6_subjects = {
            'Network & Information Security': self.get_or_create_subject('Network & Information Security / Advanced Computer Architecture'),
            'Theory of Automata and Formal Languages': self.get_or_create_subject('Theory of Automata and Formal Languages'),
            'Service Oriented Computing': self.get_or_create_subject('Service Oriented Computing'),
            'Machine Learning': self.get_or_create_subject('Machine Learning'),
            'Computer Networks': self.get_or_create_subject('Computer Networks'),
            'System Design Practice': self.get_or_create_subject('System Design Practice'),
        }
        
        # Semester 7
        sem7_subjects = {
            'Artificial Intelligence': self.get_or_create_subject('Artificial Intelligence'),
            'Elective I': self.get_or_create_subject('Elective I'),
            'Elective II': self.get_or_create_subject('Elective II'),
            'Elective III': self.get_or_create_subject('Elective III'),
            'Compiler Construction': self.get_or_create_subject('Compiler Construction'),
        }
        
        # Semester 8
        sem8_subjects = {
            'Project/Industrial Training': self.get_or_create_subject('Project/Industrial Training'),
            'Seminar': self.get_or_create_subject('Seminar'),
            'Effective Technical Communication': self.get_or_create_subject('Effective Technical Communication'),
        }
        
        # Get sample faculty (or create placeholder)
        faculty = self.get_sample_faculty()
        
        # Create timetables for Semester 1
        self.create_semester_timetable(1, sem1_subjects, faculty)
        
        # Create timetables for Semester 2
        self.create_semester_timetable(2, sem2_subjects, faculty)
        
        # Create timetables for Semester 3
        self.create_semester_timetable(3, sem3_subjects, faculty)
        
        # Create timetables for Semester 4
        self.create_semester_timetable(4, sem4_subjects, faculty)
        
        # Create timetables for Semester 5
        self.create_semester_timetable(5, sem5_subjects, faculty)
        
        # Create timetables for Semester 6
        self.create_semester_timetable(6, sem6_subjects, faculty)
        
        # Create timetables for Semester 7
        self.create_semester_timetable(7, sem7_subjects, faculty)
        
        # Create timetables for Semester 8
        self.create_semester_timetable(8, sem8_subjects, faculty)
        
        self.stdout.write(self.style.SUCCESS('Successfully populated timetable for all semesters'))

    def get_or_create_subject(self, name):
        subject, created = Subject.objects.get_or_create(name=name)
        if created:
            self.stdout.write(f'Created subject: {name}')
        return subject

    def get_sample_faculty(self):
        # Try to get first available faculty or create a placeholder
        faculty = Faculty.objects.first()
        if not faculty:
            self.stdout.write(self.style.WARNING('No faculty found. Please add faculty members via admin panel.'))
            return None
        return faculty

    def create_semester_timetable(self, semester, subjects, faculty):
        """Create a sample timetable for a semester"""
        if not faculty:
            return
            
        subject_list = list(subjects.values())
        
        # Monday
        if len(subject_list) >= 5:
            self.create_slot('CE', semester, 'monday', subject_list[0], faculty, 'theory', time(8, 30), time(9, 30), 'Class-05')
            self.create_slot('CE', semester, 'monday', subject_list[1], faculty, 'theory', time(9, 30), time(10, 30), 'Class-05')
            self.create_slot('CE', semester, 'monday', subject_list[2], faculty, 'theory', time(10, 45), time(11, 45), 'Class-05')
            self.create_slot('CE', semester, 'monday', subject_list[3], faculty, 'theory', time(11, 45), time(12, 45), 'Class-05')
            self.create_slot('CE', semester, 'monday', subject_list[4], faculty, 'practical', time(13, 30), time(14, 30), 'Lab-1')
        
        # Tuesday
        if len(subject_list) >= 4:
            self.create_slot('CE', semester, 'tuesday', subject_list[0], faculty, 'theory', time(9, 30), time(10, 30), 'Class-05')
            self.create_slot('CE', semester, 'tuesday', subject_list[1], faculty, 'theory', time(10, 45), time(11, 45), 'Class-05')
            self.create_slot('CE', semester, 'tuesday', subject_list[2], faculty, 'theory', time(11, 45), time(12, 45), 'Class-05')
            self.create_slot('CE', semester, 'tuesday', subject_list[3], faculty, 'practical', time(13, 30), time(15, 30), 'Lab-1')
        
        # Wednesday
        if len(subject_list) >= 4:
            self.create_slot('CE', semester, 'wednesday', subject_list[0], faculty, 'theory', time(8, 30), time(9, 30), 'Class-05')
            self.create_slot('CE', semester, 'wednesday', subject_list[1], faculty, 'theory', time(9, 30), time(10, 30), 'Class-05')
            self.create_slot('CE', semester, 'wednesday', subject_list[2], faculty, 'theory', time(10, 45), time(11, 45), 'Class-05')
            self.create_slot('CE', semester, 'wednesday', subject_list[3], faculty, 'theory', time(11, 45), time(12, 45), 'Class-05')
        
        # Thursday
        if len(subject_list) >= 4:
            self.create_slot('CE', semester, 'thursday', subject_list[0], faculty, 'theory', time(8, 30), time(9, 30), 'Class-05')
            self.create_slot('CE', semester, 'thursday', subject_list[1], faculty, 'theory', time(9, 30), time(10, 30), 'Class-05')
            self.create_slot('CE', semester, 'thursday', subject_list[2], faculty, 'theory', time(10, 45), time(11, 45), 'Class-05')
            self.create_slot('CE', semester, 'thursday', subject_list[3], faculty, 'practical', time(13, 30), time(15, 30), 'Lab-1')
        
        # Friday
        if len(subject_list) >= 5:
            self.create_slot('CE', semester, 'friday', subject_list[0], faculty, 'theory', time(8, 30), time(9, 30), 'Class-05')
            self.create_slot('CE', semester, 'friday', subject_list[1], faculty, 'theory', time(9, 30), time(10, 30), 'Class-05')
            self.create_slot('CE', semester, 'friday', subject_list[2], faculty, 'theory', time(10, 45), time(11, 45), 'Class-05')
            self.create_slot('CE', semester, 'friday', subject_list[3], faculty, 'theory', time(11, 45), time(12, 45), 'Class-05')
            self.create_slot('CE', semester, 'friday', subject_list[4], faculty, 'practical', time(13, 30), time(16, 30), 'Lab-2')
        
        # Saturday
        if len(subject_list) >= 4:
            self.create_slot('CE', semester, 'saturday', subject_list[0], faculty, 'theory', time(8, 30), time(9, 30), 'Class-05')
            self.create_slot('CE', semester, 'saturday', subject_list[1], faculty, 'theory', time(9, 30), time(10, 30), 'Class-05')
            self.create_slot('CE', semester, 'saturday', subject_list[2], faculty, 'theory', time(10, 45), time(11, 45), 'Class-05')
            self.create_slot('CE', semester, 'saturday', subject_list[3], faculty, 'theory', time(11, 45), time(12, 45), 'Class-05')

    def create_slot(self, department, semester, day, subject, faculty, slot_type, start_time, end_time, room):
        try:
            Timetable.objects.create(
                department=department,
                semester=semester,
                day=day,
                subject=subject,
                faculty=faculty,
                slot_type=slot_type,
                start_time=start_time,
                end_time=end_time,
                room_number=room
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating slot: {e}'))
