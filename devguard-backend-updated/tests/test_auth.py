"""
tests/test_auth.py — Authentication Tests
===========================================
Tests cover:
- Successful registration
- Duplicate username rejection
- Password validation rules
- Successful login
- Invalid credentials rejection
- Token-protected endpoint access
"""

import pytest


@pytest.mark.auth
class TestRegistration:
    """Tests for POST /api/v1/auth/register"""

    def test_register_success(self, client, clean_data):
        """Valid registration should return 201 with user data."""
        response = client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "password": "ValidPass123!"
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["username"] == "newuser"
        # Password hash should NEVER be in the response
        assert "password_hash" not in data["data"]
        assert "password" not in data["data"]

    def test_register_duplicate_username(self, client, clean_data):
        """Registering the same username twice should return 409 Conflict."""
        client.post("/api/v1/auth/register", json={
            "username": "duplicate",
            "password": "ValidPass123!"
        })
        response = client.post("/api/v1/auth/register", json={
            "username": "duplicate",
            "password": "AnotherPass456!"
        })
        assert response.status_code == 409

    def test_register_weak_password(self, client, clean_data):
        """Password without uppercase should return 422."""
        response = client.post("/api/v1/auth/register", json={
            "username": "user1",
            "password": "weakpassword1"  # No uppercase
        })
        assert response.status_code == 422

    def test_register_short_password(self, client, clean_data):
        """Password under 8 chars should return 422."""
        response = client.post("/api/v1/auth/register", json={
            "username": "user2",
            "password": "Ab1!"  # Too short
        })
        assert response.status_code == 422

    def test_register_no_username(self, client, clean_data):
        """Missing username should return 422."""
        response = client.post("/api/v1/auth/register", json={
            "password": "ValidPass123!"
        })
        assert response.status_code == 422

    def test_register_assigns_id(self, client, clean_data):
        """Registered user should have an auto-generated ID."""
        response = client.post("/api/v1/auth/register", json={
            "username": "idtest",
            "password": "ValidPass123!"
        })
        assert response.status_code == 201
        user_id = response.get_json()["data"]["id"]
        assert user_id.startswith("usr-")


@pytest.mark.auth
class TestLogin:
    """Tests for POST /api/v1/auth/login"""

    def test_login_success(self, client, clean_data):
        """Valid credentials should return 200 with JWT token."""
        client.post("/api/v1/auth/register", json={
            "username": "logintest",
            "password": "ValidPass123!"
        })
        response = client.post("/api/v1/auth/login", json={
            "username": "logintest",
            "password": "ValidPass123!"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    def test_login_wrong_password(self, client, clean_data):
        """Wrong password should return 401."""
        client.post("/api/v1/auth/register", json={
            "username": "wrongpass",
            "password": "CorrectPass123!"
        })
        response = client.post("/api/v1/auth/login", json={
            "username": "wrongpass",
            "password": "WrongPassword999!"
        })
        assert response.status_code == 401

    def test_login_unknown_user(self, client, clean_data):
        """Non-existent user should return 401 (not 404)."""
        # We return 401 for both "wrong password" and "user not found"
        # to prevent username enumeration attacks
        response = client.post("/api/v1/auth/login", json={
            "username": "doesnotexist",
            "password": "SomePass123!"
        })
        assert response.status_code == 401

    def test_protected_route_without_token(self, client):
        """Accessing protected route without token should return 401."""
        response = client.get("/api/v1/pipelines")
        assert response.status_code == 401

    def test_protected_route_with_token(self, client, auth_headers):
        """Accessing protected route with valid token should work."""
        response = client.get("/api/v1/pipelines", headers=auth_headers)
        assert response.status_code == 200
