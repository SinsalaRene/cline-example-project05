"""Structured JSON logging configuration."""
import logging
import sys
import json
import uuid
from datetime import datetime, timezone

from app.config import settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "unknown"),
        }
        
        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ("name", "msg", "args", "levelname", "levelno",
                           "pathname", "filename", "folder", "module",
                           "exc_info", "exc_text", "stack_info", "lineno",
                           "funcName", "created", "relativeCreated",
                           "threadName", "processName", "thread", "process",
                           "request_id"):
                if not key.startswith("_"):
                    log_entry[key] = value
        
        return json.dumps(log_entry)


def setup_logging():
    """Configure application-wide logging."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    # Request ID logger
    logging.getLogger("app.middleware.request_id").setLevel(logging.INFO)