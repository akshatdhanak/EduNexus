"""
Unified Database Models for University Attendance & Exam Management System
Based on normalized design with 23 core entities and proper relationships
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from datetime import datetime, date, timedelta
from decimal import Decimal
from registration.models import CustomUser


# ============================================================================
# ACADEMIC STRUCTURE ENTITIES
# ============================================================================

class Department(models.Model):
    """Academic departments"""
    name = models.CharField(max_length=200, unique=True)  # e.g., "Faculty of Technology"
    code = models.CharField(max_length=10, unique=True)   # e.g., "FoT"
    head = models.ForeignKey('Faculty', on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_departments')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class DegreeProgram(models.Model):
    """Degree programs offered"""
    name = models.CharField(max_length=200, unique=True)  # e.g., "B.Tech - Computer Engineering"
    code = models.CharField(max_length=10, unique=True)   # e.g., "CE"
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='degree_programs')
    duration_semesters = models.IntegerField(default=8)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['department', 'name']
    
    def __str__(self):
        return f"{self.name}"


class Subject(models.Model):
    """Course subjects"""
    code = models.CharField(max_length=20, unique=True)   # e.g., "23CE610"
    name = models.CharField(max_length=200, unique=True)  # e.g., "ADVANCED COMPUTER ARCHITECTURE"
    credits = models.IntegerField(default=4)
    semester = models.IntegerField(choices=[(i, f"Semester {i}") for i in range(1, 9)])
    is_elective = models.BooleanField(default=False)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='subjects')
    syllabus_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['semester', 'code']
        unique_together = ['code', 'department']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class SubjectOffering(models.Model):
    """Instance of a subject in an academic year/division"""
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='offerings')
    academic_year = models.CharField(max_length=10)  # e.g., "2025-26"
    division = models.CharField(max_length=5)  # e.g., "A", "B", "C"
    faculty = models.ForeignKey('Faculty', on_delete=models.PROTECT, related_name='teaching_subjects')
    max_students = models.IntegerField(default=60)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['academic_year', 'subject', 'division']
        unique_together = ['subject', 'academic_year', 'division']
    
    def __str__(self):
        return f"{self.subject.code} - {self.academic_year} - Div {self.division}"
    
    def get_enrolled_count(self):
        return self.enrollments.filter(status='active').count()


# ============================================================================
# USER & PROFILE ENTITIES
# ============================================================================

class Student(models.Model):
    """Student profile linked to User"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('graduated', 'Graduated'),
        ('suspended', 'Suspended'),
        ('dropped', 'Dropped'),
    ]
    BATCH_CHOICES = [
        ('A1', 'A1'),
        ('A2', 'A2'),
        ('A3', 'A3'),
        ('A4', 'A4'),
        ('B1', 'B1'),
        ('B2', 'B2'),
        ('B3', 'B3'),
        ('B4', 'B4'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    roll_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    degree_program = models.ForeignKey(DegreeProgram, on_delete=models.PROTECT, related_name='enrolled_students', null=True, blank=True)
    semester = models.IntegerField(choices=[(i, f"Semester {i}") for i in range(1, 9)], default=1)
    division = models.CharField(max_length=5)  # A, B, C, etc.
    batch = models.CharField(max_length=10, choices=BATCH_CHOICES)
    graduation_date = models.DateField(blank=True, null=True)
    
    # Contact
    phone = models.CharField(max_length=15)
    
    # Personal Info
    blood_group = models.CharField(max_length=3, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Address
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    
    # Parents
    father_name = models.CharField(max_length=100, blank=True, null=True)
    father_contact = models.CharField(max_length=15, blank=True, null=True)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    mother_contact = models.CharField(max_length=15, blank=True, null=True)
    
    # Media
    image = models.ImageField(upload_to='student_photos/', default='default_student.jpg')
    face_encoding = models.TextField(blank=True, null=True)  # JSON encoded face descriptor
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['degree_program', 'semester', 'roll_number']
    
    def __str__(self):
        return f"{self.roll_number} - {self.name}"
    
    def get_current_enrollment(self):
        """Get current active subject enrollments"""
        return self.enrollments.filter(status='active')
    
    def get_attendance_percentage(self, subject_offering=None):
        """Calculate attendance percentage"""
        if subject_offering:
            lectures = Lecture.objects.filter(subject_offering=subject_offering)
            attendance = Attendance.objects.filter(
                student=self,
                lecture__in=lectures,
                status='present'
            ).count()
            total = lectures.count()
        else:
            attendance = Attendance.objects.filter(
                student=self,
                status='present'
            ).count()
            total = Attendance.objects.filter(student=self).count()
        
        return (attendance / total * 100) if total > 0 else 0


class Faculty(models.Model):
    """Faculty profile linked to User"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='faculty_profile')
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='faculties', null=True, blank=True)
    specialization = models.CharField(max_length=200, blank=True, null=True)
    subjects = models.ManyToManyField(Subject, blank=True, related_name='qualified_faculties')
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to='faculty_photos/', default='default_faculty.jpg')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}"
    
    def get_teaching_subjects(self, academic_year=None):
        """Get subjects being taught by this faculty"""
        query = self.teaching_subjects.all()
        if academic_year:
            query = query.filter(academic_year=academic_year)
        return query


# ============================================================================
# ENROLLMENT ENTITY
# ============================================================================

class StudentEnrollment(models.Model):
    """Student enrollment in subject offerings"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('deferred', 'Deferred'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    subject_offering = models.ForeignKey(SubjectOffering, on_delete=models.PROTECT, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['subject_offering', 'student']
        unique_together = ['student', 'subject_offering']
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.subject_offering.subject.code}"


def assign_subjects_by_semester(student, academic_year=None):
    """Enroll a student into subject offerings for their semester/division."""
    if student is None:
        return

    if academic_year is None:
        today = date.today()
        year = today.year
        next_year = str(year + 1)[-2:]
        academic_year = f"{year}-{next_year}"

    subjects = Subject.objects.filter(
        semester=student.semester,
        department=student.degree_program.department,
    )

    if not subjects.exists():
        return

    for subject in subjects:
        offering_qs = SubjectOffering.objects.filter(
            subject=subject,
            academic_year=academic_year,
            division=student.division,
        )

        if offering_qs.exists():
            offering = offering_qs.first()
        else:
            preferred_faculty = subject.qualified_faculties.first()
            fallback_faculty = Faculty.objects.first()
            faculty = preferred_faculty or fallback_faculty
            if faculty is None:
                continue

            offering, _ = SubjectOffering.objects.get_or_create(
                subject=subject,
                academic_year=academic_year,
                division=student.division,
                defaults={"faculty": faculty},
            )

        enrollment, created = StudentEnrollment.objects.get_or_create(
            student=student,
            subject_offering=offering,
            defaults={"status": "active"},
        )
        if not created and enrollment.status != "active":
            enrollment.status = "active"
            enrollment.save(update_fields=["status"])


# ============================================================================
# EXAM MANAGEMENT ENTITIES
# ============================================================================

class ExamType(models.Model):
    """Types of exams"""
    name = models.CharField(max_length=50, unique=True)  # Regular, Remedial, External
    description = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class ExamSchedule(models.Model):
    """Exam schedule and details"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='exam_schedules')
    exam_type = models.ForeignKey(ExamType, on_delete=models.PROTECT, related_name='exam_schedules')
    academic_year = models.CharField(max_length=10)  # e.g., "2025-26"
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.IntegerField()
    max_marks = models.IntegerField(default=100)
    passing_marks = models.IntegerField(default=40)
    room_number = models.CharField(max_length=20, blank=True, null=True)
    invigilator = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='invigilated_exams')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['exam_date', 'start_time', 'subject']
        unique_together = ['subject', 'exam_type', 'academic_year']
    
    def __str__(self):
        return f"{self.subject.code} - {self.exam_type.name} - {self.exam_date}"
    
    def is_upcoming(self):
        return self.exam_date > date.today()
    
    def is_completed(self):
        return self.status == 'completed' or self.exam_date <= date.today()


class AdmitCard(models.Model):
    """Exam admit cards"""
    exam_schedule = models.ForeignKey(ExamSchedule, on_delete=models.PROTECT, related_name='admit_cards')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='admit_cards')
    admit_number = models.CharField(max_length=50, unique=True)
    seat_number = models.CharField(max_length=20, blank=True, null=True)
    issue_date = models.DateField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['exam_schedule', 'student']
        unique_together = ['exam_schedule', 'student']
    
    def __str__(self):
        return f"{self.admit_number}"


class ExamMarks(models.Model):
    """Student marks for exams"""
    admit_card = models.OneToOneField(AdmitCard, on_delete=models.CASCADE, related_name='marks', null=True, blank=True)
    exam_schedule = models.ForeignKey(ExamSchedule, on_delete=models.PROTECT, related_name='marks')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_marks')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_marked = models.BooleanField(default=False)
    marked_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='marked_exams')
    marked_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['exam_schedule', 'student']
        unique_together = ['exam_schedule', 'student']
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.exam_schedule.subject.code} - {self.marks_obtained}"


# ============================================================================
# ASSESSMENT ENTITIES
# ============================================================================

class InternalAssessment(models.Model):
    """Internal continuous assessment"""
    subject_offering = models.ForeignKey(SubjectOffering, on_delete=models.CASCADE, related_name='internal_assessments')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='internal_assessments')
    academic_year = models.CharField(max_length=10)
    session_number = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3')])  # Three sessions
    theory_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    practical_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    entered_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='entered_internal_marks')
    entered_date = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['subject_offering', 'student', 'session_number']
        unique_together = ['subject_offering', 'student', 'academic_year', 'session_number']
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.subject_offering.subject.code} - Session {self.session_number}"
    
    def get_total_marks(self):
        total = Decimal('0.00')
        if self.theory_marks:
            total += self.theory_marks
        if self.practical_marks:
            total += self.practical_marks
        return total


# ============================================================================
# ATTENDANCE ENTITIES
# ============================================================================

class Lecture(models.Model):
    """Classroom lectures/sessions"""
    TYPE_CHOICES = [
        ('theory', 'Theory'),
        ('practical', 'Practical'),
        ('tutorial', 'Tutorial'),
    ]
    
    subject_offering = models.ForeignKey(SubjectOffering, on_delete=models.CASCADE, related_name='lectures')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    lecture_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='theory')
    room_number = models.CharField(max_length=20, blank=True, null=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT, related_name='conducted_lectures')
    is_conducted = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.subject_offering.subject.code} - {self.date} - {self.lecture_type}"
    
    def get_duration_minutes(self):
        from datetime import datetime, timedelta
        start = datetime.combine(date.today(), self.start_time)
        end = datetime.combine(date.today(), self.end_time)
        return int((end - start).total_seconds() / 60)


class Attendance(models.Model):
    """Student attendance in lectures"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]
    
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='absent')
    marked_date = models.DateTimeField(auto_now=True)
    marked_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='marked_attendances')
    face_recognized = models.BooleanField(default=False, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['lecture', 'student']
        unique_together = ['lecture', 'student']
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.lecture} - {self.status}"


# ============================================================================
# TIMETABLE ENTITY
# ============================================================================

class Timetable(models.Model):
    """Weekly schedule for subject offerings"""
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ]
    
    TYPE_CHOICES = [
        ('theory', 'Theory'),
        ('practical', 'Practical'),
        ('tutorial', 'Tutorial'),
    ]
    
    subject_offering = models.ForeignKey(SubjectOffering, on_delete=models.CASCADE, related_name='timetable_slots')
    day = models.CharField(max_length=20, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=20, blank=True, null=True)
    lecture_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='theory')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['subject_offering', 'day', 'start_time']
    
    def __str__(self):
        return f"{self.subject_offering.subject.code} - {self.day} - {self.start_time}-{self.end_time}"


# ============================================================================
# RESULTS ENTITIES
# ============================================================================

class SemesterResult(models.Model):
    """Semester-wise results"""
    STATUS_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('incomplete', 'Incomplete'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='semester_results')
    semester = models.IntegerField()
    academic_year = models.CharField(max_length=10)
    sgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='incomplete')
    result_date = models.DateField(null=True, blank=True)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['student', 'semester']
        unique_together = ['student', 'semester', 'academic_year']
    
    def __str__(self):
        return f"{self.student.roll_number} - Sem {self.semester} - {self.sgpa}"


class SubjectResult(models.Model):
    """Subject-wise results within a semester"""
    GRADE_CHOICES = [
        ('A+', 'A+ (90-100)'),
        ('A', 'A (80-89)'),
        ('B+', 'B+ (70-79)'),
        ('B', 'B (60-69)'),
        ('C', 'C (50-59)'),
        ('F', 'F (Below 50)'),
    ]
    
    STATUS_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ]
    
    semester_result = models.ForeignKey(SemesterResult, on_delete=models.CASCADE, related_name='subject_results')
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='results')
    internal_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    external_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    practical_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, default='F')
    gpa = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='fail')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['semester_result', 'subject']
        unique_together = ['semester_result', 'subject']
    
    def __str__(self):
        return f"{self.semester_result.student.roll_number} - {self.subject.code} - {self.grade}"


# ============================================================================
# FINANCE ENTITIES
# ============================================================================

class FeeStructure(models.Model):
    """Fee structure for students"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_structures')
    semester = models.IntegerField()
    academic_year = models.CharField(max_length=10)
    fees_to_be_collected = models.DecimalField(max_digits=10, decimal_places=2)
    previously_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refunded = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    outstanding = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-academic_year', 'semester']
        unique_together = ['student', 'semester', 'academic_year']
    
    def __str__(self):
        return f"{self.student.roll_number} - Sem {self.semester} - {self.academic_year}"
    
    def save(self, *args, **kwargs):
        self.outstanding = self.fees_to_be_collected - self.paid - self.refunded
        super().save(*args, **kwargs)


class FeeReceipt(models.Model):
    """Payment receipts"""
    MODE_CHOICES = [
        ('online', 'Online'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('dd', 'Demand Draft'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_receipts')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='receipts')
    receipt_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.receipt_number} - {self.student.roll_number}"


# ============================================================================
# LEAVE MANAGEMENT ENTITY
# ============================================================================

class LeaveRequest(models.Model):
    """Student leave requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approval_date = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    requested_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-requested_date']
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.start_date} to {self.end_date}"


# ============================================================================
# NOTIFICATION ENTITY
# ============================================================================

class Notification(models.Model):
    """System notifications"""
    ROLE_CHOICES = [
        ('faculty', 'Faculty'),
        ('student', 'Student'),
        ('all', 'All'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    recipient_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='all')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    created_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient_role}"


# ============================================================================
# ACADEMIC CALENDAR ENTITY
# ============================================================================

class AcademicCalendar(models.Model):
    """Academic year and semester calendar"""
    academic_year = models.CharField(max_length=10, unique=True)  # e.g., "2025-26"
    semester = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    exam_start_date = models.DateField()
    exam_end_date = models.DateField()
    result_declaration_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-academic_year', 'semester']
        unique_together = ['academic_year', 'semester']
    
    def __str__(self):
        return f"{self.academic_year} - Semester {self.semester}"
    
    def is_current_semester(self):
        return self.start_date <= date.today() <= self.end_date


# ============================================================================
# LEGACY COMPATIBILITY ALIASES
# ============================================================================
AttendanceFaculty = Attendance  # Alias for backward compatibility
Leave = LeaveRequest  # Alias for backward compatibility
