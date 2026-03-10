"""
wsgi.py — Production WSGI Entry Point
=======================================
Gunicorn uses this file to start the app in production.

HOW TO RUN IN PRODUCTION:
    gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:app

WHY GUNICORN?
- Flask's built-in server handles ONE request at a time.
- Gunicorn spawns multiple worker processes (e.g., 4 workers).
- Each worker can handle a request simultaneously.
- Production traffic would overwhelm Flask's single-threaded server.

WORKERS FORMULA (rule of thumb):
    workers = (2 × CPU cores) + 1
    For a 2-core VM: 5 workers

WHY GUNICORN OVER FLASK DEV SERVER?
- No debug info exposed (no tracebacks in responses)
- Handles concurrent connections properly
- Battle-tested in production
- Works behind nginx as a reverse proxy
"""

import os
from app import create_app

# Always use production config when running via gunicorn
config_name = os.environ.get("FLASK_ENV", "production")
app = create_app(config_name)
