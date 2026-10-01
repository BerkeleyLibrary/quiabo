"""Routes for submitting and managing OCR jobs."""

import traceback
from pathlib import Path

from celery.result import AsyncResult
from flask import Blueprint, request

from quiabo.tasks import run_tesseract_job


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

        if not filelist.is_file():
            raise FileNotFoundError(f"{filelist} does not exist or is not a file")

    except (ValueError, FileNotFoundError) as error:
        return _error_response(error, 422)


    try:
        celery_result = run_tesseract_job.delay(
            job["filelist"],
            job["languages"],
            job["output"],
        )
    except Exception as error:  # pylint: disable=broad-exception-caught
        return _error_response(error, 500)

    return {
        "job_id": celery_result.id,
        "status": "PENDING",
        "job_status": f"/jobs/{celery_result.id}",
    }, 202

@bp.get("/<job_id>")
def get_job(job_id: str):
    """Get the status of an OCR job."""
    celery_result = AsyncResult(job_id)

    response = {
        "id": job_id,
        "status": celery_result.state,
    }

    if celery_result.state == "SUCCESS":
        response["result"] = celery_result.result
        response["date_done"] = celery_result.date_done.isoformat()

    if celery_result.state == "FAILURE":
        response["result"] = str(celery_result.result)
        response["traceback"] = celery_result.traceback

    return response, 200


def _error_response(error: Exception, status_code: int):
    """Build error response."""
    return {
        "status": "ERROR",
        "result": str(error),
        "traceback": traceback.format_exc(),
    }, status_code
