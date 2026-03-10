"""
app/services/scan_service.py — Security Scan Business Logic
=============================================================
The scan service is the HEART of the zero-trust model.

It stores scan results AND enforces the trust policy:
- A scan result tells us: did this scan pass or fail?
- How many critical/high vulnerabilities were found?
- The security report aggregates all scans.

ZERO-TRUST RULE:
  deployment is blocked if ANY scan has critical_count > 0
  or if scan status is "failed"
"""

from typing import Dict, List, Optional, Tuple
from app.repositories.scan_repository import ScanRepository
from app.repositories.pipeline_repository import PipelineRepository


class ScanService:
    """Business logic for security scan results."""

    def create_scan(self, data: Dict) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Record a new security scan result.

        This is called by GitHub Actions after each scan tool runs.
        The CI pipeline posts the result here via the API.

        Args:
            data: Validated scan data from request body

        Returns:
            (saved_scan, None) on success
            (None, error_message) on failure
        """
        scan_repo = ScanRepository()
        pipeline_repo = PipelineRepository()

        # Verify the referenced pipeline actually exists
        # We don't want orphaned scan records
        pipeline = pipeline_repo.get_by_id(data["pipeline_id"])
        if not pipeline:
            return None, f"Pipeline '{data['pipeline_id']}' not found"

        scan = {
            "pipeline_id": data["pipeline_id"],
            "scan_type": data["scan_type"],
            "tool": data["tool"].strip(),
            "status": data["status"],
            "critical_count": data.get("critical_count", 0),
            "high_count": data.get("high_count", 0),
            "report_path": data.get("report_path", ""),
        }

        saved = scan_repo.save(scan)
        return saved, None

    def get_all_scans(self) -> List[Dict]:
        """Retrieve all scan records, newest first."""
        repo = ScanRepository()
        scans = repo.get_all()
        return sorted(scans, key=lambda s: s.get("created_at", ""), reverse=True)

    def get_scan_by_id(self, scan_id: str) -> Optional[Dict]:
        """Get a single scan by ID."""
        repo = ScanRepository()
        return repo.get_by_id(scan_id)

    def get_security_report(self) -> Dict:
        """
        Generate the aggregate security report.

        This is what GET /api/v1/security-report returns.
        Powers the Grafana dashboard panels.

        The report answers:
        - How many scans total?
        - How many passed vs failed?
        - Total critical and high vulnerabilities found?
        """
        repo = ScanRepository()
        summary = repo.get_security_summary()

        # Add trust status to the report
        # The system is "trusted" only when there are zero critical vulns
        summary["trust_status"] = (
            "trusted" if summary["critical_vulnerabilities"] == 0
            else "untrusted"
        )
        return summary

    def pipeline_is_safe_to_deploy(self, pipeline_id: str) -> Tuple[bool, str]:
        """
        ZERO-TRUST GATE: Determine if a pipeline is safe to deploy.

        Rules (all must pass):
        1. At least one scan must exist for this pipeline
        2. No scan must have status "failed"
        3. No scan must have critical_count > 0

        Args:
            pipeline_id: The pipeline to evaluate

        Returns:
            (True, "safe") if deployment should be allowed
            (False, reason) if deployment should be blocked

        This is the core security enforcement function.
        """
        repo = ScanRepository()
        scans = repo.find_by_pipeline(pipeline_id)

        if not scans:
            return False, "No security scans found for this pipeline"

        for scan in scans:
            if scan.get("status") == "failed":
                return False, (
                    f"Security scan '{scan['scan_type']}' using '{scan['tool']}' "
                    f"failed — deployment blocked"
                )
            if scan.get("critical_count", 0) > 0:
                return False, (
                    f"Critical vulnerabilities found in '{scan['scan_type']}' scan "
                    f"({scan['critical_count']} critical) — deployment blocked"
                )

        return True, "All security checks passed"
