"""
app/repositories/deployment_repository.py — Deployment Records Data Access
"""

import os
from flask import current_app
from app.repositories.json_repository import JsonRepository
from typing import Dict, List


class DeploymentRepository(JsonRepository):
    """Manages deployment records in deployments.json."""

    def __init__(self):
        data_dir = current_app.config["DATA_DIR"]
        file_path = os.path.join(data_dir, "deployments.json")
        super().__init__(file_path=file_path, id_prefix="dp")

    def find_by_pipeline(self, pipeline_id: str) -> List[Dict]:
        """Get all deployments triggered by a specific pipeline."""
        return self.find_by_field("pipeline_id", pipeline_id)

    def find_by_environment(self, environment: str) -> List[Dict]:
        """
        Get all deployments to a specific environment.

        Useful for: "show all production deployments"
        """
        return self.find_by_field("environment", environment)

    def find_signed_deployments(self) -> List[Dict]:
        """
        Get all deployments where the image was cryptographically signed.

        In zero-trust, unsigned deployments should never reach production.
        This method lets us audit and verify compliance.
        """
        return [
            dep for dep in self.get_all()
            if dep.get("signed") is True
        ]

    def find_unsigned_deployments(self) -> List[Dict]:
        """
        Get all deployments where signed=False.

        These represent potential security policy violations.
        Should be zero in a healthy zero-trust system.
        """
        return [
            dep for dep in self.get_all()
            if dep.get("signed") is not True
        ]
