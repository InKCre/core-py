"""Logging configuration for InKCre using Better Stack (Logtail)."""

import logging
import os
import sys
from typing import Optional

# Try to import logtail, but make it optional
try:
    from logtail import LogtailHandler
    LOGTAIL_AVAILABLE = True
except ImportError:
    LOGTAIL_AVAILABLE = False
    LogtailHandler = None


def setup_logging() -> logging.Logger:
    """Setup logging with Better Stack (Logtail) integration.
    
    Configures logging to send logs to Better Stack when LOGTAIL_SOURCE_TOKEN
    and LOGTAIL_HOST environment variables are set. Falls back to console
    logging if not configured.
    
    Returns:
        Logger instance configured for the application
    """
    # Create logger
    logger = logging.getLogger("inkcre")
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Better Stack handler (optional, based on env vars)
    source_token = os.getenv("LOGTAIL_SOURCE_TOKEN")
    logtail_host = os.getenv("LOGTAIL_HOST")
    
    if LOGTAIL_AVAILABLE and source_token:
        try:
            # Create Logtail handler
            logtail_handler = LogtailHandler(source_token=source_token)
            if logtail_host:
                # If host is provided, configure it
                logtail_handler.host = logtail_host
            logtail_handler.setLevel(logging.INFO)
            logger.addHandler(logtail_handler)
            logger.info("Better Stack logging enabled", extra={
                "logtail_host": logtail_host or "default"
            })
        except Exception as e:
            logger.warning(f"Failed to setup Better Stack logging: {e}")
    elif source_token and not LOGTAIL_AVAILABLE:
        logger.warning(
            "LOGTAIL_SOURCE_TOKEN is set but logtail-python is not installed"
        )
    
    return logger


def get_logger() -> logging.Logger:
    """Get the application logger instance.
    
    Returns:
        Logger instance for the application
    """
    return logging.getLogger("inkcre")


def log_with_track_id(
    logger: logging.Logger,
    level: int,
    message: str,
    track_id: Optional[str] = None,
    **kwargs
):
    """Log a message with track_id in extra context.
    
    Args:
        logger: Logger instance to use
        level: Log level (e.g., logging.INFO)
        message: Log message
        track_id: Optional track ID for request tracking
        **kwargs: Additional fields to include in log context
    """
    extra = kwargs.copy()
    if track_id:
        extra["trackId"] = track_id
    logger.log(level, message, extra=extra)
