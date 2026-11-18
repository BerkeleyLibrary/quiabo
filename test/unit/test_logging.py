"""Tests for Quiabo's JSON log formatter."""

import json
import logging

from quiabo.logging import JsonFormatter


def test_json_formatter():
    """Verify that log records include structured job identifiers."""
    formatter = JsonFormatter()

    record = logging.LogRecord(
        name="quiabo.tasks",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="Tesseract failed",
        args=(),
        exc_info=None,
    )

    record.job_id = "quiabo-job-123"
    record.correlation_id = "mokelumne-test-456"

    result = json.loads(formatter.format(record))

    assert result == {
        "level": "error",
        "job_id": "quiabo-job-123",
        "correlation_id": "mokelumne-test-456",
        "msg": "Tesseract failed",
    }


def test_json_formatter_without_job_identifiers():
    """Verify that ordinary log records work without job identifiers."""
    formatter = JsonFormatter()

    record = logging.LogRecord(
        name="quiabo",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Application started",
        args=(),
        exc_info=None,
    )

    result = json.loads(formatter.format(record))

    assert result == {
        "level": "info",
        "job_id": None,
        "correlation_id": None,
        "msg": "Application started",
    }

def test_formatter_includes_performance_fields():
    """Include performance fields when provided."""
    import json
    import logging

    from quiabo.logging import JsonFormatter

    record = logging.makeLogRecord(
        {
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": "OCR job completed",
            "job_id": "abc123",
            "correlation_id": "run456",
            "event": "ocr_job_finished",
            "status": "success",
            "duration_seconds": 125.4,
            "tesseract_seconds": 123.8,
            "image_count": 42,
            "languages": ["eng", "spa"],
        }
    )

    result = json.loads(JsonFormatter().format(record))

    assert result["event"] == "ocr_job_finished"
    assert result["status"] == "success"
    assert result["duration_seconds"] == 125.4
    assert result["tesseract_seconds"] == 123.8
    assert result["image_count"] == 42
    assert result["languages"] == ["eng", "spa"]

def test_formatter_omits_missing_performance_fields():
    """Do not add performance fields to ordinary log messages."""
    import json
    import logging

    from quiabo.logging import JsonFormatter

    record = logging.makeLogRecord(
        {
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": "Worker started",
        }
    )

    result = json.loads(JsonFormatter().format(record))

    assert result["msg"] == "Worker started"
    assert "duration_seconds" not in result
    assert "event" not in result
