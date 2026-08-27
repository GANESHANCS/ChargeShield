import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from backend.core.config import settings

class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for production observability and auditability."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "environment": settings.ENVIRONMENT,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_fields"):
            log_obj["metadata"] = record.extra_fields
        return json.dumps(log_obj)

def setup_logging() -> logging.Logger:
    logger_inst = logging.getLogger("chargeshield")
    logger_inst.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    if not logger_inst.handlers:
        logger_inst.addHandler(handler)
        
    return logger_inst

logger = setup_logging()

def log_event(event_type: str, message: str, level: str = "INFO", extra: Optional[Dict[str, Any]] = None):
    """Logs a structured operational event without exposing sensitive credentials or PII."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    extra_fields = {"event_type": event_type}
    if extra:
        extra_fields.update(extra)
    logger.log(log_level, message, extra={"extra_fields": extra_fields})

def log_audit_event(dispute_id: str, reviewer_id: str, action: str, details: Optional[Dict[str, Any]] = None):
    """Logs an immutable human decision audit event."""
    extra = {
        "dispute_id": dispute_id,
        "reviewer_id": reviewer_id,
        "action": action
    }
    if details:
        extra.update(details)
    log_event(event_type="HUMAN_REVIEW_DECISION", message=f"Decision '{action}' authorized for {dispute_id} by {reviewer_id}", level="INFO", extra=extra)

def log_error_event(component: str, error_message: str, exc: Optional[Exception] = None):
    """Logs a system or database error event with context."""
    extra = {"component": component}
    if exc:
        extra["exception_type"] = type(exc).__name__
    logger.error(f"[{component}] {error_message}", exc_info=exc, extra={"extra_fields": extra})
