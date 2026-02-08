from django.core.exceptions import ValidationError
from django.db import models
from datetime import datetime, date
from registration.models import CustomUser

# Create your models here.


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# Semester to Subject mapping - B. Tech. Computer Engineering
SEMESTER_SUBJECTS = {
    1: [
        "Mathematics I",
        "Basic Electrical Engineering for ICT",
        "Programming for Problem Solving I",
        "Engineering Graphics & Design for ICT",
        "Software Workshop"
    ],
    2: [
        "Mathematics II",
        "Programming for Problem Solving II",
        "Physics for ICT",
        "Hardware Workshop",
        "English",
        "Environmental Sciences"
    ],
    3: [
        "Data Structure and Algorithms",
        "Database Management Systems",
        "Design of Digital Circuit",
        "Probability and Statistics",
        "Universal Human Values/ Financial and Managerial Accounting",
        "Essence of Indian Knowledge Tradition",
        "Web Development Workshop"
    ],
    4: [
        "Discrete Mathematics",
        "Design and Analysis of Algorithm",
        "Computer System Architecture",
        "Java Technology / Visual Technology",
        "Software Engineering Principles and Practices",
        "Software Project"
    ],
    5: [
        "Microprocessor Fundamental and Programming",
        "Web Development in .NET",
        "Operating Systems",
        "Advanced Algorithms",
        "Advanced Technologies"
    ],
    6: [
        "Network & Information Security / Advanced Computer Architecture",
        "Theory of Automata and Formal Languages",
        "Service Oriented Computing",
        "Machine Learning",
        "Computer Networks",
        "System Design Practice"
    ],
    7: [
        "Artificial Intelligence",
        "Elective I",
        "Elective II",
        "Elective III",
        "Compiler Construction"
    ],
    8: [
        "Project/Industrial Training",
        "Seminar",
        "Effective Technical Communication"
    ],
}


def assign_subjects_by_semester(student):
    """Auto-assign subjects to student based on their semester"""
    semester = student.semester
    subject_names = SEMESTER_SUBJECTS.get(semester, [])
    
    if subject_names:
        # Clear existing subjects
        student.subjects.clear()
        # Add subjects for this semester
        for subject_name in subject_names:
            subject, created = Subject.objects.get_or_create(name=subject_name)
            student.subjects.add(subject)
    

# Student Table (Linked to CustomUser)
class Student(models.Model):
    DEGREE_CHOICES = [
        ("CE", "Computer Engineering"),
        ("IT", "Information Technology"),
        ("EC", "Electronics & Communication"),
    ]
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    ]
    BLOOD_GROUP_CHOICES = [
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="student_id")
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='photos/', default="ava3.jpg")
    mobile_no = models.CharField(max_length=15)
    degree = models.CharField(max_length=50, choices=DEGREE_CHOICES)
    semester = models.IntegerField(default=1, choices=[(i, f"Semester {i}") for i in range(1, 9)])
    graduation_date = models.DateField()
    subjects = models.ManyToManyField(Subject, blank=True)
    face_encoding = models.TextField(blank=True, null=True)  # Store face descriptors as JSON
    
    # Personal Information
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    religion = models.CharField(max_length=50, blank=True, null=True)
    caste = models.CharField(max_length=50, blank=True, null=True)
    mother_tongue = models.CharField(max_length=50, blank=True, null=True)
    
    # Address Information
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    
    # Parent Information
    father_name = models.CharField(max_length=100, blank=True, null=True)
    father_occupation = models.CharField(max_length=100, blank=True, null=True)
    father_mobile = models.CharField(max_length=15, blank=True, null=True)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    mother_occupation = models.CharField(max_length=100, blank=True, null=True)
    mother_mobile = models.CharField(max_length=15, blank=True, null=True)
    
    # Educational Qualification
    high_school_name = models.CharField(max_length=200, blank=True, null=True)
    high_school_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    high_school_year = models.IntegerField(blank=True, null=True)
    intermediate_name = models.CharField(max_length=200, blank=True, null=True)
    intermediate_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    intermediate_year = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.user.username + '-' + self.degree


class Faculty(models.Model):
    DEPARTMENT_CHOICES = [
        ("CE", "Computer Engineering"),
        ("IT", "Information Technology"),
        ("EC", "Electronics & Communication"),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="faculty")
    image = models.ImageField(upload_to='photos/', default="ava3.jpg")
    name = models.CharField(max_length=100)
    mobile_no = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    salary = models.IntegerField(default=0)
    subject = models.ManyToManyField(Subject, blank=True)

    def __str__(self):
        return self.user.username + '-' + self.department

class Notification(models.Model):
    NOTIFICATION_CHOICES = [
        ("student", "Student"),
        ("faculty", "Faculty"),
    ]
    # user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notification")
    title=models.CharField(max_length=255)
    message=models.TextField()
    to = models.CharField(max_length=10, choices=NOTIFICATION_CHOICES)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification: {self.to} - {self.title}" 
        
class Leave(models.Model):
    LEAVE_TYPE_CHOICES = [
        ("panding", "Panding"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="leave")
    reason = models.CharField(max_length=50)
    discription = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=LEAVE_TYPE_CHOICES, default="pending")

    def __str__(self):
        return self.user.username + '-' + self.status
    

class Lecture(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    timetable = models.ForeignKey("Timetable", on_delete=models.PROTECT, null=True, blank=True, related_name="lectures")
    date = models.DateTimeField(default=datetime.today)

    def clean(self):
        if self.timetable:
            if self.subject_id and self.subject_id != self.timetable.subject_id:
                raise ValidationError("Lecture subject must match the timetable slot subject.")
            if self.faculty_id and self.faculty_id != self.timetable.faculty_id:
                raise ValidationError("Lecture faculty must match the timetable slot faculty.")
            if self.date and self.date.strftime("%A").lower() != self.timetable.day:
                raise ValidationError("Lecture date does not match the timetable day.")

    def __str__(self):
        return f"{self.subject.name} - {self.date}"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendances")
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="marked_attendances")
    date = models.DateTimeField(default=datetime.today)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="absent")

    class Meta:
        unique_together = ('student', 'lecture')  # Ensures a student has only one record per subject per day

    def __str__(self):
        return f"{self.student.user.username} - {self.lecture.subject.name} - {self.date} - {self.status}"

class AttendanceFaculty(models.Model):
    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
    ]

    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="attendance_faculty")
    date = models.DateField(default=date.today)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="absent")

    class Meta:
        unique_together = ('faculty', 'date')

    def __str__(self):
        return f"{self.faculty.name} - {self.date} - {self.status}"

class FeeStructure(models.Model):
    """Semester-wise fee structure for students"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="fee_structure")
    semester = models.IntegerField()
    fees_to_be_collected = models.DecimalField(max_digits=10, decimal_places=2)
    refunded = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    previously_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    outstanding = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'semester')
        ordering = ['semester']

    def __str__(self):
        return f"{self.student.user.username} - Semester {self.semester}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate outstanding amount
        self.outstanding = self.fees_to_be_collected - self.paid - self.refunded
        super().save(*args, **kwargs)


class FeeReceipt(models.Model):
    """Payment receipts for fee payments"""
    PAYMENT_MODE_CHOICES = [
        ("cash", "Cash"),
        ("online", "Online"),
        ("rtgs", "RTGS/NEFT"),
        ("card", "Card"),
        ("cheque", "Cheque"),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="fee_receipts")
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name="receipts")
    receipt_no = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    semester = models.IntegerField()
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES)
    reference_no = models.CharField(max_length=100, blank=True, null=True)
    reference_date = models.DateField(blank=True, null=True)
    reference_bank = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Receipt {self.receipt_no} - {self.student.user.username}"


class Timetable(models.Model):
    """Semester-wise timetable for each department"""
    DAY_CHOICES = [
        ("monday", "Monday"),
        ("tuesday", "Tuesday"),
        ("wednesday", "Wednesday"),
        ("thursday", "Thursday"),
        ("friday", "Friday"),
        ("saturday", "Saturday"),
    ]
    
    SLOT_TYPE_CHOICES = [
        ("theory", "Theory"),
        ("practical", "Practical"),
        ("tutorial", "Tutorial"),
    ]
    
    department = models.CharField(max_length=50, choices=Student.DEGREE_CHOICES)
    semester = models.IntegerField()
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    slot_type = models.CharField(max_length=10, choices=SLOT_TYPE_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        ordering = ['day', 'start_time']
        unique_together = ['department', 'semester', 'day', 'start_time']

    def __str__(self):
        return f"{self.get_department_display()} - Sem {self.semester} - {self.day} - {self.subject.name}"

class Exam(models.Model):
    """Exams for each subject and semester"""
    EXAM_TYPE_CHOICES = [
        ("internal", "Internal Exam"),
        ("external", "External Exam"),
        ("practical", "Practical Exam"),
    ]
    
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="exams")
    semester = models.IntegerField()
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    max_marks = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('subject', 'semester', 'exam_type')
        ordering = ['semester', 'subject', 'exam_type']
    
    def __str__(self):
        return f"{self.subject.name} - Sem {self.semester} - {self.get_exam_type_display()}"


class StudentExamMarks(models.Model):
    """Student marks for each exam"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="exam_marks")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="student_marks")
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    entered_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)
    entered_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'exam')
        ordering = ['exam', 'student']
    
    def __str__(self):
        return f"{self.student.user.username} - {self.exam} - {self.marks_obtained}"


class StudentResult(models.Model):
    """Final result for each semester with grades"""
    GRADE_CHOICES = [
        ("A+", "A+ (90-100)"),
        ("A", "A (80-89)"),
        ("B+", "B+ (70-79)"),
        ("B", "B (60-69)"),
        ("C", "C (50-59)"),
        ("F", "F (Below 50)"),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="semester_results")
    semester = models.IntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    internal_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    external_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    practical_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, default="F")
    gpa = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'semester', 'subject')
        ordering = ['semester', 'student', 'subject']
    
    def __str__(self):
        return f"{self.student.user.username} - Sem {self.semester} - {self.subject.name} - {self.grade}"
    
    def calculate_grade_and_gpa(self):
        """Calculate grade and GPA based on total marks"""
        grade_mapping = {
            (90, 100): ("A+", 4.0),
            (80, 89): ("A", 3.7),
            (70, 79): ("B+", 3.3),
            (60, 69): ("B", 3.0),
            (50, 59): ("C", 2.0),
            (0, 49): ("F", 0.0),
        }
        
        for (min_marks, max_marks), (grade, gpa) in grade_mapping.items():
            if min_marks <= self.total_marks <= max_marks:
                self.grade = grade
                self.gpa = Decimal(str(gpa))
                break