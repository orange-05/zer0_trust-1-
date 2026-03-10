"""
app/api/scans.py — Security Scan Routes
=========================================
Endpoints:
- POST /api/v1/scans                  — Submit a scan result
- GET  /api/v1/scans                  — List all scans
- GET  /api/v1/scans/<id>             — Get specific scan
- GET  /api/v1/security-report        — Aggregate security metrics

The security-report endpoint is the KEY monitoring endpoint.
It's what Grafana queries to populate dashboard panels.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.services.scan_service import ScanService
from app.utils.validators import validate_scan
from app.utils.response import (
    created_response, success_response,
    validation_error_response, not_found_response, error_response
)

scans_bp = Blueprint("scans", __name__)


@scans_bp.route("/scans", methods=["POST"])
@jwt_required()
def create_scan():
    """
    POST /api/v1/scans

    Record a security scan result from the CI/CD pipeline.

    This is called by GitHub Actions after each security tool runs:
    - After Trivy dependency scan
    - After Trivy image scan
    - After filesystem scan

    Request:
    {
        "pipeline_id": "pl-a3f2b1c4",
        "scan_type": "dependency",
        "tool": "trivy",
        "status": "failed",
        "critical_count": 1,
        "high_count": 2,
        "report_path": "reports/trivy-deps.json"
    }

    Response (201):
    Full scan record with generated id and created_at.

    The deployment service will later check these scan records
    to decide if deployment is allowed (zero-trust gate).
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return error_response("Bad Request", "Request body must be valid JSON", 400)

    is_valid, error_msg = validate_scan(data)
    if not is_valid:
        return validation_error_response(error_msg)

    service = ScanService()
    scan, error = service.create_scan(data)

    if error:
        if "not found" in error.lower():
            return not_found_response("Pipeline")
        return error_response("Creation Failed", error, 400)

    return created_response(data=scan, message="Scan result recorded")


@scans_bp.route("/scans", methods=["GET"])
@jwt_required()
def list_scans():
    """
    GET /api/v1/scans

    List all scan results, newest first.

    Optional query parameter:
        ?pipeline_id=pl-a3f2b1c4  — filter by pipeline

    Response:
    {
        "success": true,
        "data": {
            "scans": [...],
            "count": 12
        }
    }
    """
    service = ScanService()

    # Optional filtering by pipeline_id
    pipeline_id = request.args.get("pipeline_id")
    if pipeline_id:
        from app.repositories.scan_repository import ScanRepository
        repo = ScanRepository()
        scans = repo.find_by_pipeline(pipeline_id)
    else:
        scans = service.get_all_scans()

    return success_response(data={
        "scans": scans,
        "count": len(scans)
    })


@scans_bp.route("/scans/<string:scan_id>", methods=["GET"])
@jwt_required()
def get_scan(scan_id):
    """
    GET /api/v1/scans/<scan_id>

    Get a specific scan result by ID.
    """
    service = ScanService()
    scan = service.get_scan_by_id(scan_id)

    if not scan:
        return not_found_response("Scan")

    return success_response(data=scan)


@scans_bp.route("/security-report", methods=["GET"])
@jwt_required()
def security_report():
    """
    GET /api/v1/security-report

    Aggregate security metrics across all scans.

    This is the KEY endpoint for the Grafana dashboard.
    Grafana queries this periodically to update panels.

    Response:
    {
        "success": true,
        "data": {
            "total_scans": 12,
            "passed": 8,
            "failed": 4,
            "critical_vulnerabilities": 2,
            "high_vulnerabilities": 6,
            "trust_status": "untrusted"
        }
    }

    trust_status:
    - "trusted": zero critical vulnerabilities
    - "untrusted": one or more critical vulnerabilities found
    """
    service = ScanService()
    report = service.get_security_report()

    return success_response(data=report)
