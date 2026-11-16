"""Celery tasks for running OCR jobs."""

import hashlib
import socket
import time
from datetime import datetime, timezone
from pathlib import Path

from celery import shared_task
from celery.utils.log import get_task_logger

# directly imports run_tesseract which is not explicitly exported by the pytesseract package
# The two exported functions we could use force a tmp file to be created and then deleted.
from pytesseract.pytesseract import run_tesseract

logger = get_task_logger(__name__)

@shared_task(bind=True)
def run_tesseract_job(
    self,
    filelist: str,
    languages: list[str],
    correlation_id: str | None = None,
) -> dict:
    """Run Tesseract over the files listed in filelist and write output PDF."""

    started = time.perf_counter()
    queue_wait_seconds = None
    submitted_at = (self.request.headers or {}).get("submitted_at")

    if submitted_at:
        try:
            submitted = datetime.fromisoformat(submitted_at)
            if submitted.utcoffset() is None:
                raise ValueError("Submission timestamp has no timezone")

            queue_wait_seconds = max(
                0.0,
                round(
                    (datetime.now(timezone.utc) - submitted).total_seconds(),
                    3,
                ),
            )
        except (ValueError, TypeError, OverflowError):
            logger.warning("Invalid Celery submission timestamp: %s", submitted_at)

    tesseract_seconds = None
    image_count = None
    status = "failure"
    error_type = None
    validation_complete = False

    try:
        # is filelist a valid file with at least one line?  If not, raise an error.
        filelist_path = Path(filelist)
        if not filelist_path.is_file():
            raise FileNotFoundError(
                f"File list {filelist} does not exist or is not a file."
            )

        with filelist_path.open("r", encoding="utf-8") as f:
            image_count = sum(1 for line in f if line.strip())

        if image_count == 0:
            raise ValueError(f"File list {filelist} is empty.")

        validation_complete = True


        # output_parent will be something like '/path/to/derivatives/{images_dir_name}'
        # output, or base name of the pdf, will look like '/path/to/derivatives/C124862721/C124862721'
        # tesseract appends the .pdf extension

        output_parent = filelist_path.parent
        output = str(output_parent / output_parent.name)

        # The state update does not need any meta, unless we want it for debugging or tracking.
        self.update_state(
            state="STARTED",
            meta={"filelist": filelist, "languages": languages},
        )

        kwargs = {
            "input_filename": filelist,
            "output_filename_base": output,
            "extension": "pdf",
            "lang": "+".join(languages),
        }

        output_path = Path(f"{output}.pdf")

        tesseract_started = time.perf_counter()
        try:
            run_tesseract(**kwargs)
        finally:
            tesseract_seconds = round(
                time.perf_counter() - tesseract_started, 3
            )

        if not output_path.is_file():
            raise FileNotFoundError(
                f"Tesseract did not create expected PDF: {output_path}"
            )

        with output_path.open("rb") as f:
            sha256 = hashlib.file_digest(f, "sha256").hexdigest()

        status = "success"

    except Exception as e:
        error_type = type(e).__name__

        logger.error(
            "Error running Tesseract: %s",
            e,
            extra={
                "job_id": self.request.id,
                "correlation_id": correlation_id,
            },
        )

        # Preserve original exception types for input validation errors.
        if not validation_complete and isinstance(e, (FileNotFoundError, ValueError)):
            raise

        raise RuntimeError(f"Error running Tesseract: {e}") from e

    finally:
        duration_seconds = round(time.perf_counter() - started, 3)

        logger.info(
            "OCR job finished",
            extra={
                "event": "ocr_job_finished",
                "job_id": self.request.id,
                "correlation_id": correlation_id,
                "status": status,
                "duration_seconds": duration_seconds,
                "tesseract_seconds": tesseract_seconds,
                "queue_wait_seconds": queue_wait_seconds,
                "image_count": image_count,
                "languages": languages,
                "worker_hostname": socket.gethostname(),
                "error_type": error_type,
            },
        )

    return {"output_path": str(output_path), "sha256": sha256}
