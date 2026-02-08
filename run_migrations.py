#!/usr/bin/env python
import os
import sys
import django
from io import StringIO
from django.core.management import call_command

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project1.settings')
django.setup()

# Capture makemigrations
print("🔄 Creating migrations...")
try:
    call_command('makemigrations', 'admin_app', interactive=False, verbosity=2)
    print("✅ Migrations created successfully!")
except Exception as e:
    print(f"⚠️ Migration creation: {e}")

# Run migrations
print("\n🔄 Applying migrations...")
try:
    call_command('migrate', 'admin_app', verbosity=2)
    print("✅ Migrations applied successfully!")
except Exception as e:
    print(f"❌ Migration error: {e}")
    sys.exit(1)

# Final check
print("\n🔄 Running system check...")
try:
    call_command('check', verbosity=0)
    print("✅ System check passed!")
except Exception as e:
    print(f"❌ System check failed: {e}")
    sys.exit(1)

print("\n✨ All done! Database is ready.")
