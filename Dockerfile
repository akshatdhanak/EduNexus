# ───────────────────────────────────────────────────────────
# EduNexus — Production Dockerfile
# Multi-stage build: slim image with only runtime deps
# ───────────────────────────────────────────────────────────

# ---------- Stage 1: Builder ----------
FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libzbar-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Stage 2: Runtime ----------
FROM python:3.13-slim

# System deps needed at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libzbar0 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r edunexus && useradd -r -g edunexus -d /app -s /sbin/nologin edunexus

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy project source
COPY . .

# Create required directories
RUN mkdir -p /app/staticfiles /app/media/student_photos /app/media/faculty_photos /app/media/photos \
    && chown -R edunexus:edunexus /app

# Collect static files (uses STATIC_ROOT)
RUN DJANGO_SETTINGS_MODULE=project1.settings \
    SECRET_KEY=build-placeholder \
    DATABASE_URL=sqlite:///tmp/build.db \
    DEBUG=0 \
    python manage.py collectstatic --noinput 2>/dev/null || true

USER edunexus

EXPOSE 10000

# Health check (uses PORT env var, Render defaults to 10000)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",10000)}/accounts/login/')" || exit 1

# Start with gunicorn — use $PORT from Render (default 10000)
CMD gunicorn project1.wsgi:application \
    --bind 0.0.0.0:${PORT:-10000} \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
