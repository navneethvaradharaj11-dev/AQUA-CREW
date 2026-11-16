"""
Structured Logging Configuration
"""
import logging
import sys
from app.config import settings


"""
AQUA CREW — Production Structured Logging Configuration (Task 17)
Supports human-readable colorized text format for development
and standard structured JSON format for production ELK/CloudWatch/Datadog.
"""
import logging
import sys
import json
from datetime import datetime, timezone
from app.config import settings


class JSONFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects with ISO 8601 timestamps.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.threadName,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, default=str)


def setup_logging() -> logging.Logger:
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)

    if settings.LOG_FORMAT.lower() == "json":
        handler.setFormatter(JSONFormatter())
    else:
        log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))

    root_logger = logging.getLogger()
    # Replace existing handlers
    root_logger.handlers = [handler]
    root_logger.setLevel(level)

    logger = logging.getLogger("aqua_crew")
    logger.setLevel(level)
    return logger


logger = setup_logging()

