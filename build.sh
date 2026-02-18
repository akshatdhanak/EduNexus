#!/usr/bin/env bash
# ───────────────────────────────────────────────────────────
# EduNexus — Render Build Script
# This script is executed by Render during each deploy
# ───────────────────────────────────────────────────────────
set -o errexit

echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "📂 Collecting static files..."
python manage.py collectstatic --noinput

echo "🗃️  Running migrations..."
python manage.py migrate --noinput

echo "✅ Build complete!"
