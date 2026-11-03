"""JSON formatting for Quiabo log records."""

import json
import logging


class JsonFormatter(logging.Formatter):
    """Format log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Convert a log record to JSON."""
        return json.dumps(
            {
                "level": record.levelname.lower(),
                "job_id": getattr(record, "job_id", None),
                "correlation_id": getattr(record, "correlation_id", None),
                "msg": record.getMessage(),
            }
        )
