# Dockerfile — Production Container Build
# =========================================
#
# MULTI-STAGE APPROACH (single stage here for simplicity, explained below):
# We use a slim Python image to minimize the attack surface.
# Every package installed is a potential vulnerability.
# "slim" variants exclude many system packages included in full images.
#
# SECURITY PRACTICES APPLIED:
# 1. Non-root user: Apps should NEVER run as root inside containers.
#    If an attacker escapes the app, they'd have root on the host.
# 2. No unnecessary packages: We only install what we need.
# 3. Pinned base image tag: "python:3.11-slim" not just "python:latest"
#    (latest can change silently, introducing vulnerabilities)

# ---- Base Image ----
# python:3.11-slim = Python 3.11 on Debian slim (minimal system packages)
FROM python:3.11-slim

# ---- Build Arguments (can be overridden at build time) ----
ARG APP_USER=devguard
ARG APP_DIR=/app

# ---- System-level setup ----
# Install only essential system packages
# --no-install-recommends: Don't install "nice to have" packages
# rm -rf /var/lib/apt/lists/*: Clear apt cache to reduce image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ---- Create non-root user ----
# All subsequent commands run as this user, not root
RUN groupadd --gid 1001 ${APP_USER} && \
    useradd --uid 1001 --gid 1001 --no-create-home ${APP_USER}

# ---- Set working directory ----
WORKDIR ${APP_DIR}

# ---- Install Python dependencies ----
# Copy requirements FIRST (before app code).
# WHY? Docker layer caching.
# If requirements.txt doesn't change, Docker reuses the cached layer.
# This makes rebuilds much faster during development.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- Copy application code ----
COPY app/ ./app/
COPY wsgi.py .
COPY data/ ./data/

# ---- Create directories for reports and data ----
RUN mkdir -p reports && \
    chown -R ${APP_USER}:${APP_USER} ${APP_DIR}

# ---- Switch to non-root user ----
USER ${APP_USER}

# ---- Expose port ----
EXPOSE 5000

# ---- Health check ----
# Docker will periodically call this to check if the container is healthy.
# --interval=30s: Check every 30 seconds
# --timeout=10s: Fail if no response within 10 seconds
# --retries=3: Mark unhealthy after 3 failed checks
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

# ---- Start the application ----
# Gunicorn for production:
# --bind: Listen on all interfaces, port 5000
# --workers: 2 workers (adjust based on CPU cores: 2*cores + 1)
# --timeout: Kill workers that take longer than 120s
# --access-logfile: Log to stdout (Docker captures this)
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "wsgi:app"]
