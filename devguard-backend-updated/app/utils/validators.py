"""
app/utils/validators.py — Input Validation Functions
======================================================
WHY VALIDATE INPUTS?
- Never trust data from the outside world.
- Bad inputs can cause bugs, security vulnerabilities, or data corruption.
- Validate early, fail fast, return clear error messages.

VALIDATION STRATEGY:
- Each validator returns (is_valid: bool, error_message: str)
- If is_valid is False, the caller returns a 422 error to the client.
- This keeps validation logic OUT of the route handlers (clean code).
"""

import re
from typing import Tuple


def validate_registration(data: dict) -> Tuple[bool, str]:
    """
    Validate user registration input.

    Rules:
    - username: required, 3-50 chars, alphanumeric + underscore only
    - password: required, min 8 chars, must have upper+lower+digit

    Args:
        data: Parsed JSON body from request

    Returns:
        (True, "") if valid
        (False, "error message") if invalid
    """
    username = data.get("username", "").strip()
    password = data.get("password", "")

    # Username checks
    if not username:
        return False, "Username is required"
    if len(username) < 3 or len(username) > 50:
        return False, "Username must be between 3 and 50 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"

    # Password checks
    if not password:
        return False, "Password is required"
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    return True, ""


def validate_login(data: dict) -> Tuple[bool, str]:
    """
    Validate login input.

    Rules:
    - username: required
    - password: required
    """
    if not data.get("username", "").strip():
        return False, "Username is required"
    if not data.get("password", ""):
        return False, "Password is required"
    return True, ""


def validate_pipeline(data: dict) -> Tuple[bool, str]:
    """
    Validate pipeline creation input.

    Rules:
    - commit_id: required, 4-64 chars
    - branch: required
    - status: must be one of allowed values
    - triggered_by: required
    """
    allowed_statuses = ["running", "passed", "failed", "cancelled"]

    if not data.get("commit_id", "").strip():
        return False, "commit_id is required"
    if len(data["commit_id"]) < 4 or len(data["commit_id"]) > 64:
        return False, "commit_id must be between 4 and 64 characters"
    if not data.get("branch", "").strip():
        return False, "branch is required"
    if not data.get("triggered_by", "").strip():
        return False, "triggered_by is required"

    status = data.get("status", "")
    if status and status not in allowed_statuses:
        return False, f"status must be one of: {', '.join(allowed_statuses)}"

    return True, ""


def validate_scan(data: dict) -> Tuple[bool, str]:
    """
    Validate scan result submission.

    Rules:
    - pipeline_id: required
    - scan_type: must be one of allowed types
    - tool: required
    - status: must be passed or failed
    - critical_count, high_count: non-negative integers
    """
    allowed_scan_types = ["dependency", "image", "filesystem"]
    allowed_statuses = ["passed", "failed", "skipped"]

    if not data.get("pipeline_id", "").strip():
        return False, "pipeline_id is required"

    scan_type = data.get("scan_type", "")
    if scan_type not in allowed_scan_types:
        return False, f"scan_type must be one of: {', '.join(allowed_scan_types)}"

    if not data.get("tool", "").strip():
        return False, "tool is required"

    status = data.get("status", "")
    if status not in allowed_statuses:
        return False, f"status must be one of: {', '.join(allowed_statuses)}"

    # Validate vulnerability counts are non-negative integers
    for field in ["critical_count", "high_count"]:
        value = data.get(field, 0)
        if not isinstance(value, int) or value < 0:
            return False, f"{field} must be a non-negative integer"

    return True, ""


def validate_deployment(data: dict) -> Tuple[bool, str]:
    """
    Validate deployment record creation.

    Rules:
    - pipeline_id: required
    - image_tag: required
    - signed: must be boolean
    - environment: must be one of allowed values
    - status: must be one of allowed values
    """
    allowed_environments = ["development", "staging", "production"]
    allowed_statuses = ["deployed", "failed", "rolled_back"]

    if not data.get("pipeline_id", "").strip():
        return False, "pipeline_id is required"
    if not data.get("image_tag", "").strip():
        return False, "image_tag is required"

    signed = data.get("signed")
    if not isinstance(signed, bool):
        return False, "signed must be a boolean (true or false)"

    environment = data.get("environment", "")
    if environment not in allowed_environments:
        return False, f"environment must be one of: {', '.join(allowed_environments)}"

    status = data.get("status", "")
    if status not in allowed_statuses:
        return False, f"status must be one of: {', '.join(allowed_statuses)}"

    return True, ""
