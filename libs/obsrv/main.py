"""Main observability setup."""

import logging
import sys

__all__ = ["get_logger"]

LOGGER: logging.Logger


def setup_obsrv() -> logging.Logger:
    """Setup observability components."""
    from app.settings import settings

    # Create logger
    global LOGGER
    LOGGER = logging.getLogger("inkcre")
    LOGGER.setLevel(logging.DEBUG)

    # Clear any existing handlers
    LOGGER.handlers.clear()

    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    LOGGER.addHandler(console_handler)

    # Add backend-specific handlers
    backend = settings.obsrv.logging_backend
    if backend == "logtail":
        from .log_handler_logtail import LogtailHandler

        logtail_wrapper = LogtailHandler(
            source_token=settings.obsrv.logtail_source_token,
            host=settings.obsrv.logtail_host,
        )
        handler = logtail_wrapper.get_handler()
        if handler:
            LOGGER.addHandler(handler)
            LOGGER.info("Logtail logging enabled")
        else:
            LOGGER.warning("Logtail logging configured but not available")
    elif backend == "postgresql":
        from .log_handler_postgresql import PostgreSQLHandler

        pg_handler = PostgreSQLHandler(dsn=settings.database_url)
        LOGGER.addHandler(pg_handler)
        LOGGER.info("PostgreSQL logging enabled")
    else:
        LOGGER.warning(f"Unknown logging backend: {backend}")

    return LOGGER


def get_logger() -> logging.Logger:
    """Get the application logger instance.

    Returns:
        Logger instance for the application
    """
    global LOGGER
    return LOGGER
