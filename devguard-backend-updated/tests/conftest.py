"""
tests/conftest.py — Shared Test Fixtures
==========================================
WHY conftest.py?
- pytest automatically discovers and loads conftest.py.
- Fixtures defined here are available to ALL test files.
- No need to import them — pytest injects them by parameter name.

WHAT IS A FIXTURE?
- A fixture is a function that sets up (and optionally tears down)
  the state needed by a test.
- @pytest.fixture means "this is a fixture, not a test."
- yield separates setup (before) from teardown (after).

KEY FIXTURES WE DEFINE:
- app: Creates a test Flask app with isolated temp data directory
- client: Flask test client for making HTTP requests
- auth_headers: A JWT token for authenticated requests
"""

import os
import json
import shutil
import tempfile
import pytest
from app import create_app


@pytest.fixture(scope="session")
def app():
    """
    Create a Flask app configured for testing.

    scope="session" means this fixture is created ONCE per test session
    (not once per test). Faster — app creation is expensive.

    Testing config differences:
    - TESTING=True: Exceptions propagate (easier debugging)
    - DATA_DIR: Points to a temp directory (tests don't touch real data)
    - JWT expires in 5 seconds (not 1 hour)
    """
    # Create a temporary directory for test data
    test_data_dir = tempfile.mkdtemp()

    # Create the app with testing config
    flask_app = create_app("testing")

    # Override DATA_DIR to use our temp directory
    flask_app.config["DATA_DIR"] = test_data_dir

    # Initialize empty JSON files in the temp directory
    for filename in ["users.json", "pipelines.json", "scan_reports.json", "deployments.json"]:
        filepath = os.path.join(test_data_dir, filename)
        with open(filepath, "w") as f:
            json.dump([], f)

    yield flask_app

    # TEARDOWN: Clean up temp directory after all tests complete
    shutil.rmtree(test_data_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def client(app):
    """
    Flask test client for making HTTP requests.

    scope="function" means a fresh client for EACH test.
    This ensures test isolation — state from one test doesn't bleed
    into another.

    Usage in tests:
        def test_health(client):
            response = client.get("/api/v1/health")
            assert response.status_code == 200
    """
    with app.test_client() as testing_client:
        with app.app_context():
            yield testing_client


@pytest.fixture(scope="function")
def clean_data(app):
    """
    Reset all JSON data files to empty arrays before a test.

    Use this fixture on tests that need a clean slate.
    Without it, data from previous tests persists in the temp files.

    Usage:
        def test_empty_pipelines(client, clean_data):
            response = client.get("/api/v1/pipelines", headers=...)
            assert response.json["data"]["count"] == 0
    """
    data_dir = app.config["DATA_DIR"]
    for filename in ["users.json", "pipelines.json", "scan_reports.json", "deployments.json"]:
        filepath = os.path.join(data_dir, filename)
        with open(filepath, "w") as f:
            json.dump([], f)
    yield


@pytest.fixture(scope="function")
def auth_headers(client, clean_data):
    """
    Register a user and log in, returning JWT auth headers.

    Protected routes need: Authorization: Bearer <token>
    This fixture handles the whole flow so tests can focus
    on what they're actually testing.

    Usage:
        def test_list_pipelines(client, auth_headers):
            response = client.get("/api/v1/pipelines", headers=auth_headers)
            assert response.status_code == 200
    """
    # Register a test user
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "password": "TestPass123!"
    })

    # Log in and get the token
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "TestPass123!"
    })

    token = response.get_json()["data"]["access_token"]

    # Return headers dict — tests pass this to every authenticated request
    return {"Authorization": f"Bearer {token}"}
