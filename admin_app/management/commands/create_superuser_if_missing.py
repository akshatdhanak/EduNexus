"""
Auto-create a superuser from environment variables if none exists.
Usage:  python manage.py create_superuser_if_missing
"""
import os
import traceback
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Creates a superuser from DJANGO_SUPERUSER_* env vars if no superuser exists"

    def handle(self, *args, **options):
        try:
            existing = User.objects.filter(is_superuser=True).count()
            self.stdout.write(f"[superuser-check] Found {existing} existing superuser(s)")

            if existing > 0:
                self.stdout.write(self.style.WARNING("Superuser already exists — skipping."))
                return

            username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
            email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@edunexus.com")
            password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin123")

            self.stdout.write(f"[superuser-check] Creating superuser: username={username}, email={email}")

            user = User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(
                f"Superuser '{username}' created! (id={user.id}, is_superuser={user.is_superuser})"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to create superuser: {e}"))
            traceback.print_exc()
