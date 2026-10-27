"""Logging setup that redacts secret-looking tokens/keys from records."""
import logging
import re

_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|api[_-]?secret|access[_-]?token|token|secret)"
    r"([\"'=:\s]+)([^\s\"',}]+)")


class RedactFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = _SECRET_RE.sub(r"\1\2<redacted>", record.msg)
        return True


def setup_logging(level=logging.INFO):
    f = RedactFilter()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"))
    handler.addFilter(f)
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]
