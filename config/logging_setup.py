"""Logging setup shared by the backend, scripts and training.

Logs go both to the console and to `logs/platform.log` (rotated at 10 MB).
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def setup_logging(level: str, logs_dir: Path, filename: str = "platform.log") -> None:
    """Configure the root logger once. Calling it again does nothing."""
    root = logging.getLogger()
    if root.handlers:
        return
    logs_dir.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(LOG_FORMAT)

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    log_file = RotatingFileHandler(logs_dir / filename, maxBytes=10_000_000, backupCount=3, encoding="utf-8")
    log_file.setFormatter(formatter)

    root.setLevel(level)
    root.addHandler(console)
    root.addHandler(log_file)
