# Class Diagram - University Attendance & Exam Management System

## Class Relationships & Inheritance

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                         CLASS DIAGRAM - COMPLETE VIEW                         ║
╚════════════════════════════════════════════════════════════════════════════════╝


┌──────────────────────────────────┐
│          <<abstract>>             │
│         BaseEntity                │
├──────────────────────────────────┤
│ - id: Integer (PK)               │
│ - created_at: DateTime           │
│ - updated_at: DateTime           │
├──────────────────────────────────┤
│ + getAge(): Integer              │
│ + isRecent(): Boolean            │
└──────────────────────────────────┘
        △                    △
        │ inherits           │ inherits
        │                    │
        │                    │
    ┌───────────────────┐    ┌─────────────────────┐
    │      User         │    │   AcademicEntity    │
    ├───────────────────┤    ├─────────────────────┤
    │ - username*       │    │ - semester: Int     │
    │ - email*          │    │ - academic_year     │
    │ - password_hash   │    │ - status: ENUM      │
    │ - role: ENUM      │    └─────────────────────┘
    └───────────────────┘             △
            △                         │
            │                    ┌────┴──────────────┐
        ┌───┴────────────┐       │                   │
        │                │       │                   │
    ┌───────────┐   ┌──────────┐ │            ┌────────────┐
    │ Student   │   │ Faculty  │ │            │ Subject    │
    ├───────────┤   ├──────────┤ │            ├────────────┤
    │ - roll*   │   │ - name   │ │            │ - code*    │
    │ - name    │   │ - spec   │ │            │ - credits  │
    │ - phone   │   │ - salary │ │            │ - is_elec  │
    │ - blood   │   │ - image  │ │            │ - dept_id  │
    │ - dob     │   └──────────┘ │            └────────────┘
    │ - image   │        △       │
    │ - address │        │       │
    │ - parent  │        │       │
    │ - status  │   ┌────────────────────┐
    │ - division│   │ SubjectOffering    │
    │ - batch   │   ├────────────────────┤
    └───────────┘   │ - subject_id (FK)  │
         │          │ - faculty_id (FK)  │
         │          │ - division         │
         │          │ - academic_year    │
         │          │ - max_students     │
    ┌────┴─────┐    └────────────────────┘
    │           │              △
    │           │              │ offered_in
    │           │              │
    │    ┌──────┴──────────────┐
    │    │ StudentEnrollment   │
    │    ├─────────────────────┤
    │    │ - student_id (FK)   │
    │    │ - offering_id (FK)  │
    │    │ - enrollment_date   │
    │    │ - status: ENUM      │
    │    └─────────────────────┘
    │
    │   RELATIONSHIPS WITH EXAMS & MARKS
    │
    ├─→ ┌─────────────────────────┐
    │   │ InternalAssessment      │
    │   ├─────────────────────────┤
    │   │ - subject_offering (FK) │
    │   │ - theory_marks          │
    │   │ - practical_marks       │
    │   │ - session_number        │
    │   │ - entered_by (FK)       │
    │   └─────────────────────────┘
    │
    ├─→ ┌─────────────────────────┐
    │   │ Attendance              │
    │   ├─────────────────────────┤
    │   │ - lecture_id (FK)       │
    │   │ - status: ENUM          │
    │   │ - marked_by (FK)        │
    │   │ - face_recognized       │
    │   └─────────────────────────┘
    │
    ├─→ ┌─────────────────────────┐
    │   │ AdmitCard               │
    │   ├─────────────────────────┤
    │   │ - exam_schedule_id (FK) │
    │   │ - admit_number*         │
    │   │ - seat_number           │
    │   │ - is_valid: Boolean     │
    │   └─────────────────────────┘
    │        │
    │        └──→ ┌──────────────────┐
    │            │ ExamMarks        │
    │            ├──────────────────┤
    │            │ - admit_card (FK)│
    │            │ - marks_obtained │
    │            │ - marked_by (FK) │
    │            │ - marked_date    │
    │            └──────────────────┘
    │
    ├─→ ┌─────────────────────────┐
    │   │ SemesterResult          │
    │   ├─────────────────────────┤
    │   │ - semester: Int         │
    │   │ - sgpa: Decimal         │
    │   │ - status: ENUM          │
    │   │ - published: Boolean    │
    │   └─────────────────────────┘
    │        │
    │        └──→ ┌──────────────────┐
    │            │ SubjectResult    │
    │            ├──────────────────┤
    │            │ - subject (FK)   │
    │            │ - internal       │
    │            │ - external       │
    │            │ - practical      │
    │            │ - grade: ENUM    │
    │            │ - gpa: Decimal   │
    │            └──────────────────┘
    │
    ├─→ ┌─────────────────────────┐
    │   │ LeaveRequest            │
    │   ├─────────────────────────┤
    │   │ - start_date            │
    │   │ - end_date              │
    │   │ - reason                │
    │   │ - status: ENUM          │
    │   │ - approved_by (FK)      │
    │   └─────────────────────────┘
    │
    └─→ ┌─────────────────────────┐
        │ FeeStructure            │
        ├─────────────────────────┤
        │ - semester: Int         │
        │ - fees_collected        │
        │ - previously_paid       │
        │ - paid: Decimal         │
        │ - refunded: Decimal     │
        │ - outstanding: Decimal  │
        └─────────────────────────┘
             │
             └──→ ┌──────────────────┐
                 │ FeeReceipt       │
                 ├──────────────────┤
                 │ - receipt_no*    │
                 │ - amount         │
                 │ - payment_date   │
                 │ - payment_mode   │
                 │ - transaction_id │
                 └──────────────────┘


EXAM MANAGEMENT HIERARCHY
═════════════════════════════════════════

┌─────────────────────────┐
│    ExamType             │
├─────────────────────────┤
│ - name: String*         │
│ - description           │
│ - is_mandatory: Boolean │
├─────────────────────────┤
│ + getName(): String     │
└─────────────────────────┘
        △
        │ has_type
        │
    ┌───────────────────────────────┐
    │    ExamSchedule               │
    ├───────────────────────────────┤
    │ - subject_id (FK)*            │
    │ - exam_type_id (FK)*          │
    │ - exam_date*                  │
    │ - start_time                  │
    │ - end_time                    │
    │ - duration_minutes            │
    │ - max_marks                   │
    │ - passing_marks               │
    │ - room_number                 │
    │ - invigilator_id (FK)         │
    │ - status: ENUM                │
    ├───────────────────────────────┤
    │ + isUpcoming(): Boolean       │
    │ + isCompleted(): Boolean      │
    │ + getPassingPercentage()      │
    └───────────────────────────────┘
             │
        ┌────┴──────────────┐
        │                   │
        ▼                   ▼
    ┌──────────────┐  ┌──────────────┐
    │ AdmitCard    │  │ ExamMarks    │
    └──────────────┘  └──────────────┘


ACADEMIC STRUCTURE
═════════════════════════════════════════

┌──────────────────────────┐
│    Department            │
├──────────────────────────┤
│ - name: String*          │
│ - code: String*          │
│ - head_id (FK)           │
├──────────────────────────┤
│ + getHeadName(): String  │
└──────────────────────────┘
        △
        │ belongs_to
        │
┌──────────────────────────┐
│ DegreeProgram            │
├──────────────────────────┤
│ - name: String*          │
│ - code: String*          │
│ - duration_sem: Int      │
└──────────────────────────┘
        △
        │ enrolled_in
        │
    ┌───────────────────────────────┐
    │    Subject                    │
    ├───────────────────────────────┤
    │ - code: String*               │
    │ - name: String*               │
    │ - credits: Int                │
    │ - semester: Int               │
    │ - is_elective: Boolean        │
    │ - syllabus_url                │
    ├───────────────────────────────┤
    │ + getCredits(): Int           │
    │ + isMandatory(): Boolean      │
    │ + getSemester(): Int          │
    └───────────────────────────────┘


ATTENDANCE SYSTEM
═════════════════════════════════════════

┌──────────────────────────┐
│    Lecture               │
├──────────────────────────┤
│ - subject_offering (FK)  │
│ - date*                  │
│ - start_time             │
│ - end_time               │
│ - lecture_type: ENUM     │
│ - room_number            │
│ - faculty_id (FK)        │
│ - is_conducted: Boolean  │
├──────────────────────────┤
│ + getDuration(): Int     │
│ + getType(): String      │
└──────────────────────────┘
        │
        └──→ ┌──────────────────────┐
             │ Attendance           │
             ├──────────────────────┤
             │ - student_id (FK)    │
             │ - status: ENUM       │
             │ - marked_date        │
             │ - marked_by (FK)     │
             │ - face_recognized    │
             ├──────────────────────┤
             │ + isPresent(): Bool  │
             │ + isLate(): Boolean  │
             └──────────────────────┘


TIMETABLE
═════════════════════════════════════════

┌──────────────────────────────┐
│    Timetable                 │
├──────────────────────────────┤
│ - subject_offering_id (FK)   │
│ - day: ENUM (Mon-Sun)*       │
│ - start_time*                │
│ - end_time*                  │
│ - room_number                │
│ - lecture_type: ENUM         │
├──────────────────────────────┤
│ + isActiveOnDay(): Boolean   │
│ + getSlotDuration(): Int     │
└──────────────────────────────┘


CALENDAR & NOTIFICATIONS
═════════════════════════════════════════

┌──────────────────────────────┐
│    AcademicCalendar          │
├──────────────────────────────┤
│ - academic_year: String      │
│ - semester: Int              │
│ - start_date*                │
│ - end_date*                  │
│ - exam_start_date            │
│ - exam_end_date              │
│ - result_decl_date           │
├──────────────────────────────┤
│ + isCurrentSemester(): Bool  │
│ + getExamPeriod(): String    │
└──────────────────────────────┘

┌──────────────────────────────┐
│    Notification              │
├──────────────────────────────┤
│ - title: String*             │
│ - message: String*           │
│ - recipient_role: ENUM       │
│ - priority: ENUM             │
│ - created_by_id (FK)         │
│ - is_read: Boolean           │
├──────────────────────────────┤
│ + isUrgent(): Boolean        │
│ + isForRole(role): Boolean   │
└──────────────────────────────┘


KEY ENUMERATIONS
═════════════════════════════════════════

UserRole
├── ADMIN
├── FACULTY
└── STUDENT

StudentStatus
├── ACTIVE
├── GRADUATED
├── SUSPENDED
└── DROPPED

EnrollmentStatus
├── ACTIVE
├── COMPLETED
├── DROPPED
└── DEFERRED

ExamStatus
├── SCHEDULED
├── COMPLETED
├── CANCELLED
└── RESCHEDULED

ExamType
├── REGULAR
├── REMEDIAL
├── EXTERNAL
└── MAKEUP

AttendanceStatus
├── PRESENT
├── ABSENT
└── LATE

Grade
├── A_PLUS (10)
├── A (9)
├── B_PLUS (8)
├── B (7)
├── C (6)
└── F (0)

LeaveStatus
├── PENDING
├── APPROVED
├── REJECTED
└── EXPIRED

PaymentMode
├── ONLINE
├── CASH
├── CHECK
└── DEMAND_DRAFT


MULTIPLICITY SUMMARY
═════════════════════════════════════════

Student  1  ────────────────  N  Enrollment
Enrollment 1  ────────────────  N  Subject
Subject  1  ────────────────  N  Exam
Exam     1  ────────────────  N  AdmitCard
AdmitCard 1  ────────────────  N  ExamMarks
Student  1  ────────────────  N  Attendance
Lecture  1  ────────────────  N  Attendance
Subject  1  ────────────────  N  InternalAssessment
Student  1  ────────────────  N  InternalAssessment
Faculty  1  ────────────────  N  Lecture
Student  1  ────────────────  1  FeeStructure
FeeStructure 1  ────────────────  N  FeeReceipt
Student  1  ────────────────  N  LeaveRequest
Student  1  ────────────────  N  SemesterResult
SemesterResult 1  ────────────────  N  SubjectResult
Timetable N  ────────────────  1  SubjectOffering
```

---

## Class Hierarchy & Inheritance

```
BaseEntity (Abstract)
├─ Auditable Traits
│  ├─ created_at
│  ├─ updated_at
│  └─ is_active
│
└─ Common Behaviors
   ├─ getAge()
   ├─ isRecent()
   └─ getFormattedDate()


User (Abstract)
├─ Authentication
├─ Authorization  
│
├─ Student
│  └─ Academic Info
│     ├─ Enrollment
│     ├─ Marks
│     └─ Attendance
│
└─ Faculty
   └─ Teaching Info
      ├─ Subject Teaching
      ├─ Mark Entry
      └─ Attendance Marking


AcademicEntity (Abstract)
├─ Semester Info
├─ Year Info
├─ Status Tracking
│
├─ Subject
├─ SubjectOffering
└─ StudentEnrollment


ExamEntity (Abstract)
├─ Exam Information
├─ Schedule Data
│
├─ ExamSchedule
├─ AdmitCard
└─ ExamMarks


AssessmentEntity (Abstract)
├─ Marks Data
├─ Status Tracking
│
├─ InternalAssessment
├─ ExamMarks
└─ SubjectResult


FinancialEntity (Abstract)
├─ Payment Data
├─ Amount Tracking
│
├─ FeeStructure
└─ FeeReceipt
```

---

## Method Examples for Key Classes

```
┌────────────────────────────────┐
│        Student                 │
├────────────────────────────────┤
│ # Getters                      │
│ + getName(): String            │
│ + getRollNumber(): String      │
│ + getSemester(): Integer       │
│ + getCurrentGPA(): Decimal     │
│ + getAttendancePercentage():Decimal
│                                │
│ # Academic                     │
│ + enrollSubject(Subject):void  │
│ + getMarks(Exam): ExamMarks    │
│ + getSemesterResult():Result   │
│ + getExamSchedule(): List      │
│                                │
│ # Attendance                   │
│ + getAttendanceBySubject():Map │
│ + markPresent(Lecture):void    │
│ + getAbsentCount(): Integer    │
│                                │
│ # Finance                      │
│ + getFeeStructure(): FeeStruct │
│ + getOutstandingFees():Decimal │
│ + payFee(Amount): Receipt      │
│                                │
│ # Queries                      │
│ + isEligibleForExam():Boolean  │
│ + getMinimumAttendance():Decimal
│ + canRegisterSubject():Boolean │
└────────────────────────────────┘


┌────────────────────────────────┐
│        Faculty                 │
├────────────────────────────────┤
│ # Teaching                     │
│ + getSubjectsTeaching():List   │
│ + getLectures(Subject):List    │
│ + getStudentsInClass():List    │
│                                │
│ # Assessment                   │
│ + markAttendance():void        │
│ + enterMarks(ExamMarks):void   │
│ + recordInternalAssess():void  │
│ + generateReport():Report      │
│                                │
│ # Queries                      │
│ + canTeachSubject():Boolean    │
│ + getClassLoad(): Integer      │
│ + getStudentPerformance():Map  │
└────────────────────────────────┘


┌────────────────────────────────┐
│        ExamSchedule            │
├────────────────────────────────┤
│ # Getters                      │
│ + getExamCode(): String        │
│ + getDuration(): Integer       │
│ + getMaxMarks(): Decimal       │
│ + getPassingMarks(): Decimal   │
│                                │
│ # Validations                  │
│ + isUpcoming(): Boolean        │
│ + isCompleted(): Boolean       │
│ + canRegister(): Boolean       │
│ + isValid(): Boolean           │
│                                │
│ # Operations                   │
│ + generateAdmitCard():void     │
│ + recordMarks(Marks):void      │
│ + getStatistics(): Map         │
│ + getTopScorers(N): List       │
└────────────────────────────────┘


┌────────────────────────────────┐
│        Attendance              │
├────────────────────────────────┤
│ # Getters                      │
│ + getStatus(): String          │
│ + getPercentage(): Decimal     │
│ + getAbsentDays(): Integer     │
│                                │
│ # Mark Attendance              │
│ + markAsPresent():void         │
│ + markAsAbsent():void          │
│ + markAsLate():void            │
│                                │
│ # Reports                      │
│ + generateAttendReport():PDF   │
│ + isMinimumMaintained():Bool   │
│ + getUnexcusedAbsence():Int    │
└────────────────────────────────┘
```

---

## Associations & Cardinalities

| Association | From | To | Cardinality | Role |
|------------|------|-------|-------------|------|
| Teaches | Faculty | Subject | N:M | instructor |
| Enrolls | Student | Subject | N:M | learner |
| Takes | Student | Exam | N:M | examinee |
| Marks | Faculty | ExamMarks | 1:N | marker |
| Tracks | Lecture | Attendance | 1:N | tracked_in |
| Calculates | ExamMarks | SubjectResult | 1:1 | used_for |
| Pays | Student | FeeReceipt | 1:N | payer |
| Requests | Student | LeaveRequest | 1:N | requester |

---

## Benefits of This Class Structure

✅ **Single Responsibility** - Each class has one clear purpose  
✅ **DRY Principle** - BaseEntity eliminates duplicate code  
✅ **Encapsulation** - Data and methods bundled together  
✅ **Polymorphism** - Shared interface for common operations  
✅ **Maintainability** - Easy to locate and modify functionality  
✅ **Scalability** - New classes inherit common traits  
✅ **Type Safety** - Clear contracts for inter-class communication  
