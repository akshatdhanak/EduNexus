"""
Seed default Department and DegreeProgram records if they don't exist.
Usage:  python manage.py seed_departments
"""
from django.core.management.base import BaseCommand
from admin_app.models import Department, DegreeProgram


# (dept_name, dept_code, [(program_name, program_code, semesters), ...])
SEED_DATA = [
    ("Computer Engineering", "CE", [
        ("B.Tech - Computer Engineering", "CE", 8),
        ("M.Tech - Computer Engineering", "CE-M", 4),
    ]),
    ("Information Technology", "IT", [
        ("B.Tech - Information Technology", "IT", 8),
        ("M.Tech - Information Technology", "IT-M", 4),
    ]),
    ("Computer Science", "CS", [
        ("B.Tech - Computer Science", "CS", 8),
    ]),
    ("Electronics & Communication", "EC", [
        ("B.Tech - Electronics & Communication", "EC", 8),
    ]),
    ("Mechanical Engineering", "ME", [
        ("B.Tech - Mechanical Engineering", "ME", 8),
    ]),
    ("Civil Engineering", "CV", [
        ("B.Tech - Civil Engineering", "CV", 8),
    ]),
    ("Electrical Engineering", "EE", [
        ("B.Tech - Electrical Engineering", "EE", 8),
    ]),
]


class Command(BaseCommand):
    help = "Seed Department and DegreeProgram tables with defaults (idempotent)"

    def handle(self, *args, **options):
        created_depts = 0
        created_progs = 0

        for dept_name, dept_code, programs in SEED_DATA:
            # Try to find by name first, then by code
            dept = Department.objects.filter(name=dept_name).first()
            if not dept:
                dept = Department.objects.filter(code=dept_code).first()
            if not dept:
                dept = Department.objects.create(name=dept_name, code=dept_code)
                created_depts += 1
            else:
                # Update code if it was empty
                if not dept.code and dept_code:
                    dept.code = dept_code
                    dept.save(update_fields=["code"])

            for prog_name, prog_code, semesters in programs:
                prog = DegreeProgram.objects.filter(code=prog_code).first()
                if not prog:
                    prog = DegreeProgram.objects.filter(name=prog_name).first()
                if not prog:
                    DegreeProgram.objects.create(
                        name=prog_name,
                        code=prog_code,
                        department=dept,
                        duration_semesters=semesters,
                    )
                    created_progs += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete: {created_depts} departments, {created_progs} programs created."
            )
        )
