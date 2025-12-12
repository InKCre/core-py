"""Middleware for logging and request tracking."""

import logging
import time
import uuid
import jwt
from typing import Callable

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.settings import settings
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


class JWTMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.jwt_secret = settings.jwt_secret
        if not self.jwt_secret:
            raise ValueError("JWT_SECRET environment variable is not set")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate JWT token from Authorization header.

        Args:
            request: The incoming request
            call_next: Next middleware/handler in chain

        Returns:
            Response from the handler
        """
        # Skip JWT validation for heartbeat endpoint
        if (
            request.url.path == "/heartbeat"
            or request.url.path == "/docs"
            or request.url.path.startswith("/openapi.json")
        ):
            return await call_next(request)

        # Get Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header missing")

        # Check Bearer token format
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401, detail="Invalid authorization header format"
            )

        token = auth_header[7:]  # Remove "Bearer "

        try:
            # Decode JWT
            jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                audience=("inkcre-client-web", "inkcre-client-webext"),
            )
        except jwt.exceptions.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.exceptions.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=e)

        # Proceed to next middleware/handler
        return await call_next(request)
