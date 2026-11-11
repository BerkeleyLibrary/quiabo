"""Celery tasks for running OCR jobs."""

import hashlib
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

    # is filelist a valid file with at least one line?  If not, raise an error.
    filelist_path = Path(filelist)
    if not filelist_path.is_file():
        raise FileNotFoundError(
            f"File list {filelist} does not exist or is not a file."
        )
    with filelist_path.open("r", encoding="utf-8") as f:
        if not any(line.strip() for line in f):
            raise ValueError(f"File list {filelist} is empty.")

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

    try:
        run_tesseract(**kwargs)

        if not output_path.is_file():
            raise FileNotFoundError(
                f"Tesseract did not create expected PDF: {output_path}"
            )

        with output_path.open("rb") as f:
            sha256 = hashlib.file_digest(f, "sha256").hexdigest()
    except Exception as e:
        logger.error(
            "Error running Tesseract: %s",
            e,
            extra={
                "job_id": self.request.id,
                "correlation_id": correlation_id,
            },
        )
        raise RuntimeError(f"Error running Tesseract: {e}") from e

    logger.info(
        "OCR job completed successfully: %s",
        output_path,
        extra={
            "job_id": self.request.id,
            "correlation_id": correlation_id,
        },
    )

    return {"output_path": str(output_path), "sha256": sha256}
