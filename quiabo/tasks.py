"""Celery tasks for running OCR jobs."""

import hashlib
from pathlib import Path

# directly imports run_tesseract which is not explicitly exported by the pytesseract package
# The two exported functions we could use force a tmp file to be created and then deleted.
from pytesseract.pytesseract import run_tesseract
from celery import shared_task


@shared_task(bind=True)
def run_tesseract_job(self, filelist: str, languages: list[str], output: str) -> dict:
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

    output = output.removesuffix(".pdf")

    output_dir = Path(output).parent
    if not output_dir.exists():
        raise FileNotFoundError(f"Output directory {output_dir} does not exist.")

    # The state update does not need any meta, unless we want it for debugging or tracking.
    self.update_state(
        state="STARTED",
        meta={"filelist": filelist, "languages": languages, "output": output},
    )

    kwargs = {
        "input_filename": filelist,
        "output_filename_base": output,
        "extension": "pdf",
        "lang": "+".join(languages),
    }

    try:
        run_tesseract(**kwargs)
        output_path = Path(f"{output}.pdf")
        with output_path.open("rb") as f:
            sha256 = hashlib.file_digest(f, "sha256").hexdigest()
    except Exception as e:
        raise RuntimeError(f"Error running Tesseract: {e}") from e

    return {"output_path": str(output_path), "sha256": sha256}
