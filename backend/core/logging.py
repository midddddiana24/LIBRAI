from __future__ import annotations
import json, logging, sys


class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {"level": record.levelname, "logger": record.name, "message": record.getMessage()}
        if record.exc_info: data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout); handler.setFormatter(JsonFormatter())
    root = logging.getLogger(); root.handlers = [handler]; root.setLevel(logging.INFO)
