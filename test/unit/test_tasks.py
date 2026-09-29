"""Unit tests for the shared task defined in ``tasks.py``."""

import hashlib
from pathlib import Path
from unittest.mock import Mock

import pytest

from quiabo.tasks import run_tesseract_job


def test_shared_task_is_registered():
    """Verify that the Tesseract task is registered with Celery."""
    task = run_tesseract_job

    assert task.name
    assert task.app.tasks[task.name].name == task.name
    assert callable(task.run)


def test_shared_task_delay_delegates_to_apply_async(monkeypatch):
    """Verify that delaying the task delegates to ``apply_async``."""
    apply_async = Mock(return_value="queued")
    monkeypatch.setattr(run_tesseract_job, "apply_async", apply_async)

    result = run_tesseract_job.delay("filelist.txt", ["eng", "spa"], "output")

    assert result == "queued"
    apply_async.assert_called_once_with(
        ("filelist.txt", ["eng", "spa"], "output"),
        {},
    )


def test_run_tesseract_job_updates_state_and_returns_digest(monkeypatch, tmp_path):
    """Verify that the task runs Tesseract and returns the PDF digest."""
    filelist = tmp_path / "files.txt"
    filelist.touch()
    output = tmp_path / "output"
    pdf_contents = b"generated PDF"

    update_state = Mock()
    run = Mock()

    def write_output(**kwargs):
        Path(f"{kwargs['output_filename_base']}.pdf").write_bytes(pdf_contents)

    run.side_effect = write_output
    monkeypatch.setattr(run_tesseract_job, "update_state", update_state)
    monkeypatch.setattr("quiabo.tasks.run_tesseract", run)

    result = run_tesseract_job.run(
        str(filelist),
        ["eng", "spa"],
        str(output),
    )

    update_state.assert_called_once_with(
        state="STARTED",
        meta={
            "filelist": str(filelist),
            "languages": ["eng", "spa"],
            "output": str(output),
        },
    )
    run.assert_called_once_with(
        input_filename=str(filelist),
        output_filename_base=str(output),
        extension="pdf",
        lang="eng+spa",
    )
    assert result == {
        "output_path": f"{output}.pdf",
        "sha256": hashlib.sha256(pdf_contents).hexdigest(),
    }


def test_run_tesseract_job_removes_pdf_suffix(monkeypatch):
    """Verify that an existing PDF suffix is removed before invocation."""
    update_state = Mock()
    run = Mock()

    def write_output(**kwargs):
        Path(f"{kwargs['output_filename_base']}.pdf").touch()

    run.side_effect = write_output
    monkeypatch.setattr(run_tesseract_job, "update_state", update_state)
    monkeypatch.setattr("quiabo.tasks.run_tesseract", run)

    result = run_tesseract_job.run("files.txt", ["eng"], "output.pdf")

    update_state.assert_called_once_with(
        state="STARTED",
        meta={
            "filelist": "files.txt",
            "languages": ["eng"],
            "output": "output",
        },
    )
    run.assert_called_once_with(
        input_filename="files.txt",
        output_filename_base="output",
        extension="pdf",
        lang="eng",
    )
    assert result == {
        "output_path": "output.pdf",
        "sha256": hashlib.sha256(b"").hexdigest(),
    }


def test_run_tesseract_job_requires_existing_output_directory(tmp_path):
    """Verify that the task rejects a missing output directory."""
    output = tmp_path / "missing" / "output"

    with pytest.raises(FileNotFoundError, match="does not exist"):
        run_tesseract_job.run("files.txt", ["eng"], str(output))


def test_run_tesseract_job_wraps_tesseract_errors(monkeypatch, tmp_path):
    """Verify that Tesseract errors are wrapped with task context."""
    output = tmp_path / "output"
    error = RuntimeError("Tesseract failed")
    run = Mock(side_effect=error)
    monkeypatch.setattr("quiabo.tasks.run_tesseract", run)

    with pytest.raises(
        RuntimeError, match="Error running Tesseract: Tesseract failed"
    ) as exc_info:
        run_tesseract_job.run("files.txt", ["eng"], str(output))

    assert exc_info.value.__cause__ is error
