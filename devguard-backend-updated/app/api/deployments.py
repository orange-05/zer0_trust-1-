"""
app/api/deployments.py — Deployment Record Routes
===================================================
Endpoints:
- POST /api/v1/deployments          — Record a deployment (with zero-trust check)
- GET  /api/v1/deployments          — List all deployments
- GET  /api/v1/deployments/<id>     — Get specific deployment

THE CRITICAL ENDPOINT: POST /api/v1/deployments
This is where the zero-trust gate is enforced.
GitHub Actions calls this ONLY after all checks pass,
but the service layer re-validates independently:
- Image must be signed
- Pipeline scans must have passed
- No critical vulnerabilities
If these rules aren't met, the deployment is REJECTED with 403 Forbidden.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.services.deployment_service import DeploymentService
from app.utils.validators import validate_deployment
from app.utils.response import (
    created_response, success_response,
    validation_error_response, not_found_response, error_response
)

deployments_bp = Blueprint("deployments", __name__)


@deployments_bp.route("/deployments", methods=["POST"])
@jwt_required()
def create_deployment():
    """
    POST /api/v1/deployments

    Record a deployment after passing all zero-trust checks.
    This is the FINAL step in the pipeline — deployment only
    reaches here if all prior stages passed.

    Request:
    {
        "pipeline_id": "pl-a3f2b1c4",
        "image_tag": "devguard-api:1.0.0",
        "signed": true,
        "environment": "production",
        "status": "deployed"
    }

    Response (201 — Trust gates passed):
    {
        "success": true,
        "message": "Deployment recorded successfully",
        "data": { full deployment object }
    }

    Response (403 — Trust gate failed):
    {
        "success": false,
        "error": "Deployment Blocked",
        "message": "DEPLOYMENT BLOCKED: Critical vulnerabilities found..."
    }

    WHY 403 AND NOT 400 FOR BLOCKED DEPLOYMENTS?
    - 400 Bad Request = invalid input format
    - 403 Forbidden = valid request, but policy prevents it
    - A blocked deployment is a POLICY DECISION, not a bad request.
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return error_response("Bad Request", "Request body must be valid JSON", 400)

    is_valid, error_msg = validate_deployment(data)
    if not is_valid:
        return validation_error_response(error_msg)

    service = DeploymentService()
    deployment, error = service.create_deployment(data)

    if error:
        if "not found" in error.lower():
            return not_found_response("Pipeline")
        # Zero-trust policy violation → 403 Forbidden
        return error_response("Deployment Blocked", error, 403)

    return created_response(data=deployment, message="Deployment recorded successfully")


@deployments_bp.route("/deployments", methods=["GET"])
@jwt_required()
def list_deployments():
    """
    GET /api/v1/deployments

    List all deployment records, newest first.

    Response:
    {
        "success": true,
        "data": {
            "deployments": [...],
            "count": 3,
            "signed_count": 3,
            "unsigned_count": 0
        }
    }

    We include signed vs unsigned counts so the Grafana dashboard
    can show a "policy compliance" panel.
    """
    service = DeploymentService()
    from app.repositories.deployment_repository import DeploymentRepository
    repo = DeploymentRepository()

    deployments = service.get_all_deployments()
    signed = len(repo.find_signed_deployments())
    unsigned = len(repo.find_unsigned_deployments())

    return success_response(data={
        "deployments": deployments,
        "count": len(deployments),
        "signed_count": signed,
        "unsigned_count": unsigned
    })


@deployments_bp.route("/deployments/<string:deployment_id>", methods=["GET"])
@jwt_required()
def get_deployment(deployment_id):
    """
    GET /api/v1/deployments/<deployment_id>

    Get a specific deployment record by ID.
    """
    service = DeploymentService()
    deployment = service.get_deployment_by_id(deployment_id)

    if not deployment:
        return not_found_response("Deployment")

    return success_response(data=deployment)
