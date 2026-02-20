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

# NOTE: Migrations are NOT run here because DATABASE_URL from
# Render's managed PostgreSQL may not be available during the build phase.
# Migrations run via preDeployCommand and startCommand in render.yaml instead.

echo "✅ Build complete!"
