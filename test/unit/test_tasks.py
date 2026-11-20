"""Unit tests for the shared task defined in ``tasks.py``."""

import errno
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock
from quiabo import app

import pytest

from pytesseract.pytesseract import TesseractError
from quiabo.tasks import is_retryable_error, run_tesseract_job

@pytest.mark.parametrize(
    "error",
    [
        FileNotFoundError("Missing filelist"),
        PermissionError("Permission denied"),
        ValueError("Invalid OCR language"),
        RuntimeError("Unexpected Tesseract failure"),
        OSError(errno.EINTR, "Interrupted system call"),
    ],
)
def test_non_retryable_errors(error):
    assert is_retryable_error(error) is False


@pytest.mark.parametrize(
    "error",
    [
        OSError(errno.EAGAIN, "Resource temporarily unavailable"),
        OSError(errno.ETIMEDOUT, "Operation timed out"),
    ],
)
def test_transient_errors_are_retryable(error):
    assert is_retryable_error(error) is True


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

    result = run_tesseract_job.delay("filelist.txt", ["eng", "spa"])

    assert result == "queued"
    apply_async.assert_called_once_with(
        ("filelist.txt", ["eng", "spa"]),
        {},
    )


def test_shared_task_delay_with_correlation_id(monkeypatch):
    """Verify that correlation_id is forwarded to Celery."""
    apply_async = Mock(return_value="queued")
    monkeypatch.setattr(run_tesseract_job, "apply_async", apply_async)

    result = run_tesseract_job.delay(
        "filelist.txt",
        ["eng", "spa"],
        correlation_id="mokelumne-test-123",
    )

    assert result == "queued"
    apply_async.assert_called_once_with(
        ("filelist.txt", ["eng", "spa"]),
        {"correlation_id": "mokelumne-test-123"},
    )


def test_run_tesseract_job_raises_error_for_empty_filelist(tmp_path):
    """Verify that the task rejects an empty file list."""
    filelist = tmp_path / "empty.txt"
    filelist.touch()

    with pytest.raises(ValueError, match="is empty"):
        run_tesseract_job.run(str(filelist), ["eng"])


def test_run_tesseract_job_raises_error_for_missing_filelist(tmp_path):
    """Verify that the task rejects a missing file list."""
    filelist = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError, match="does not exist"):
        run_tesseract_job.run(str(filelist), ["eng"])


@pytest.mark.parametrize(
    ("retry_count", "expected_delay"),
    [
        (0, 30),
        (1, 60),
        (2, 120),
    ],
)
def test_run_tesseract_job_retries_transient_errors(
    monkeypatch, tmp_path, retry_count, expected_delay
):
    """Verify transient errors trigger retries with exponential backoff."""
    filelist = tmp_path / "files.txt"
    filelist.write_text("image1.tif\n", encoding="utf-8")

    error = OSError(errno.EAGAIN, "Resource temporarily unavailable")

    monkeypatch.setattr(
        "quiabo.tasks.run_tesseract",
        Mock(side_effect=error),
    )

    retry = Mock(side_effect=RuntimeError("Retry requested"))
    monkeypatch.setattr(run_tesseract_job, "retry", retry)

    run_tesseract_job.push_request(retries=retry_count)
    try:
        with app.app_context():
            with pytest.raises(RuntimeError, match="Retry requested"):
                run_tesseract_job.run(str(filelist), ["eng"])
    finally:
        run_tesseract_job.pop_request()

    retry.assert_called_once_with(
        exc=error,
        countdown=expected_delay,
        max_retries=3,
    )


def test_run_tesseract_job_stops_after_max_retries(monkeypatch, tmp_path, caplog):
    """Verify exhausted retries result in a final failure."""
    caplog.set_level("INFO", logger="quiabo.tasks")

    filelist = tmp_path / "files.txt"
    filelist.write_text("image1.tif\n", encoding="utf-8")

    error = OSError(errno.EAGAIN, "Resource temporarily unavailable")
    monkeypatch.setattr(
        "quiabo.tasks.run_tesseract",
        Mock(side_effect=error),
    )

    run_tesseract_job.push_request(retries=3)
    try:
        with app.app_context():
            with pytest.raises(OSError) as exc_info:
                run_tesseract_job.run(str(filelist), ["eng"])
    finally:
        run_tesseract_job.pop_request()

    assert exc_info.value is error

    completion_records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "ocr_job_finished"
    ]

    assert len(completion_records) == 1
    assert completion_records[0].status == "failure"
    assert completion_records[0].error_type == "BlockingIOError"

    assert any(
        record.levelname == "ERROR"
        and "Resource temporarily unavailable" in record.getMessage()
        for record in caplog.records
    )


def test_run_tesseract_job_uses_configured_retry_settings(monkeypatch, tmp_path):
    """Verify retry settings can be overridden through Flask configuration."""
    filelist = tmp_path / "files.txt"
    filelist.write_text("image1.tif\n", encoding="utf-8")

    error = OSError(errno.EAGAIN, "Resource temporarily unavailable")
    monkeypatch.setattr(
        "quiabo.tasks.run_tesseract",
        Mock(side_effect=error),
    )

    retry = Mock(side_effect=RuntimeError("Retry requested"))
    monkeypatch.setattr(run_tesseract_job, "retry", retry)

    # Override the defaults for this test.
    monkeypatch.setitem(app.config, "OCR_MAX_RETRIES", 5)
    monkeypatch.setitem(app.config, "OCR_RETRY_BACKOFF", 10)

    run_tesseract_job.push_request(retries=2)
    try:
        with app.app_context():
            with pytest.raises(RuntimeError, match="Retry requested"):
                run_tesseract_job.run(str(filelist), ["eng"])
    finally:
        run_tesseract_job.pop_request()

    retry.assert_called_once_with(
        exc=error,
        countdown=40,
        max_retries=5,
    )


def test_run_tesseract_job_updates_state_and_returns_digest(monkeypatch, tmp_path, caplog):
    """Verify that the task runs Tesseract and returns the PDF digest."""
    caplog.set_level("INFO", logger="quiabo.tasks")

    images_dir = tmp_path / "999mmsid_like_name"
    images_dir.mkdir()
    filelist = images_dir / "files.txt"
    filelist.write_text("image1.tif\nimage2.tif\n", encoding="utf-8")
    output = images_dir / "999mmsid_like_name"
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
        correlation_id="mokelumne-test-123",
    )

    update_state.assert_called_once_with(
        state="STARTED",
        meta={
            "filelist": str(filelist),
            "languages": ["eng", "spa"],
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
    completion_records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "ocr_job_finished"
    ]

    assert len(completion_records) == 1

    record = completion_records[0]

    assert record.levelname == "INFO"
    assert record.correlation_id == "mokelumne-test-123"
    assert record.status == "success"
    assert record.image_count == 2
    assert record.languages == ["eng", "spa"]
    assert record.duration_seconds >= 0
    assert record.tesseract_seconds >= 0
    assert record.queue_wait_seconds is None
    assert record.worker_hostname
    assert record.error_type is None


def test_run_tesseract_job_wraps_tesseract_errors(monkeypatch, tmp_path):
    """Verify that Tesseract errors are wrapped with task context."""
    filelist = tmp_path / "files.txt"
    filelist.write_text("image1.tif\nimage2.tif\n", encoding="utf-8")
    error = RuntimeError("Tesseract failed")
    run = Mock(side_effect=error)
    monkeypatch.setattr("quiabo.tasks.run_tesseract", run)

    with pytest.raises(
        RuntimeError, match="Error running Tesseract: Tesseract failed"
    ) as exc_info:
        run_tesseract_job.run(str(filelist), ["eng"])

    assert exc_info.value.__cause__ is error


def test_run_tesseract_job_fails_when_no_pdf_written(monkeypatch, tmp_path, caplog):
    """Verify that the task fails when Tesseract writes no PDF."""
    caplog.set_level("INFO", logger="quiabo.tasks")

    filelist = tmp_path / "files.txt"
    filelist.write_text("image1.tif\nimage2.tif\n", encoding="utf-8")
    monkeypatch.setattr("quiabo.tasks.run_tesseract", Mock())

    with pytest.raises(
        RuntimeError,
        match="Tesseract did not create expected PDF",
    ) as exc_info:
        run_tesseract_job.run(str(filelist), ["eng"])

    completion_records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "ocr_job_finished"
    ]

    assert len(completion_records) == 1
    record = completion_records[0]

    assert isinstance(exc_info.value.__cause__, FileNotFoundError)
    assert record.status == "failure"
    assert record.error_type == "FileNotFoundError"
    assert record.tesseract_seconds is not None
    assert record.image_count == 2


def test_run_tesseract_job_fails_when_language_unavailable(monkeypatch, tmp_path):
    """Verify that the task fails when Tesseract cannot load a language."""
    filelist = tmp_path / "files.txt"
    filelist.write_text("image1.tif\nimage2.tif\n", encoding="utf-8")
    error = TesseractError(1, "Failed loading language 'swe'")
    run = Mock(side_effect=error)

    monkeypatch.setattr("quiabo.tasks.run_tesseract", run)

    with pytest.raises(RuntimeError, match="Failed loading language 'swe'"):
        run_tesseract_job.run(str(filelist), ["swe"])


def test_run_tesseract_job_logs_correlation_id(monkeypatch, tmp_path, caplog):
    """Verify that OCR job logs include the correlation ID."""
    filelist = tmp_path / "files.txt"
    filelist.write_text("image1.tif\n", encoding="utf-8")

    monkeypatch.setattr(
        "quiabo.tasks.run_tesseract",
        Mock(side_effect=RuntimeError("Tesseract failed")),
    )

    with pytest.raises(RuntimeError, match="Error running Tesseract"):
        run_tesseract_job.run(
            str(filelist),
            ["eng"],
            correlation_id="mokelumne-test-123",
        )

    assert any(
        record.correlation_id == "mokelumne-test-123"
        for record in caplog.records
    )


def test_run_tesseract_job_records_queue_wait(monkeypatch, tmp_path, caplog):
    """Verify queue wait is calculated from the submission timestamp."""
    caplog.set_level("INFO", logger="quiabo.tasks")

    filelist = tmp_path / "files.txt"
    filelist.write_text("image1.tif\n", encoding="utf-8")

    def write_output(**kwargs):
        Path(f"{kwargs['output_filename_base']}.pdf").write_bytes(b"PDF")

    monkeypatch.setattr("quiabo.tasks.run_tesseract", write_output)

    submitted_at = (
        datetime.now(timezone.utc) - timedelta(seconds=10)
    ).isoformat()

    run_tesseract_job.push_request(
        headers={"submitted_at": submitted_at}
    )
    try:
        run_tesseract_job.run(str(filelist), ["eng"])
    finally:
        run_tesseract_job.pop_request()

    completion_records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "ocr_job_finished"
    ]

    assert len(completion_records) == 1

    record = completion_records[0]

    assert record.status == "success"
    assert record.queue_wait_seconds == pytest.approx(10, abs=1)


@pytest.mark.parametrize(
    "submitted_at",
    [
        "not-a-timestamp",
        "2026-11-16T12:00:00",
    ],
)
def test_run_tesseract_job_ignores_invalid_submission_timestamp(
    monkeypatch, tmp_path, caplog, submitted_at
):
    """Verify invalid timing metadata does not prevent OCR."""
    caplog.set_level("INFO", logger="quiabo.tasks")

    filelist = tmp_path / "files.txt"
    filelist.write_text("image1.tif\n", encoding="utf-8")

    def write_output(**kwargs):
        Path(f"{kwargs['output_filename_base']}.pdf").write_bytes(b"PDF")

    monkeypatch.setattr("quiabo.tasks.run_tesseract", write_output)

    run_tesseract_job.push_request(
        headers={"submitted_at": submitted_at}
    )
    try:
        result = run_tesseract_job.run(str(filelist), ["eng"])
    finally:
        run_tesseract_job.pop_request()

    assert Path(result["output_path"]).is_file()

    completion_records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "ocr_job_finished"
    ]

    assert len(completion_records) == 1
    assert completion_records[0].status == "success"
    assert completion_records[0].queue_wait_seconds is None
    assert "Invalid Celery submission timestamp" in caplog.text
