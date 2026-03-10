"""
app/services/pipeline_service.py — Pipeline Business Logic
app/services/scan_service.py — Scan Business Logic
app/services/deployment_service.py — Deployment Business Logic
"""

# ================================================================
# PIPELINE SERVICE
# ================================================================
from typing import Dict, List, Optional, Tuple
from app.repositories.pipeline_repository import PipelineRepository


class PipelineService:
    """
    Business logic for CI/CD pipeline records.

    A pipeline record represents one run of the CI/CD pipeline:
    - It's created when GitHub Actions starts a run
    - It tracks the commit, branch, status, and who triggered it
    - Scan results and deployment records link back to it via pipeline_id
    """

    def create_pipeline(self, data: Dict) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Create a new pipeline run record.

        The status defaults to "running" if not provided.
        This is because pipelines are typically created at the START
        of a run, before we know if it passed or failed.

        Args:
            data: Validated request body

        Returns:
            (created_pipeline, None) on success
            (None, error_message) on failure
        """
        repo = PipelineRepository()

        pipeline = {
            "commit_id": data["commit_id"].strip(),
            "branch": data.get("branch", "unknown").strip(),
            "status": data.get("status", "running"),
            "triggered_by": data.get("triggered_by", "unknown").strip(),
        }

        saved = repo.save(pipeline)
        return saved, None

    def get_all_pipelines(self) -> List[Dict]:
        """
        Retrieve all pipeline records.

        Returns most recent first (reverse chronological order).
        The sort is by created_at string — ISO 8601 format sorts correctly
        as a string because it's year-month-day order.
        """
        repo = PipelineRepository()
        pipelines = repo.get_all()
        return sorted(pipelines, key=lambda p: p.get("created_at", ""), reverse=True)

    def get_pipeline_by_id(self, pipeline_id: str) -> Optional[Dict]:
        """Get a single pipeline by ID. Returns None if not found."""
        repo = PipelineRepository()
        return repo.get_by_id(pipeline_id)

    def update_pipeline_status(self, pipeline_id: str, status: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Update the status of a pipeline run.

        Called by GitHub Actions at the end of a run to mark
        the pipeline as "passed" or "failed".
        """
        allowed = ["running", "passed", "failed", "cancelled"]
        if status not in allowed:
            return None, f"Invalid status. Must be one of: {', '.join(allowed)}"

        repo = PipelineRepository()
        updated = repo.update(pipeline_id, {"status": status})

        if not updated:
            return None, "Pipeline not found"
        return updated, None
