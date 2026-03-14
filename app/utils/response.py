"""
app/utils/response.py — Standardized API Response Helpers
===========================================================
WHY RESPONSE HELPERS?
- Every API endpoint should return a consistent JSON structure.
- Instead of writing jsonify({...}) differently everywhere,
  we use these helper functions to enforce a standard format.

SUCCESS RESPONSE:
{
    "success": true,
    "data": { ... },
    "message": "Optional message"
}

ERROR RESPONSE:
{
    "success": false,
    "error": "Error Type",
    "message": "What went wrong"
}

This makes the API predictable — frontend or CI/CD consumers
always know where to look for data vs errors.
"""

from flask import jsonify
from typing import Any


def success_response(data: Any = None, message: str = None, status_code: int = 200):
    """
    Build a standard success response.

    Args:
        data: The payload to return (dict, list, etc.)
        message: Optional human-readable message
        status_code: HTTP status code (default 200)

    Returns:
        Flask Response object with JSON body
    """
    response = {"success": True}

    if message:
        response["message"] = message

    if data is not None:
        response["data"] = data

    return jsonify(response), status_code


def created_response(data: Any = None, message: str = "Resource created successfully"):
    """
    Shortcut for 201 Created responses.
    Used when a new resource (user, pipeline, scan) is created.
    """
    return success_response(data=data, message=message, status_code=201)


def error_response(error: str, message: str, status_code: int = 400):
    """
    Build a standard error response.

    Args:
        error: Short error type (e.g., "Validation Error")
        message: Human-readable explanation
        status_code: HTTP status code

    Returns:
        Flask Response object with JSON body
    """
    response = {
        "success": False,
        "error": error,
        "message": message,
        "status_code": status_code
    }
    return jsonify(response), status_code


def validation_error_response(message: str):
    """Shortcut for 422 Unprocessable Entity — bad input data."""
    return error_response("Validation Error", message, 422)


def not_found_response(resource: str = "Resource"):
    """Shortcut for 404 Not Found."""
    return error_response("Not Found", f"{resource} not found", 404)


def unauthorized_response(message: str = "Authentication required"):
    """Shortcut for 401 Unauthorized."""
    return error_response("Unauthorized", message, 401)


def conflict_response(message: str):
    """Shortcut for 409 Conflict — e.g., duplicate username."""
    return error_response("Conflict", message, 409)
