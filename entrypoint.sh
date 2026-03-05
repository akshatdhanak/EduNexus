#!/bin/bash
# ───────────────────────────────────────────────────────────
# EduNexus — Docker Entrypoint
# Runs migrations + superuser creation before starting gunicorn
# ───────────────────────────────────────────────────────────
set -e

echo "🗃️  Running database migrations..."
python manage.py migrate --noinput

echo "🏫 Seeding departments & programs..."
python manage.py seed_departments

echo "👤 Creating superuser if missing..."
python manage.py create_superuser_if_missing

echo "🚀 Starting gunicorn on port ${PORT:-10000}..."
exec gunicorn project1.wsgi:application \
    --bind 0.0.0.0:${PORT:-10000} \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
