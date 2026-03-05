import django.db.models.deletion
from django.db import migrations, models


def populate_subject_from_offering(apps, schema_editor):
    """Copy subject_id from the related SubjectOffering into the new subject field."""
    Assignment = apps.get_model("admin_app", "Assignment")
    SubjectOffering = apps.get_model("admin_app", "SubjectOffering")
    for assignment in Assignment.objects.all():
        offering = SubjectOffering.objects.get(id=assignment.subject_offering_id)
        assignment.subject_id = offering.subject_id
        assignment.save(update_fields=["subject_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0009_assignment_assignmentsubmission"),
    ]

    operations = [
        # 1. Add nullable subject FK
        migrations.AddField(
            model_name="assignment",
            name="subject",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assignments_new",
                to="admin_app.subject",
            ),
        ),
        # 2. Populate subject from subject_offering
        migrations.RunPython(
            populate_subject_from_offering,
            migrations.RunPython.noop,
        ),
        # 3. Remove old subject_offering FK
        migrations.RemoveField(
            model_name="assignment",
            name="subject_offering",
        ),
        # 4. Make subject non-nullable and set final related_name
        migrations.AlterField(
            model_name="assignment",
            name="subject",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assignments",
                to="admin_app.subject",
            ),
        ),
    ]
