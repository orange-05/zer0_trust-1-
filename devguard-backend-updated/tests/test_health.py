"""
tests/test_health.py — Health Endpoint Tests
=============================================
Each test function tests ONE specific behaviour.
Test names describe what they verify.
"""

import pytest


@pytest.mark.health
def test_health_returns_200(client):
    """Health endpoint should return 200 OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.health
def test_health_returns_json(client):
    """Health endpoint should return JSON with 'success: true'."""
    response = client.get("/api/v1/health")
    data = response.get_json()
    assert data["success"] is True


@pytest.mark.health
def test_health_contains_status_field(client):
    """Health data should contain 'status: healthy'."""
    response = client.get("/api/v1/health")
    data = response.get_json()
    assert data["data"]["status"] == "healthy"


@pytest.mark.health
def test_health_contains_service_name(client):
    """Health data should identify the service."""
    response = client.get("/api/v1/health")
    data = response.get_json()
    assert data["data"]["service"] == "devguard-api"


@pytest.mark.health
def test_health_requires_no_auth(client):
    """Health endpoint must be accessible without a token."""
    # No Authorization header — should still work
    response = client.get("/api/v1/health")
    assert response.status_code == 200
