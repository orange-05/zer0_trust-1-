"""
app/api/auth.py — Authentication Routes
=========================================
This blueprint handles:
- POST /api/v1/auth/register — Create a new user account
- POST /api/v1/auth/login    — Authenticate and get JWT token

ROUTE HANDLER PATTERN (what every route does):
1. Parse the request JSON body
2. Validate the input using our validators
3. Call the service layer to do business logic
4. Return a standard response

Routes should be THIN — no business logic here.
All real logic is in auth_service.py.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.auth_service import AuthService
from app.utils.validators import validate_registration, validate_login
from app.utils.response import (
    created_response, success_response,
    validation_error_response, error_response, conflict_response
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    POST /api/v1/auth/register

    Register a new user account.

    Request body:
    {
        "username": "admin",
        "password": "StrongPass123!"
    }

    Response (201 Created):
    {
        "success": true,
        "message": "User registered successfully",
        "data": {
            "id": "usr-abc123",
            "username": "admin",
            "created_at": "2026-03-09T10:00:00Z"
        }
    }

    Errors:
    - 400: Missing/invalid JSON body
    - 409: Username already taken
    - 422: Validation failed (weak password, etc.)
    """
    # Step 1: Parse JSON body
    # force=True: parse even without Content-Type: application/json header
    # silent=True: return None instead of raising error if body is not JSON
    data = request.get_json(force=True, silent=True)
    if not data:
        return error_response("Bad Request", "Request body must be valid JSON", 400)

    # Step 2: Validate input
    is_valid, error_msg = validate_registration(data)
    if not is_valid:
        return validation_error_response(error_msg)

    # Step 3: Call service
    service = AuthService()
    user, error = service.register(
        username=data["username"].strip(),
        password=data["password"]
    )

    # Step 4: Return response
    if error:
        # "Username already taken" is a 409 Conflict
        return conflict_response(error)

    return created_response(data=user, message="User registered successfully")


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/v1/auth/login

    Authenticate and receive a JWT access token.

    Request body:
    {
        "username": "admin",
        "password": "StrongPass123!"
    }

    Response (200 OK):
    {
        "success": true,
        "data": {
            "access_token": "eyJ...",
            "token_type": "bearer",
            "user": { "id": "...", "username": "admin" }
        }
    }

    HOW TO USE THE TOKEN:
    Include in subsequent requests as:
    Authorization: Bearer eyJ...
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return error_response("Bad Request", "Request body must be valid JSON", 400)

    is_valid, error_msg = validate_login(data)
    if not is_valid:
        return validation_error_response(error_msg)

    service = AuthService()
    result, error = service.login(
        username=data["username"].strip(),
        password=data["password"]
    )

    if error:
        # 401 for invalid credentials — not 404 (don't confirm user existence)
        return error_response("Unauthorized", error, 401)

    return success_response(data=result, message="Login successful")


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """
    GET /api/v1/auth/me

    Get the currently authenticated user's profile.
    Requires: Authorization: Bearer <token>

    @jwt_required() decorator:
    - Reads the Authorization header
    - Validates the JWT signature
    - If invalid/expired/missing → automatic 401 response
    - If valid → stores user ID, accessible via get_jwt_identity()

    Response:
    {
        "success": true,
        "data": { "user_id": "usr-abc123" }
    }
    """
    current_user_id = get_jwt_identity()
    return success_response(data={"user_id": current_user_id})
