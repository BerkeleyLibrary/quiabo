"""JSON formatting for Quiabo log records."""

import json
import logging


PERFORMANCE_FIELDS = (
    "event",
    "status",
    "duration_seconds",
    "tesseract_seconds",
    "queue_wait_seconds",
    "image_count",
    "languages",
    "worker_hostname",
    "error_type",
)

class JsonFormatter(logging.Formatter):
    """Format log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Convert a log record to JSON."""
        data = {
            "level": record.levelname.lower(),
            "job_id": getattr(record, "job_id", None),
            "correlation_id": getattr(record, "correlation_id", None),
            "msg": record.getMessage(),
        }

        for field in PERFORMANCE_FIELDS:
            if hasattr(record, field):
                data[field] = getattr(record, field)

        return json.dumps(data)
