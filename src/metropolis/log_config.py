# src/metropolis/logging_config.py

import logging
import logging.config
import os

# Get the service name from an environment variable, with a default.
# We will set this variable in our docker-compose.yml file.
SERVICE_NAME = os.environ.get("METROPOLIS_SERVICE_NAME", "metropolis_app")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(service_name)s",
        },
    },
    "handlers": {
        "json": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
      
        "": {
            "handlers": ["json"],
            "level": "INFO",
        },
        "uvicorn.access": {
            "handlers": ["json"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

def setup_logging():
    """Applies the logging configuration."""
    old_factory = logging.getLogRecordFactory()
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service_name = SERVICE_NAME
        return record
    
    logging.setLogRecordFactory(record_factory)
    logging.config.dictConfig(LOGGING_CONFIG)