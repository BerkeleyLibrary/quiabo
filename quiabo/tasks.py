import subprocess
from pathlib import Path

from celery import shared_task


@shared_task(bind=True)
def run_tesseract_job(self, filelist: str, languages: list[str], output: str) -> dict:
    """Run Tesseract over the files listed in filelist and write output PDF."""
    # The state update does not need any meta, unless we want it for debugging or tracking.
    self.update_state(
        state="STARTED",
        meta={"filelist": filelist, "languages": languages, "output": output},
    )

    command = ["tesseract", "-l", ",".join(languages), filelist, output, "pdf"]
    subprocess.run(command, check=True, capture_output=True, text=True)

    return {"output": f"{output}.pdf"}
