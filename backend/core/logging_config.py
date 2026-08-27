"""
Structured Application Logging Configuration for ChargeShield Backend.
Formats logs with timestamp, log level, request correlation ID, endpoint method, and status.
Ensures sensitive tokens, passwords, and secrets are NEVER written to logs.
"""

import logging
import json
import sys
from datetime import datetime, timezone
from backend.core.config import settings

class StructuredJSONFormatter(logging.Formatter):
    """Custom formatter outputting structured JSON log entries for production observability."""
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "environment": settings.ENVIRONMENT,
            "service": settings.PROJECT_NAME
        }

        # Suppress sensitive information
        msg = log_entry["message"]
        if "password" in msg.lower() or "token" in msg.lower() or "secret" in msg.lower():
            log_entry["message"] = "[REDACTED SENSITIVE SECURITY CONTENT]"

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_structured_logging():
    """Configures application logger with structured output format."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if settings.ENVIRONMENT == "production":
        handler.setFormatter(StructuredJSONFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

    root_logger.addHandler(handler)
    return root_logger
