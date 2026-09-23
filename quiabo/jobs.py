"""Routes for submitting and managing OCR jobs."""

import traceback

from pathlib import Path
from flask import Blueprint, request


bp = Blueprint("jobs", __name__, url_prefix="/jobs")


@bp.post("")
def create_job():
    """Submit a new OCR job."""
    job = request.get_json()

    try:
        for field in ("filelist", "languages", "output"):
            if field not in job:
                raise ValueError(f"{field} is required")

        if not isinstance(job["languages"], list):
            raise ValueError("languages must be a list")

        if not job["languages"]:
            raise ValueError("languages must not be empty")

        filelist = Path(job["filelist"])

        if not filelist.exists():
            raise FileNotFoundError(f"{filelist} does not exist")

    except (ValueError, FileNotFoundError) as error:
        return _error_response(error, 422)


    return {}, 202


def _error_response(error: Exception, status_code: int):
    """Build error response."""
    return {
        "status": "ERROR",
        "result": str(error),
        "traceback": traceback.format_exc(),
    }, status_code
