"""Configuration du logging applicatif."""

from __future__ import annotations

import logging
import logging.config

from app.core.config import Settings

_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s %(message)s"


def configure_logging(settings: Settings) -> None:
    """Configure le logging de manière centralisée et idempotente."""
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": _LOG_FORMAT, "datefmt": "%Y-%m-%dT%H:%M:%S%z"},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {"handlers": ["console"], "level": settings.log_level.upper()},
            "loggers": {
                "uvicorn": {"level": settings.log_level.upper(), "propagate": True},
                "uvicorn.error": {"level": settings.log_level.upper(), "propagate": True},
                "uvicorn.access": {"level": "WARNING", "propagate": True},
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger nommé."""
    return logging.getLogger(name)
