import logging
from logging.config import dictConfig

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(log_level: str = "INFO") -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": DEFAULT_LOG_FORMAT,
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                }
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": log_level, "propagate": False},
                "uvicorn.error": {"handlers": ["default"], "level": log_level, "propagate": False},
                "uvicorn.access": {"handlers": ["default"], "level": log_level, "propagate": False},
                "alembic": {"handlers": ["default"], "level": log_level, "propagate": False},
            },
            "root": {"handlers": ["default"], "level": log_level},
        }
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
