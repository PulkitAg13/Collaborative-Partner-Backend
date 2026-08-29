"""Structured logging configuration."""

import logging
import sys


def setup_logging(debug: bool = False) -> None:
    """Configure root logger with a structured format.

    Args:
        debug: When True, set level to DEBUG; otherwise INFO.
    """
    level = logging.DEBUG if debug else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicate log lines when reloading
    if root_logger.handlers:
        root_logger.handlers.clear()

    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if debug else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger.

    Usage:
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)
