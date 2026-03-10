"""
app/errors.py — Centralized Error Handling
============================================
WHY CENTRALIZED ERROR HANDLING?
- Without this, Flask returns HTML error pages for 404, 500, etc.
- Our API should ALWAYS return JSON — even for errors.
- Registering error handlers once here covers the entire app.

HOW IT WORKS:
- @app.errorhandler(404) catches all 404 errors app-wide.
- We return a JSON response with a consistent structure.

CONSISTENT ERROR STRUCTURE:
Every error response looks like:
{
    "error": "Not Found",
    "message": "The requested resource does not exist",
    "status_code": 404
}
"""

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask) -> None:
    """Register all error handlers on the Flask app."""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "error": "Bad Request",
            "message": str(error.description) if hasattr(error, "description") else "Bad request",
            "status_code": 400
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            "error": "Unauthorized",
            "message": "Authentication is required to access this resource",
            "status_code": 401
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            "error": "Forbidden",
            "message": "You do not have permission to access this resource",
            "status_code": 403
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource does not exist",
            "status_code": 404
        }), 404

    @app.errorhandler(409)
    def conflict(error):
        return jsonify({
            "error": "Conflict",
            "message": str(error.description) if hasattr(error, "description") else "Resource conflict",
            "status_code": 409
        }), 409

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "error": "Unprocessable Entity",
            "message": str(error.description) if hasattr(error, "description") else "Validation failed",
            "status_code": 422
        }), 422

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "status_code": 500
        }), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Catch-all for any other HTTP exceptions."""
        return jsonify({
            "error": error.name,
            "message": error.description,
            "status_code": error.code
        }), error.code
