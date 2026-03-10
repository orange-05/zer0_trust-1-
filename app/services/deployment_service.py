"""
app/services/deployment_service.py — Deployment Business Logic
================================================================
THE DEPLOYMENT SERVICE IS WHERE ZERO-TRUST IS ENFORCED.

Before recording a deployment, it checks:
1. The referenced pipeline exists
2. The image was cryptographically signed (signed=True)
3. All security scans passed (no critical vulnerabilities)

If ANY check fails → deployment is REJECTED with a clear reason.
This is the "trust gate" from the project spec.

WHY ENFORCE HERE (SERVICE LAYER) AND NOT IN THE ROUTE?
- Routes only handle HTTP mechanics.
- Business rules live in services.
- If you add a CLI or scheduled job later, the same rules apply
  because they call the service, not the route.
"""

from typing import Dict, List, Optional, Tuple
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.pipeline_repository import PipelineRepository
from app.services.scan_service import ScanService


class DeploymentService:
    """Business logic for recording and validating deployments."""

    def create_deployment(self, data: Dict) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Record a deployment ONLY if all zero-trust checks pass.

        ZERO-TRUST GATES (in order):
        1. Pipeline must exist
        2. Image must be signed
        3. All security scans for this pipeline must have passed

        Args:
            data: Validated deployment data from request body

        Returns:
            (deployment_record, None) on success
            (None, rejection_reason) on failure
        """
        pipeline_repo = PipelineRepository()
        deploy_repo = DeploymentRepository()
        scan_service = ScanService()

        # ---- GATE 1: Pipeline must exist ----
        pipeline = pipeline_repo.get_by_id(data["pipeline_id"])
        if not pipeline:
            return None, f"Pipeline '{data['pipeline_id']}' not found"

        # ---- GATE 2: Image must be signed ----
        # An unsigned image could be tampered with between build and deploy.
        # Cosign signature verification ensures the image came from our pipeline.
        if not data.get("signed"):
            return None, (
                "DEPLOYMENT BLOCKED: Image is not signed. "
                "All production deployments require Cosign image signing."
            )

        # ---- GATE 3: Security scans must all pass ----
        is_safe, reason = scan_service.pipeline_is_safe_to_deploy(data["pipeline_id"])
        if not is_safe:
            return None, f"DEPLOYMENT BLOCKED: {reason}"

        # ---- ALL GATES PASSED — Record the deployment ----
        deployment = {
            "pipeline_id": data["pipeline_id"],
            "image_tag": data["image_tag"].strip(),
            "signed": data["signed"],
            "environment": data["environment"],
            "status": data.get("status", "deployed"),
        }

        saved = deploy_repo.save(deployment)
        return saved, None

    def get_all_deployments(self) -> List[Dict]:
        """Retrieve all deployment records, newest first."""
        repo = DeploymentRepository()
        deployments = repo.get_all()
        return sorted(deployments, key=lambda d: d.get("created_at", ""), reverse=True)

    def get_deployment_by_id(self, deployment_id: str) -> Optional[Dict]:
        """Get a single deployment record by ID."""
        repo = DeploymentRepository()
        return repo.get_by_id(deployment_id)
