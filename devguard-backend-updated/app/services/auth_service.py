"""
app/services/auth_service.py — Authentication Business Logic
==============================================================
WHY A SERVICE LAYER?
- Routes should only handle HTTP: parse request, call service, return response.
- Services hold the business logic: "what must be true for this to succeed?"
- This separation makes services testable without HTTP (pure Python functions).

AUTH SERVICE RESPONSIBILITIES:
1. Register: validate username uniqueness → hash password → save user
2. Login: find user → verify password → create JWT token

HOW JWT AUTH WORKS IN THIS API:
1. User calls POST /api/v1/auth/login with username + password
2. auth_service verifies credentials
3. If valid, creates a JWT token signed with JWT_SECRET_KEY
4. Token is returned to client
5. Client stores token and sends it as: Authorization: Bearer <token>
6. Protected endpoints use @jwt_required() to verify the token
7. If token is invalid/expired, Flask-JWT-Extended returns 401
"""

from flask_jwt_extended import create_access_token
from app.repositories.user_repository import UserRepository
from app.utils.security import hash_password, verify_password
from typing import Dict, Tuple, Optional


class AuthService:
    """
    Handles user registration and authentication.

    All methods return (result_dict, error_message) tuples.
    - If error_message is None → success, use result_dict
    - If error_message is set → failure, return error to client
    """

    def register(self, username: str, password: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Register a new user.

        Steps:
        1. Check username is not already taken
        2. Hash the password (NEVER store plain text)
        3. Save user record to JSON store
        4. Return the created user (without password hash)

        Args:
            username: Desired username
            password: Plain-text password (will be hashed immediately)

        Returns:
            (user_dict, None) on success
            (None, error_message) on failure
        """
        repo = UserRepository()

        # Step 1: Check for duplicate username
        if repo.username_exists(username):
            return None, f"Username '{username}' is already taken"

        # Step 2: Hash password before storage
        # After this line, the original password is not stored anywhere.
        password_hash = hash_password(password)

        # Step 3: Build and save the user record
        user_record = {
            "username": username,
            "password_hash": password_hash,
            # Note: id and created_at are auto-added by JsonRepository.save()
        }
        saved_user = repo.save(user_record)

        # Step 4: Return user without password hash (never expose hashes)
        return self._sanitize_user(saved_user), None

    def login(self, username: str, password: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Authenticate a user and return a JWT token.

        Steps:
        1. Find user by username
        2. Verify password against stored hash
        3. Create and return JWT access token

        Args:
            username: Username entered at login
            password: Plain-text password entered at login

        Returns:
            ({"access_token": "...", "user": {...}}, None) on success
            (None, error_message) on failure

        SECURITY NOTE:
        - We return the SAME error for "user not found" and "wrong password".
        - Saying "user not found" specifically helps attackers enumerate usernames.
        - Generic "Invalid credentials" is the secure practice.
        """
        repo = UserRepository()

        # Step 1: Find user
        user = repo.find_by_username(username)

        # Step 2: Verify password — same error message for both failure cases
        if not user or not verify_password(password, user.get("password_hash", "")):
            return None, "Invalid credentials"

        # Step 3: Create JWT token
        # identity is what gets embedded in the token — we use user ID
        # so we can look up the user on protected endpoints
        access_token = create_access_token(identity=user["id"])

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": self._sanitize_user(user)
        }, None

    def _sanitize_user(self, user: Dict) -> Dict:
        """
        Remove sensitive fields before returning user data to the client.

        We NEVER return the password_hash to API consumers.
        Even hashes shouldn't be exposed — they could aid offline attacks.
        """
        return {
            "id": user.get("id"),
            "username": user.get("username"),
            "created_at": user.get("created_at"),
        }
