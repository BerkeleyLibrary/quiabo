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
