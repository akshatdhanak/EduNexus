from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0007_add_faculty_department"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="graduation_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="student",
            name="batch",
            field=models.CharField(
                max_length=10,
                choices=[
                    ("A1", "A1"),
                    ("A2", "A2"),
                    ("A3", "A3"),
                    ("A4", "A4"),
                    ("B1", "B1"),
                    ("B2", "B2"),
                    ("B3", "B3"),
                    ("B4", "B4"),
                ],
            ),
        ),
    ]
