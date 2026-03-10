"""
tests/test_scans.py — Security Scan Endpoint Tests
tests/test_deployments.py — Deployment Endpoint Tests (Zero-Trust)
"""

import pytest


# ================================================================
# SCAN TESTS
# ================================================================

@pytest.mark.scans
class TestScans:

    def _create_pipeline(self, client, headers):
        """Helper: create a pipeline and return its ID."""
        resp = client.post("/api/v1/pipelines", headers=headers, json={
            "commit_id": "scan-test-commit",
            "branch": "main",
            "triggered_by": "test"
        })
        return resp.get_json()["data"]["id"]

    def test_create_scan_success(self, client, auth_headers, clean_data):
        """Valid scan submission should return 201."""
        pipeline_id = self._create_pipeline(client, auth_headers)
        response = client.post("/api/v1/scans", headers=auth_headers, json={
            "pipeline_id": pipeline_id,
            "scan_type": "dependency",
            "tool": "trivy",
            "status": "passed",
            "critical_count": 0,
            "high_count": 1,
            "report_path": "reports/trivy-deps.json"
        })
        assert response.status_code == 201
        data = response.get_json()["data"]
        assert data["id"].startswith("sc-")
        assert data["scan_type"] == "dependency"

    def test_create_scan_invalid_type(self, client, auth_headers, clean_data):
        """Invalid scan_type should return 422."""
        pipeline_id = self._create_pipeline(client, auth_headers)
        response = client.post("/api/v1/scans", headers=auth_headers, json={
            "pipeline_id": pipeline_id,
            "scan_type": "invalid-type",
            "tool": "trivy",
            "status": "passed",
            "critical_count": 0,
            "high_count": 0
        })
        assert response.status_code == 422

    def test_create_scan_nonexistent_pipeline(self, client, auth_headers, clean_data):
        """Scan for non-existent pipeline should return 404."""
        response = client.post("/api/v1/scans", headers=auth_headers, json={
            "pipeline_id": "pl-doesnotexist",
            "scan_type": "image",
            "tool": "trivy",
            "status": "passed",
            "critical_count": 0,
            "high_count": 0
        })
        assert response.status_code == 404

    def test_security_report_structure(self, client, auth_headers, clean_data):
        """Security report should return all required fields."""
        response = client.get("/api/v1/security-report", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()["data"]
        required_fields = [
            "total_scans", "passed", "failed",
            "critical_vulnerabilities", "high_vulnerabilities", "trust_status"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_security_report_trust_status_trusted(self, client, auth_headers, clean_data):
        """With no critical vulns, trust_status should be 'trusted'."""
        pipeline_id = self._create_pipeline(client, auth_headers)
        client.post("/api/v1/scans", headers=auth_headers, json={
            "pipeline_id": pipeline_id,
            "scan_type": "dependency",
            "tool": "trivy",
            "status": "passed",
            "critical_count": 0,
            "high_count": 0
        })
        response = client.get("/api/v1/security-report", headers=auth_headers)
        assert response.get_json()["data"]["trust_status"] == "trusted"

    def test_security_report_trust_status_untrusted(self, client, auth_headers, clean_data):
        """With critical vulns, trust_status should be 'untrusted'."""
        pipeline_id = self._create_pipeline(client, auth_headers)
        client.post("/api/v1/scans", headers=auth_headers, json={
            "pipeline_id": pipeline_id,
            "scan_type": "image",
            "tool": "trivy",
            "status": "failed",
            "critical_count": 3,
            "high_count": 5
        })
        response = client.get("/api/v1/security-report", headers=auth_headers)
        assert response.get_json()["data"]["trust_status"] == "untrusted"


# ================================================================
# DEPLOYMENT TESTS — This is where zero-trust is tested
# ================================================================

@pytest.mark.deployments
class TestDeployments:

    def _setup_safe_pipeline(self, client, headers):
        """
        Helper: Create a pipeline with a passed scan.
        This pipeline should be ALLOWED to deploy.
        """
        pipeline_resp = client.post("/api/v1/pipelines", headers=headers, json={
            "commit_id": "safe-commit-abc",
            "branch": "main",
            "triggered_by": "github-actions"
        })
        pipeline_id = pipeline_resp.get_json()["data"]["id"]

        client.post("/api/v1/scans", headers=headers, json={
            "pipeline_id": pipeline_id,
            "scan_type": "dependency",
            "tool": "trivy",
            "status": "passed",
            "critical_count": 0,
            "high_count": 0
        })
        client.post("/api/v1/scans", headers=headers, json={
            "pipeline_id": pipeline_id,
            "scan_type": "image",
            "tool": "trivy",
            "status": "passed",
            "critical_count": 0,
            "high_count": 1
        })
        return pipeline_id

    def _setup_risky_pipeline(self, client, headers):
        """
        Helper: Create a pipeline with a FAILED scan.
        This pipeline should be BLOCKED from deploying.
        """
        pipeline_resp = client.post("/api/v1/pipelines", headers=headers, json={
            "commit_id": "risky-commit-xyz",
            "branch": "main",
            "triggered_by": "github-actions"
        })
        pipeline_id = pipeline_resp.get_json()["data"]["id"]

        client.post("/api/v1/scans", headers=headers, json={
            "pipeline_id": pipeline_id,
            "scan_type": "image",
            "tool": "trivy",
            "status": "failed",
            "critical_count": 2,
            "high_count": 8
        })
        return pipeline_id

    def test_deployment_allowed_when_all_checks_pass(self, client, auth_headers, clean_data):
        """
        HAPPY PATH: Signed image + passed scans = deployment allowed.
        This is the normal successful deployment flow.
        """
        pipeline_id = self._setup_safe_pipeline(client, auth_headers)
        response = client.post("/api/v1/deployments", headers=auth_headers, json={
            "pipeline_id": pipeline_id,
            "image_tag": "devguard-api:1.0.0",
            "signed": True,
            "environment": "production",
            "status": "deployed"
        })
        assert response.status_code == 201
        data = response.get_json()["data"]
        assert data["signed"] is True
        assert data["environment"] == "production"

    def test_deployment_blocked_unsigned_image(self, client, auth_headers, clean_data):
        """
        ZERO-TRUST GATE: Unsigned image must be rejected.
        Even if scans passed, unsigned = blocked.
        """
        pipeline_id = self._setup_safe_pipeline(client, auth_headers)
        response = client.post("/api/v1/deployments", headers=auth_headers, json={
            "pipeline_id": pipeline_id,
            "image_tag": "devguard-api:1.0.0",
            "signed": False,  # ← This should cause rejection
            "environment": "production",
            "status": "deployed"
        })
        assert response.status_code == 403
        assert "DEPLOYMENT BLOCKED" in response.get_json()["message"]

    def test_deployment_blocked_critical_vulnerabilities(self, client, auth_headers, clean_data):
        """
        ZERO-TRUST GATE: Critical vulnerabilities block deployment.
        Even if image is signed, critical vulns = blocked.
        """
        pipeline_id = self._setup_risky_pipeline(client, auth_headers)
        response = client.post("/api/v1/deployments", headers=auth_headers, json={
            "pipeline_id": pipeline_id,
            "image_tag": "devguard-api:1.0.0",
            "signed": True,  # Signed, but scans failed
            "environment": "production",
            "status": "deployed"
        })
        assert response.status_code == 403
        assert "DEPLOYMENT BLOCKED" in response.get_json()["message"]

    def test_deployment_blocked_no_scans(self, client, auth_headers, clean_data):
        """
        ZERO-TRUST GATE: Pipeline with no scans must be blocked.
        "No evidence of security" is not the same as "secure."
        """
        # Create pipeline but run NO scans
        pipeline_resp = client.post("/api/v1/pipelines", headers=auth_headers, json={
            "commit_id": "noscan-commit",
            "branch": "main",
            "triggered_by": "test"
        })
        pipeline_id = pipeline_resp.get_json()["data"]["id"]

        response = client.post("/api/v1/deployments", headers=auth_headers, json={
            "pipeline_id": pipeline_id,
            "image_tag": "devguard-api:1.0.0",
            "signed": True,
            "environment": "production",
            "status": "deployed"
        })
        assert response.status_code == 403

    def test_list_deployments_shows_signing_counts(self, client, auth_headers, clean_data):
        """Deployment list should include signed vs unsigned counts."""
        pipeline_id = self._setup_safe_pipeline(client, auth_headers)
        client.post("/api/v1/deployments", headers=auth_headers, json={
            "pipeline_id": pipeline_id,
            "image_tag": "devguard-api:1.0.0",
            "signed": True,
            "environment": "production",
            "status": "deployed"
        })
        response = client.get("/api/v1/deployments", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert "signed_count" in data
        assert "unsigned_count" in data
        assert data["signed_count"] == 1
