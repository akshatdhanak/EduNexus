"""
AI Database Chat Assistant — Powered by Google Gemini LLM
Natural Language → SQL/ORM Pipeline with Schema Awareness

Architecture:
  1. Dynamic schema introspection (reads actual DB structure)
  2. User asks a question in plain English
  3. Gemini LLM receives the question + full DB schema + sample data
  4. LLM generates Django ORM code
  5. Safe sandboxed execution with blocked writes
  6. LLM explains the results in human-friendly language
  7. Conversation history for follow-up questions
"""

import json
import re
import time
import traceback
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import wraps

import google.generativeai as genai
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Count, Avg, Sum, Max, Min, Q, F, Value, CharField
from django.db.models.functions import Concat, Lower, Upper, Coalesce
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .models import (
    AcademicCalendar,
    AdmitCard,
    Attendance,
    Department,
    DegreeProgram,
    ExamMarks,
    ExamSchedule,
    ExamType,
    Faculty,
    FeeReceipt,
    FeeStructure,
    InternalAssessment,
    Lecture,
    LeaveRequest,
    Notification,
    SemesterResult,
    Student,
    StudentEnrollment,
    Subject,
    SubjectOffering,
    SubjectResult,
    Timetable,
)


# ======================================================================
# ACCESS CONTROL
# ======================================================================

def admin_or_faculty_required(view_func):
    """Restrict to admin/faculty users."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("registration:login")
        if request.user.role not in ("admin", "faculty") and not request.user.is_superuser:
            return redirect("registration:login")
        return view_func(request, *args, **kwargs)
    return wrapper


def authenticated_required(view_func):
    """Allow any authenticated user (student, faculty, admin)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("registration:login")
        return view_func(request, *args, **kwargs)
    return wrapper


# ======================================================================
# DYNAMIC SCHEMA INTROSPECTION — reads actual DB structure
# ======================================================================

_CACHED_SCHEMA = None
_CACHED_SCHEMA_TIME = None
SCHEMA_CACHE_SECONDS = 300  # Re-introspect every 5 minutes


def introspect_database_schema():
    """
    Dynamically read all tables, columns, types, and relationships
    from the actual SQLite database. Keeps the AI always in sync.
    """
    global _CACHED_SCHEMA, _CACHED_SCHEMA_TIME

    now = datetime.now()
    if _CACHED_SCHEMA and _CACHED_SCHEMA_TIME:
        if (now - _CACHED_SCHEMA_TIME).total_seconds() < SCHEMA_CACHE_SECONDS:
            return _CACHED_SCHEMA

    schema_lines = []
    schema_lines.append("=" * 70)
    schema_lines.append("EduNexus University Management System — Live Database Schema")
    schema_lines.append("Database: SQLite | Framework: Django 4.2")
    schema_lines.append("=" * 70)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'django_%' "
            "AND name NOT LIKE 'auth_%' ORDER BY name;"
        )
        tables = [row[0] for row in cursor.fetchall()]

        for table_name in tables:
            schema_lines.append(f"\nTABLE: {table_name}")

            cursor.execute(f"PRAGMA table_info('{table_name}');")
            columns = cursor.fetchall()
            for col in columns:
                cid, col_name, col_type, notnull, default, pk = col
                parts = [f"  - {col_name} ({col_type or 'TEXT'}"]
                if pk:
                    parts.append(", PRIMARY KEY")
                if notnull:
                    parts.append(", NOT NULL")
                if default is not None:
                    parts.append(f", DEFAULT={default}")
                parts.append(")")
                schema_lines.append("".join(parts))

            cursor.execute(f"PRAGMA foreign_key_list('{table_name}');")
            fks = cursor.fetchall()
            for fk in fks:
                schema_lines.append(f"  -> FK: {fk[3]} -> {fk[2]}.{fk[4]}")

            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
                count = cursor.fetchone()[0]
                schema_lines.append(f"  Rows: {count}")
            except Exception:
                pass

    _CACHED_SCHEMA = "\n".join(schema_lines)
    _CACHED_SCHEMA_TIME = now
    return _CACHED_SCHEMA


def get_sample_data():
    """
    Get a small sample of data from key tables so the LLM
    understands actual data patterns (names, codes, formats).
    """
    samples = {}
    sample_queries = {
        "departments": "SELECT id, name, code FROM admin_app_department LIMIT 5;",
        "degree_programs": "SELECT id, name, code, department_id FROM admin_app_degreeprogram LIMIT 5;",
        "subjects": "SELECT id, code, name, credits, semester FROM admin_app_subject LIMIT 5;",
        "students": "SELECT id, roll_number, name, semester, division, batch, status FROM admin_app_student LIMIT 5;",
        "faculty": "SELECT id, name, email, specialization, status FROM admin_app_faculty LIMIT 5;",
    }

    with connection.cursor() as cursor:
        for key, query in sample_queries.items():
            try:
                cursor.execute(query)
                cols = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                samples[key] = {
                    "columns": cols,
                    "rows": [dict(zip(cols, row)) for row in rows],
                }
            except Exception:
                samples[key] = {"columns": [], "rows": []}

    return samples


# ======================================================================
# DJANGO ORM MODEL SCHEMA (for the LLM)
# ======================================================================

DJANGO_ORM_SCHEMA = """
DJANGO ORM MODEL MAPPING (use these model names in Python code):

Model: Department
  Fields: id, name (unique), code (unique), head_id (FK->Faculty, nullable), created_at
  Related: degree_programs (DegreeProgram), subjects (Subject), faculties (Faculty)

Model: DegreeProgram
  Fields: id, name (unique), code (unique), department_id (FK->Department), duration_semesters, created_at
  Related: enrolled_students (Student)

Model: Subject
  Fields: id, code (unique), name (unique), credits, semester (1-8), is_elective, department_id (FK->Department), created_at
  Related: offerings (SubjectOffering), exam_schedules (ExamSchedule), results (SubjectResult), qualified_faculties (M2M Faculty)

Model: SubjectOffering
  Fields: id, subject_id (FK->Subject), academic_year, division, faculty_id (FK->Faculty), max_students, created_at
  Related: enrollments (StudentEnrollment), lectures (Lecture), internal_assessments, timetable_slots (Timetable)

Model: Student
  Fields: id, user_id (OneToOne->CustomUser), roll_number (unique), name, degree_program_id (FK->DegreeProgram, nullable),
          semester (1-8), division, batch (A1-A4, B1-B4), graduation_date, phone,
          blood_group, date_of_birth, address, city, state, pincode,
          father_name, father_contact, mother_name, mother_contact,
          image, face_encoding, status (active/graduated/suspended/dropped), created_at, updated_at
  Related: enrollments, attendances, exam_marks, internal_assessments, semester_results,
           fee_structures, fee_receipts, leave_requests, admit_cards

Model: Faculty
  Fields: id, user_id (OneToOne->CustomUser), name, email, phone, department_id (FK->Department, nullable),
          specialization, salary, image, status (active/inactive), created_at, updated_at
  M2M: subjects (Subject, related_name='qualified_faculties')
  Related: teaching_subjects (SubjectOffering), conducted_lectures, marked_attendances,
           invigilated_exams, entered_internal_marks, marked_exams, created_notifications,
           approved_leaves, headed_departments

Model: StudentEnrollment
  Fields: id, student_id (FK->Student), subject_offering_id (FK->SubjectOffering), status, enrollment_date

Model: ExamType
  Fields: id, name (unique), description, is_mandatory

Model: ExamSchedule
  Fields: id, subject_id (FK->Subject), exam_type_id (FK->ExamType), academic_year,
          exam_date, start_time, end_time, duration_minutes, max_marks, passing_marks,
          room_number, invigilator_id (FK->Faculty, nullable), status

Model: AdmitCard
  Fields: id, exam_schedule_id (FK->ExamSchedule), student_id (FK->Student),
          admit_number (unique), seat_number, issue_date, is_valid, notes

Model: ExamMarks
  Fields: id, admit_card_id (OneToOne->AdmitCard, nullable), exam_schedule_id (FK->ExamSchedule),
          student_id (FK->Student), marks_obtained, is_marked, marked_by_id (FK->Faculty), marked_date

Model: InternalAssessment
  Fields: id, subject_offering_id (FK->SubjectOffering), student_id (FK->Student),
          academic_year, session_number (1-3), theory_marks, practical_marks, entered_by_id (FK->Faculty)

Model: Lecture
  Fields: id, subject_offering_id (FK->SubjectOffering), date, start_time, end_time,
          lecture_type (theory/practical/tutorial), room_number, faculty_id (FK->Faculty), is_conducted

Model: Attendance
  Fields: id, lecture_id (FK->Lecture), student_id (FK->Student),
          status (present/absent/late), marked_date, marked_by_id (FK->Faculty), face_recognized

Model: Timetable
  Fields: id, subject_offering_id (FK->SubjectOffering), day (monday-saturday),
          start_time, end_time, room_number, lecture_type

Model: SemesterResult
  Fields: id, student_id (FK->Student), semester, academic_year, sgpa,
          status (pass/fail/incomplete), result_date, published

Model: SubjectResult
  Fields: id, semester_result_id (FK->SemesterResult), subject_id (FK->Subject),
          internal_marks, external_marks, practical_marks, total_marks, grade (A+/A/B+/B/C/F), gpa, status

Model: FeeStructure
  Fields: id, student_id (FK->Student), semester, academic_year,
          fees_to_be_collected, previously_paid, paid, refunded, outstanding

Model: FeeReceipt
  Fields: id, student_id (FK->Student), fee_structure_id (FK->FeeStructure),
          receipt_number (unique), amount, payment_date, payment_mode (online/cash/check/dd),
          transaction_id, bank_name

Model: LeaveRequest
  Fields: id, student_id (FK->Student), start_date, end_date, reason,
          status (pending/approved/rejected/expired), approved_by_id (FK->Faculty),
          approval_date, remarks, requested_date

Model: Notification
  Fields: id, title, message, recipient_role (faculty/student/all),
          priority (low/medium/high), created_by_id (FK->Faculty), is_read

Model: AcademicCalendar
  Fields: id, academic_year (unique), semester, start_date, end_date,
          exam_start_date, exam_end_date, result_declaration_date
"""


# ======================================================================
# GEMINI LLM CONFIGURATION
# ======================================================================

def _get_api_key():
    """Safely retrieve Gemini API key from settings."""
    return getattr(settings, "GEMINI_API_KEY", None)


def get_system_prompt(user_role="admin", student_info=None):
    """
    Build the full system prompt with dynamic schema + ORM mapping +
    sample data + role-based access rules.
    """
    live_schema = introspect_database_schema()
    samples = get_sample_data()

    sample_text = "\nSAMPLE DATA (for understanding data patterns):\n"
    for key, data in samples.items():
        if data["rows"]:
            sample_text += f"\n{key}:\n"
            for row in data["rows"][:3]:
                sample_text += f"  {row}\n"

    role_rules = ""
    if user_role == "student" and student_info:
        role_rules = (
            f"\n\nROLE-BASED ACCESS RESTRICTION:\n"
            f"Current user is a STUDENT:\n"
            f"  - Student ID: {student_info.get('id')}\n"
            f"  - Roll Number: {student_info.get('roll_number')}\n"
            f"  - Name: {student_info.get('name')}\n"
            f"\nALWAYS filter to show ONLY their own records.\n"
            f"Add .filter(student_id={student_info.get('id')}) to student-specific queries.\n"
            f"Students CAN see: own attendance, marks, results, fees, leave, timetable, plus general info.\n"
            f"Students CANNOT see: other students' data, faculty salaries, all fee records.\n"
        )
    elif user_role == "faculty":
        role_rules = (
            "\n\nROLE NOTE: Current user is FACULTY. They can see teaching data "
            "and student data for subjects they teach. No salary data of others.\n"
        )

    prompt = (
        "You are an expert AI database assistant for the EduNexus University Management System.\n"
        "You have access to a Django/SQLite database.\n\n"
        "YOUR CAPABILITIES:\n"
        "1. UNDERSTAND user questions about the university database\n"
        "2. GENERATE Django ORM Python code to answer the question\n"
        "3. EXPLAIN results in clear, human-friendly language\n"
        "4. Handle FOLLOW-UP questions using conversation context\n"
        "5. Suggest related queries the user might want to ask\n\n"
        "LIVE DATABASE SCHEMA (auto-introspected):\n"
        + live_schema + "\n\n"
        "DJANGO ORM MODEL DETAILS:\n"
        + DJANGO_ORM_SCHEMA + "\n"
        + sample_text
        + role_rules +
        "\n\nCODE GENERATION RULES:\n"
        "- Respond ONLY in the EXACT JSON format specified below\n"
        "- The 'query_code' must be valid Python using Django ORM\n"
        "- All models are already imported and available\n"
        "- Django Q, F, Value, Count, Avg, Sum, Max, Min, Concat, Lower, Upper, Coalesce are available\n"
        "- Python date, datetime, timedelta, Decimal are available\n"
        "- Code MUST assign the final result to a variable called 'result'\n"
        "- 'result' should be a list of dicts, a single dict, a number, or a string\n"
        "- For querysets use .values() or list comprehension to convert\n"
        "- Use select_related/prefetch_related for efficiency\n"
        "- LIMIT results to 50 rows max using [:50]\n"
        "- NEVER modify data: no .save(), .create(), .delete(), .update()\n"
        "- NEVER use raw SQL, always use Django ORM\n"
        "- NEVER use import statements\n"
        "- For greetings/help, set query_code to null\n"
        "- For date comparisons use date.today() or datetime.now()\n\n"
        'RESPONSE FORMAT (strict JSON only, no markdown fencing):\n'
        '{\n'
        '  "query_code": "result = Student.objects.filter(semester=6).values(\'roll_number\', \'name\')[:50]",\n'
        '  "explanation": "Here are the students in semester 6.",\n'
        '  "display_type": "table",\n'
        '  "title": "Students in Semester 6",\n'
        '  "columns": ["Roll No", "Name"],\n'
        '  "field_keys": ["roll_number", "name"],\n'
        '  "suggestions": ["Show attendance", "Count by division"]\n'
        '}\n\n'
        'display_type options:\n'
        '- "table": for lists -> provide columns, field_keys\n'
        '- "text": for explanations -> put answer in explanation\n'
        '- "stat": for aggregates -> result = dict of metric:value\n'
        '- "chart": for charts -> add chart_type (bar/pie/line) and chart_data {label_key, value_key}\n\n'
        'For greetings:\n'
        '{"query_code": null, "explanation": "Hello! ...", "display_type": "text", '
        '"title": null, "columns": null, "field_keys": null, "suggestions": ["Show students", "Stats"]}\n\n'
        'For stats:\n'
        '{"query_code": "result = {\'Total\': Student.objects.count()}", '
        '"explanation": "Count.", "display_type": "stat", "title": "Stats", '
        '"columns": null, "field_keys": null, "suggestions": ["By dept"]}\n\n'
        'For charts:\n'
        '{"query_code": "result = list(Student.objects.values(\'semester\').annotate(count=Count(\'id\')).order_by(\'semester\'))", '
        '"explanation": "Distribution.", "display_type": "chart", "title": "Per Semester", '
        '"chart_type": "bar", "chart_data": {"label_key": "semester", "value_key": "count"}, '
        '"columns": ["Semester", "Count"], "field_keys": ["semester", "count"], "suggestions": ["By dept"]}\n'
    )
    return prompt


_gemini_model = None
_gemini_api_key_used = None
_gemini_model_name = None

# Models to try in order of preference
PREFERRED_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemma-3-27b-it",
    "gemma-3-12b-it",
]


def get_gemini_model():
    """Initialize and cache the Gemini model with automatic fallback.

    Tries models in PREFERRED_MODELS order. If the current cached model
    hits a quota error, call reset_model() then get_gemini_model() again
    to try the next one.
    """
    global _gemini_model, _gemini_api_key_used, _gemini_model_name
    api_key = _get_api_key()
    if not api_key:
        return None
    # Re-create model if key has changed
    if _gemini_model is not None and _gemini_api_key_used == api_key:
        return _gemini_model
    genai.configure(api_key=api_key)
    # Pick the first model that hasn't been exhausted
    model_name = PREFERRED_MODELS[0]
    _gemini_model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=4096,
        ),
    )
    _gemini_api_key_used = api_key
    _gemini_model_name = model_name
    return _gemini_model


def _try_next_model():
    """Switch to the next model in the fallback list. Returns True if switched."""
    global _gemini_model, _gemini_model_name
    if not _gemini_model_name:
        return False
    try:
        idx = PREFERRED_MODELS.index(_gemini_model_name)
    except ValueError:
        idx = -1
    next_idx = idx + 1
    if next_idx >= len(PREFERRED_MODELS):
        return False
    model_name = PREFERRED_MODELS[next_idx]
    _gemini_model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=4096,
        ),
    )
    _gemini_model_name = model_name
    return True


# ======================================================================
# SAFE QUERY EXECUTOR — sandboxed Django ORM execution
# ======================================================================

SAFE_GLOBALS = {
    "__builtins__": {
        "list": list, "dict": dict, "str": str, "int": int, "float": float,
        "bool": bool, "len": len, "sorted": sorted, "round": round,
        "range": range, "enumerate": enumerate, "zip": zip, "map": map,
        "min": min, "max": max, "sum": sum, "abs": abs, "set": set,
        "tuple": tuple, "True": True, "False": False, "None": None,
        "isinstance": isinstance, "hasattr": hasattr, "getattr": getattr,
        "format": format, "print": lambda *a, **k: None,
        "any": any, "all": all, "filter": filter,
    },
    # Models
    "Department": Department, "DegreeProgram": DegreeProgram,
    "Subject": Subject, "SubjectOffering": SubjectOffering,
    "Student": Student, "Faculty": Faculty,
    "StudentEnrollment": StudentEnrollment,
    "ExamType": ExamType, "ExamSchedule": ExamSchedule,
    "AdmitCard": AdmitCard, "ExamMarks": ExamMarks,
    "InternalAssessment": InternalAssessment,
    "Lecture": Lecture, "Attendance": Attendance,
    "Timetable": Timetable,
    "SemesterResult": SemesterResult, "SubjectResult": SubjectResult,
    "FeeStructure": FeeStructure, "FeeReceipt": FeeReceipt,
    "LeaveRequest": LeaveRequest, "Notification": Notification,
    "AcademicCalendar": AcademicCalendar,
    # Django ORM tools
    "Q": Q, "F": F, "Value": Value, "CharField": CharField,
    "Count": Count, "Avg": Avg, "Sum": Sum, "Max": Max, "Min": Min,
    "Concat": Concat, "Lower": Lower, "Upper": Upper, "Coalesce": Coalesce,
    # Python standard lib
    "Decimal": Decimal,
    "date": date, "datetime": datetime, "timedelta": timedelta,
}

BLOCKED_PATTERNS = [
    r'\.delete\s*\(', r'\.save\s*\(', r'\.create\s*\(',
    r'\.update\s*\(', r'\.bulk_create\s*\(', r'\.bulk_update\s*\(',
    r'\.raw\s*\(', r'import\s+', r'__import__',
    r'exec\s*\(', r'eval\s*\(', r'compile\s*\(',
    r'open\s*\(', r'os\.', r'sys\.', r'subprocess',
    r'shutil', r'pathlib', r'globals\s*\(', r'locals\s*\(',
    r'__class__', r'__subclasses__', r'__bases__',
]


def validate_query_code(code):
    """Validate that generated code is safe to execute."""
    if not code or not code.strip():
        return False, "Empty code"
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, code):
            return False, f"Blocked unsafe operation: {pattern}"
    if "result" not in code:
        return False, "Code must assign to 'result' variable"
    return True, "OK"


def execute_query(code):
    """Safely execute Django ORM code in a sandboxed environment."""
    is_valid, msg = validate_query_code(code)
    if not is_valid:
        return None, f"Security check failed: {msg}"

    local_vars = {}
    try:
        exec(code, SAFE_GLOBALS.copy(), local_vars)
    except Exception as exc:
        return None, f"Query execution error: {type(exc).__name__}: {exc}"

    result = local_vars.get("result")
    if result is None:
        return None, "Query produced no result"

    return result, None


# ======================================================================
# RESULT SERIALIZER
# ======================================================================

def serialize_value(val):
    """Convert a value to a JSON-serializable format."""
    if val is None:
        return "\u2014"
    if isinstance(val, datetime):
        return val.strftime("%d %b %Y %H:%M")
    if isinstance(val, date):
        return val.strftime("%d %b %Y")
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, bool):
        return "Yes" if val else "No"
    if isinstance(val, (list, tuple)):
        return ", ".join(str(v) for v in val)
    return str(val)


def serialize_result(result, field_keys=None):
    """Serialize query result into JSON-safe format."""
    from django.db.models import QuerySet
    if isinstance(result, QuerySet):
        if field_keys:
            result = list(result.values(*field_keys)[:50])
        else:
            result = list(result.values()[:50])

    if isinstance(result, dict):
        return {str(k): serialize_value(v) for k, v in result.items()}

    if isinstance(result, (list, tuple)):
        serialized = []
        for item in result[:50]:
            if isinstance(item, dict):
                serialized.append({str(k): serialize_value(v) for k, v in item.items()})
            elif isinstance(item, (list, tuple)):
                serialized.append([serialize_value(v) for v in item])
            else:
                serialized.append(serialize_value(item))
        return serialized

    return serialize_value(result)


# ======================================================================
# CONVERSATION HISTORY MANAGER
# ======================================================================

class ConversationManager:
    """Manages per-session conversation history for follow-up questions."""
    MAX_HISTORY = 10

    @staticmethod
    def get_history(request):
        return request.session.get("chat_history", [])

    @staticmethod
    def add_exchange(request, user_msg, bot_response, query_code=None):
        history = request.session.get("chat_history", [])
        history.append({"role": "user", "content": user_msg})
        summary = bot_response.get("message", "")[:300]
        if query_code:
            summary += f"\n[Executed: {query_code[:200]}]"
        history.append({"role": "assistant", "content": summary})
        if len(history) > ConversationManager.MAX_HISTORY * 2:
            history = history[-(ConversationManager.MAX_HISTORY * 2):]
        request.session["chat_history"] = history

    @staticmethod
    def clear_history(request):
        request.session["chat_history"] = []

    @staticmethod
    def format_history(history):
        if not history:
            return ""
        lines = ["\n\nCONVERSATION HISTORY (for follow-up context):"]
        for entry in history[-6:]:
            role = "User" if entry["role"] == "user" else "Assistant"
            lines.append(f"{role}: {entry['content'][:200]}")
        return "\n".join(lines)


# ======================================================================
# MAIN AI PIPELINE
# ======================================================================

def get_user_context(request):
    """Extract user role and student info for role-based filtering."""
    user = request.user
    user_role = getattr(user, "role", "admin")
    student_info = None

    if user_role == "student":
        try:
            student = user.student_profile
            student_info = {
                "id": student.id,
                "roll_number": student.roll_number,
                "name": student.name,
                "semester": student.semester,
                "division": student.division,
                "degree_program": str(student.degree_program) if student.degree_program else None,
            }
        except Exception:
            pass

    return user_role, student_info


def process_message(message, request=None):
    """
    Full AI pipeline:
    User question -> Schema + History -> Gemini LLM -> ORM Code -> Execute -> Explain
    """
    model = get_gemini_model()
    if not model:
        return {
            "type": "text",
            "message": (
                "**Gemini API key not configured.**\n\n"
                "1. Get a free key from Google AI Studio (https://aistudio.google.com/apikey)\n"
                "2. Add to project1/settings.py: GEMINI_API_KEY = 'your-key'\n"
                "3. Or set env var: export GEMINI_API_KEY=your-key\n"
                "4. Restart the server"
            ),
        }

    user_role = "admin"
    student_info = None
    if request:
        user_role, student_info = get_user_context(request)

    system_prompt = get_system_prompt(user_role, student_info)

    history = []
    if request:
        history = ConversationManager.get_history(request)
    history_text = ConversationManager.format_history(history)

    full_prompt = system_prompt + history_text + "\n\nUSER QUESTION: " + message

    # Call Gemini (with model fallback on quota errors)
    max_retries = len(PREFERRED_MODELS)
    for attempt in range(max_retries):
        try:
            chat = model.start_chat(history=[])
            response = chat.send_message(full_prompt)
            raw_text = response.text.strip()
            break
        except Exception as exc:
            exc_str = str(exc)
            # Detect rate-limit / quota errors (HTTP 429)
            if "429" in exc_str or "quota" in exc_str.lower() or "ResourceExhausted" in exc_str:
                # Try the next model in the fallback list
                if _try_next_model():
                    model = _gemini_model
                    continue
                return {
                    "type": "text",
                    "message": (
                        "**⏳ API Rate Limit Reached**\n\n"
                        "All available AI models have exceeded their free-tier quota. "
                        "This resets automatically — please try again later.\n\n"
                        "**What you can do:**\n"
                        "- Wait a few hours for the daily quota to reset\n"
                        "- Create a key from a new Google Cloud project\n"
                        "- Upgrade to a paid Gemini API plan for higher limits"
                    ),
                    "suggestions": ["Try again", "Show schema", "Show statistics"],
                }
            return {
                "type": "text",
                "message": f"Error communicating with AI: {exc}",
            }

    # Parse LLM JSON response
    try:
        cleaned = raw_text
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        llm_response = json.loads(cleaned)
    except json.JSONDecodeError:
        # Retry: ask LLM to fix
        try:
            retry_prompt = (
                "Your previous response was not valid JSON. "
                "Respond ONLY with the JSON object, no markdown fencing. "
                "Previous response:\n" + raw_text[:500]
            )
            response = chat.send_message(retry_prompt)
            cleaned = response.text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)
            llm_response = json.loads(cleaned)
        except Exception:
            return {
                "type": "text",
                "message": "AI returned an invalid response. Please rephrase your question.\n\nRaw:\n" + raw_text[:500],
            }

    query_code = llm_response.get("query_code")
    explanation = llm_response.get("explanation", "")
    display_type = llm_response.get("display_type", "text")
    title = llm_response.get("title")
    columns = llm_response.get("columns")
    field_keys = llm_response.get("field_keys")
    suggestions = llm_response.get("suggestions", [])
    chart_type = llm_response.get("chart_type")
    chart_data = llm_response.get("chart_data")

    # No query -> greeting/help
    if not query_code:
        result = {
            "type": "text",
            "message": explanation,
            "suggestions": suggestions,
            "_ai": {"query": None, "model": "gemini-2.0-flash"},
        }
        if request:
            ConversationManager.add_exchange(request, message, result)
        return result

    # Execute the ORM query
    raw_result, error = execute_query(query_code)

    if error:
        # Auto-retry with LLM
        retry_result = _retry_failed_query(model, message, query_code, error, system_prompt)
        if retry_result is not None:
            result_data = _build_response(
                retry_result["result"], retry_result["code"],
                explanation, display_type, title, columns,
                field_keys, suggestions, chart_type, chart_data
            )
            if request:
                ConversationManager.add_exchange(request, message, result_data, retry_result["code"])
            return result_data

        result = {
            "type": "text",
            "message": (
                f"I couldn't execute that query. Error: {error}\n\n"
                f"**Generated code:**\n`{query_code}`\n\n"
                f"**AI explanation:** {explanation}\n\n"
                "Please try rephrasing your question."
            ),
            "suggestions": ["Show all students", "Count by department", "List subjects"],
            "_ai": {"query": query_code, "error": error, "model": "gemini-2.0-flash"},
        }
        if request:
            ConversationManager.add_exchange(request, message, result, query_code)
        return result

    # Build successful response
    result_data = _build_response(
        raw_result, query_code, explanation, display_type,
        title, columns, field_keys, suggestions, chart_type, chart_data
    )
    if request:
        ConversationManager.add_exchange(request, message, result_data, query_code)
    return result_data


def _retry_failed_query(model, original_question, failed_code, error, system_prompt):
    """Ask the LLM to fix a failed query. Returns dict or None."""
    try:
        retry_prompt = (
            f"{system_prompt}\n\n"
            f"User asked: {original_question}\n"
            f"Generated code: {failed_code}\n"
            f"Error: {error}\n\n"
            "Fix the code. Handle edge cases (empty querysets, None values)."
        )
        chat = model.start_chat(history=[])
        response = chat.send_message(retry_prompt)
        cleaned = response.text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        retry_response = json.loads(cleaned)
        new_code = retry_response.get("query_code")
        if new_code:
            result, err = execute_query(new_code)
            if err is None:
                return {"result": result, "code": new_code}
    except Exception:
        pass
    return None


def _build_response(raw_result, query_code, explanation, display_type,
                    title, columns, field_keys, suggestions,
                    chart_type=None, chart_data=None):
    """Build the final response dict from query results."""
    serialized = serialize_result(raw_result, field_keys)

    # TABLE
    if display_type == "table" and isinstance(serialized, list) and columns:
        rows = []
        for item in serialized:
            if isinstance(item, dict):
                keys = field_keys or list(item.keys())
                row = [serialize_value(item.get(k, "\u2014")) for k in keys]
            elif isinstance(item, (list, tuple)):
                row = [serialize_value(v) for v in item]
            else:
                row = [serialize_value(item)]
            rows.append(row)

        count_msg = f"\n\nShowing **{len(rows)}** result(s)." if rows else "\n\nNo results found."
        return {
            "type": "table",
            "title": title or "Query Results",
            "columns": columns,
            "rows": rows,
            "message": explanation + count_msg,
            "suggestions": suggestions,
            "_ai": {"query": query_code, "model": "gemini-2.0-flash"},
        }

    # STAT
    elif display_type == "stat" and isinstance(serialized, dict):
        rows = [[k.replace("_", " ").title(), serialize_value(v)] for k, v in serialized.items()]
        return {
            "type": "table",
            "title": title or "Statistics",
            "columns": ["Metric", "Value"],
            "rows": rows,
            "message": explanation,
            "suggestions": suggestions,
            "_ai": {"query": query_code, "model": "gemini-2.0-flash"},
        }

    # CHART
    elif display_type == "chart" and isinstance(serialized, list):
        rows = []
        if columns and field_keys:
            for item in serialized:
                if isinstance(item, dict):
                    row = [serialize_value(item.get(k, "\u2014")) for k in field_keys]
                    rows.append(row)

        chart_labels = []
        chart_values = []
        if chart_data and isinstance(chart_data, dict):
            for item in serialized:
                if isinstance(item, dict):
                    chart_labels.append(serialize_value(item.get(chart_data.get("label_key", ""), "")))
                    chart_values.append(item.get(chart_data.get("value_key", ""), 0))

        return {
            "type": "chart",
            "title": title or "Chart",
            "chart_type": chart_type or "bar",
            "chart_data": {"labels": chart_labels, "values": chart_values},
            "columns": columns,
            "rows": rows,
            "message": explanation,
            "suggestions": suggestions,
            "_ai": {"query": query_code, "model": "gemini-2.0-flash"},
        }

    # TEXT
    else:
        if isinstance(serialized, (list, dict)):
            formatted = json.dumps(serialized, indent=2, default=str)
            msg = explanation + "\n\n**Results:**\n" + formatted
        else:
            msg = explanation + "\n\n**Answer:** " + str(serialized)
        return {
            "type": "text",
            "message": msg,
            "suggestions": suggestions,
            "_ai": {"query": query_code, "model": "gemini-2.0-flash"},
        }


# ======================================================================
# VIEWS
# ======================================================================

@authenticated_required
def database_chat(request):
    """Render the chat interface — accessible to all authenticated users."""
    user_role = getattr(request.user, "role", "admin")
    return render(request, "admin_app/database_chat.html", {
        "user_role": user_role,
    })


@authenticated_required
def chat_api(request):
    """API endpoint for chat messages."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        body = json.loads(request.body)
        message = body.get("message", "").strip()
    except (json.JSONDecodeError, AttributeError):
        message = request.POST.get("message", "").strip()

    if not message:
        return JsonResponse({"error": "Empty message"}, status=400)

    # Special commands
    if message.lower() in ("/clear", "/reset", "clear history", "reset chat"):
        ConversationManager.clear_history(request)
        return JsonResponse({
            "type": "text",
            "message": "Chat history cleared! Ask me anything about the database.",
            "suggestions": ["Show all students", "Database statistics", "List departments"],
        })

    if message.lower() in ("/schema", "show schema", "show database schema"):
        schema = introspect_database_schema()
        return JsonResponse({
            "type": "text",
            "message": f"**Live Database Schema:**\n\n```\n{schema[:3000]}\n```",
            "suggestions": ["Show statistics", "List tables", "Count records"],
        })

    try:
        response = process_message(message, request)
    except Exception as exc:
        exc_str = str(exc)
        if "429" in exc_str or "quota" in exc_str.lower() or "rate" in exc_str.lower():
            response = {
                "type": "text",
                "message": (
                    "**\u23f3 API Rate Limit Reached**\n\n"
                    "The Gemini AI quota has been exceeded. "
                    "Please wait a moment and try again.\n\n"
                    "**Tips:**\n"
                    "- Wait ~30 seconds before retrying\n"
                    "- Upgrade your Gemini API plan for higher limits"
                ),
                "suggestions": ["Try again", "Show schema"],
            }
        else:
            response = {
                "type": "text",
                "message": f"An unexpected error occurred: {exc}",
                "suggestions": ["Try a simpler question", "Show all students"],
                "_ai": {"error": str(exc)},
            }

    return JsonResponse(response)


@authenticated_required
def chat_clear(request):
    """Clear chat history endpoint."""
    if request.method == "POST":
        ConversationManager.clear_history(request)
        return JsonResponse({"status": "ok", "message": "History cleared"})
    return JsonResponse({"error": "POST required"}, status=405)
