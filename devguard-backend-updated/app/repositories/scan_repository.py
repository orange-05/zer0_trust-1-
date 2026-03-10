"""
app/repositories/scan_repository.py — Scan Results Data Access
"""

import os
from flask import current_app
from app.repositories.json_repository import JsonRepository
from typing import List, Dict


class ScanRepository(JsonRepository):
    """Manages security scan records in scan_reports.json."""

    def __init__(self):
        data_dir = current_app.config["DATA_DIR"]
        file_path = os.path.join(data_dir, "scan_reports.json")
        super().__init__(file_path=file_path, id_prefix="sc")

    def find_by_pipeline(self, pipeline_id: str) -> List[Dict]:
        """
        Get all scans run for a specific pipeline.

        Used to build the full security picture for one pipeline run.
        Example: pl-001 has 3 scans: dependency, image, filesystem
        """
        return self.find_by_field("pipeline_id", pipeline_id)

    def find_by_scan_type(self, scan_type: str) -> List[Dict]:
        """Find all scans of a specific type (dependency/image/filesystem)."""
        return self.find_by_field("scan_type", scan_type)

    def find_by_status(self, status: str) -> List[Dict]:
        """
        Find all scans with a given status (passed/failed).

        Used by the security report endpoint to count failures.
        """
        return self.find_by_field("status", status)

    def get_critical_scans(self) -> List[Dict]:
        """
        Return all scans that found at least one critical vulnerability.

        The zero-trust policy blocks deployment if critical vulns exist.
        This method powers the security dashboard.
        """
        return [
            scan for scan in self.get_all()
            if scan.get("critical_count", 0) > 0
        ]

    def get_security_summary(self) -> Dict:
        """
        Compute aggregate security statistics across all scans.

        This powers the GET /api/v1/security-report endpoint.

        Returns:
            Dict with total_scans, passed, failed, vulnerability counts
        """
        all_scans = self.get_all()
        total = len(all_scans)
        passed = sum(1 for s in all_scans if s.get("status") == "passed")
        failed = total - passed
        critical_total = sum(s.get("critical_count", 0) for s in all_scans)
        high_total = sum(s.get("high_count", 0) for s in all_scans)

        return {
            "total_scans": total,
            "passed": passed,
            "failed": failed,
            "critical_vulnerabilities": critical_total,
            "high_vulnerabilities": high_total,
        }
