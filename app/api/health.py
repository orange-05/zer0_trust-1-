"""
app/api/health.py — Health Check Endpoint
==========================================
WHY A HEALTH ENDPOINT?
- Load balancers (AWS ALB, nginx) probe /health to know if the app is alive.
- Kubernetes uses liveness/readiness probes on health endpoints.
- Monitoring tools (Grafana, Uptime Robot) check it periodically.
- It's the first endpoint you test after deployment to confirm it's running.

NO AUTH REQUIRED:
- Health checks must be accessible without a token.
- Otherwise, the system can't check health before a user logs in.

BLUEPRINT PATTERN:
- A Blueprint is a modular collection of routes.
- Instead of @app.route(...), we use @health_bp.route(...)
- This keeps related routes together and avoids one huge routes file.
- Blueprints are registered in create_app() with a url_prefix.
"""

from flask import Blueprint
from app.utils.response import success_response

# Create the Blueprint
# Name: "health" — must be unique across all blueprints
# __name__: helps Flask find templates/static files (not used here)
health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    GET /api/v1/health

    Returns a simple confirmation that the API is running.
    No authentication required.

    Response:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "service": "devguard-api",
            "version": "1.0.0"
        }
    }
    """
    return success_response(data={
        "status": "healthy",
        "service": "devguard-api",
        "version": "1.0.0"
    })
