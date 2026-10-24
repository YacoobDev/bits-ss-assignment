import logging
import json
import sys
from contextvars import ContextVar

correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="N/A")

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": "notification-service",
            "correlation_id": correlation_id_ctx.get(),
            "message": record.getMessage(),
            "logger": record.name
        }
        return json.dumps(log_obj)

def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]
