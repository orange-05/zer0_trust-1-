"""
app/repositories/pipeline_repository.py
app/repositories/scan_repository.py
app/repositories/deployment_repository.py
=========================================
These three repositories follow the same pattern as UserRepository:
- Inherit from JsonRepository (all CRUD is free)
- Add entity-specific query methods
- Get their file path from Flask app config (testable!)
"""

# ================================================================
# PIPELINE REPOSITORY
# ================================================================
import os
from flask import current_app
from app.repositories.json_repository import JsonRepository
from typing import List, Dict


class PipelineRepository(JsonRepository):
    """Manages pipeline run records in pipelines.json."""

    def __init__(self):
        data_dir = current_app.config["DATA_DIR"]
        file_path = os.path.join(data_dir, "pipelines.json")
        super().__init__(file_path=file_path, id_prefix="pl")

    def find_by_commit(self, commit_id: str) -> List[Dict]:
        """
        Find all pipeline runs triggered by a specific commit.

        Useful for: "show me all runs for commit abc123"
        """
        return self.find_by_field("commit_id", commit_id)

    def find_by_branch(self, branch: str) -> List[Dict]:
        """Find all pipeline runs on a specific branch."""
        return self.find_by_field("branch", branch)

    def find_by_status(self, status: str) -> List[Dict]:
        """
        Find all pipelines with a specific status.

        Used by Grafana metrics endpoint to count failures.
        """
        return self.find_by_field("status", status)
