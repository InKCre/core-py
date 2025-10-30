"""Middleware for logging and request tracking."""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.logging_config import get_logger, log_with_track_id


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests, responses, and exceptions with track ID."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log with track ID.
        
        Args:
            request: The incoming request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from the handler
        """
        # Generate track ID for this request
        track_id = str(uuid.uuid4())
        
        # Store track_id in request state for access in route handlers
        request.state.track_id = track_id
        
        # Log request
        start_time = time.time()
        log_with_track_id(
            self.logger,
            logging.INFO,
            f"Request started: {request.method} {request.url.path}",
            track_id=track_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            log_with_track_id(
                self.logger,
                logging.INFO,
                f"Request completed: {request.method} {request.url.path}",
                track_id=track_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=int(duration * 1000),
            )
            
            # Add track ID to response headers
            response.headers["X-Track-ID"] = track_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log exception with full context
            log_with_track_id(
                self.logger,
                logging.ERROR,
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                track_id=track_id,
                method=request.method,
                path=request.url.path,
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=int(duration * 1000),
            )
            
            # Re-raise exception to be handled by FastAPI's exception handlers
            raise
