"""
run.py — Development Server Entry Point
=========================================
HOW TO RUN IN DEVELOPMENT:
    python run.py

This starts Flask's built-in development server.
DO NOT use this in production — use wsgi.py with Gunicorn instead.

WHY TWO ENTRY POINTS?
- run.py: Quick local development with auto-reload and debug mode
- wsgi.py: Production deployment with Gunicorn (multiple workers,
           proper logging, no debug info exposed)
"""

import os
from app import create_app

# Determine which config to use based on environment variable.
# If FLASK_ENV is not set, default to "development".
# In production, set: export FLASK_ENV=production
config_name = os.environ.get("FLASK_ENV", "development")

app = create_app(config_name)

if __name__ == "__main__":
    print(f"🚀 DevGuard API starting in {config_name} mode...")
    print(f"📡 Running on http://127.0.0.1:5000")
    print(f"🔒 Zero-Trust Security Pipeline — Ready")
    app.run(
        host="0.0.0.0",   # Listen on all interfaces (needed for Docker)
        port=5000,
        debug=(config_name == "development")
    )
