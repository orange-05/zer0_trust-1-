"""
tests/test_pipelines.py — Pipeline Endpoint Tests
"""

import pytest


@pytest.mark.pipelines
class TestCreatePipeline:

    def test_create_pipeline_success(self, client, auth_headers, clean_data):
        """Valid pipeline creation should return 201."""
        response = client.post("/api/v1/pipelines", headers=auth_headers, json={
            "commit_id": "abc123def456",
            "branch": "main",
            "status": "running",
            "triggered_by": "github-actions"
        })
        assert response.status_code == 201
        data = response.get_json()["data"]
        assert data["commit_id"] == "abc123def456"
        assert data["id"].startswith("pl-")
        assert "created_at" in data

    def test_create_pipeline_missing_commit(self, client, auth_headers, clean_data):
        """Missing commit_id should return 422."""
        response = client.post("/api/v1/pipelines", headers=auth_headers, json={
            "branch": "main",
            "triggered_by": "github-actions"
        })
        assert response.status_code == 422

    def test_create_pipeline_requires_auth(self, client, clean_data):
        """Pipeline creation without token should return 401."""
        response = client.post("/api/v1/pipelines", json={
            "commit_id": "abc123",
            "branch": "main",
            "triggered_by": "github-actions"
        })
        assert response.status_code == 401


@pytest.mark.pipelines
class TestGetPipelines:

    def test_list_pipelines_empty(self, client, auth_headers, clean_data):
        """Empty data store should return empty list."""
        response = client.get("/api/v1/pipelines", headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json()["data"]["count"] == 0

    def test_list_pipelines_after_create(self, client, auth_headers, clean_data):
        """After creating a pipeline, list should return it."""
        client.post("/api/v1/pipelines", headers=auth_headers, json={
            "commit_id": "abc123",
            "branch": "main",
            "triggered_by": "test"
        })
        response = client.get("/api/v1/pipelines", headers=auth_headers)
        assert response.get_json()["data"]["count"] == 1

    def test_get_pipeline_by_id(self, client, auth_headers, clean_data):
        """Should retrieve a specific pipeline by ID."""
        create_response = client.post("/api/v1/pipelines", headers=auth_headers, json={
            "commit_id": "findme123",
            "branch": "feature",
            "triggered_by": "push"
        })
        pipeline_id = create_response.get_json()["data"]["id"]

        response = client.get(f"/api/v1/pipelines/{pipeline_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json()["data"]["commit_id"] == "findme123"

    def test_get_nonexistent_pipeline(self, client, auth_headers, clean_data):
        """Non-existent pipeline ID should return 404."""
        response = client.get("/api/v1/pipelines/pl-notreal", headers=auth_headers)
        assert response.status_code == 404
