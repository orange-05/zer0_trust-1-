"""
app/api/pipelines.py — Pipeline Run Routes
============================================
Endpoints:
- POST /api/v1/pipelines              — Create pipeline record
- GET  /api/v1/pipelines              — List all pipelines
- GET  /api/v1/pipelines/<id>         — Get specific pipeline
- PATCH /api/v1/pipelines/<id>/status — Update pipeline status

ALL ROUTES REQUIRE JWT:
- Pipeline data is sensitive security information.
- Only authenticated CI/CD systems or engineers should access it.
- The GitHub Actions workflow will log in first, then use the token.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.services.pipeline_service import PipelineService
from app.utils.validators import validate_pipeline
from app.utils.response import (
    created_response, success_response,
    validation_error_response, not_found_response, error_response
)

pipelines_bp = Blueprint("pipelines", __name__)


@pipelines_bp.route("/pipelines", methods=["POST"])
@jwt_required()
def create_pipeline():
    """
    POST /api/v1/pipelines

    Create a new CI/CD pipeline run record.
    Called at the START of a GitHub Actions workflow run.

    Request:
    {
        "commit_id": "abc123def456",
        "branch": "main",
        "status": "running",
        "triggered_by": "github-actions"
    }

    Response (201):
    {
        "success": true,
        "data": {
            "id": "pl-a3f2b1c4",
            "commit_id": "abc123def456",
            "branch": "main",
            "status": "running",
            "triggered_by": "github-actions",
            "created_at": "2026-03-09T10:10:00Z"
        }
    }
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return error_response("Bad Request", "Request body must be valid JSON", 400)

    is_valid, error_msg = validate_pipeline(data)
    if not is_valid:
        return validation_error_response(error_msg)

    service = PipelineService()
    pipeline, error = service.create_pipeline(data)

    if error:
        return error_response("Creation Failed", error, 400)

    return created_response(data=pipeline, message="Pipeline record created")


@pipelines_bp.route("/pipelines", methods=["GET"])
@jwt_required()
def list_pipelines():
    """
    GET /api/v1/pipelines

    List all pipeline runs, sorted newest first.

    Response:
    {
        "success": true,
        "data": {
            "pipelines": [...],
            "count": 5
        }
    }
    """
    service = PipelineService()
    pipelines = service.get_all_pipelines()

    return success_response(data={
        "pipelines": pipelines,
        "count": len(pipelines)
    })


@pipelines_bp.route("/pipelines/<string:pipeline_id>", methods=["GET"])
@jwt_required()
def get_pipeline(pipeline_id):
    """
    GET /api/v1/pipelines/<pipeline_id>

    Get a specific pipeline run by ID.

    Path parameter:
        pipeline_id: e.g., "pl-a3f2b1c4"

    Response: Single pipeline object or 404
    """
    service = PipelineService()
    pipeline = service.get_pipeline_by_id(pipeline_id)

    if not pipeline:
        return not_found_response("Pipeline")

    return success_response(data=pipeline)


@pipelines_bp.route("/pipelines/<string:pipeline_id>/status", methods=["PATCH"])
@jwt_required()
def update_pipeline_status(pipeline_id):
    """
    PATCH /api/v1/pipelines/<pipeline_id>/status

    Update the status of a pipeline (e.g., from "running" to "passed").
    Called at the END of a GitHub Actions workflow.

    WHY PATCH AND NOT PUT?
    - PUT replaces the entire resource.
    - PATCH updates only specific fields.
    - We only want to change status, not replace the whole pipeline.

    Request:
    {
        "status": "passed"
    }
    """
    data = request.get_json(force=True, silent=True)
    if not data or "status" not in data:
        return validation_error_response("'status' field is required")

    service = PipelineService()
    updated, error = service.update_pipeline_status(pipeline_id, data["status"])

    if error:
        if "not found" in error.lower():
            return not_found_response("Pipeline")
        return validation_error_response(error)

    return success_response(data=updated, message="Pipeline status updated")
