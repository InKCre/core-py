"""Middleware for logging and request tracking."""

import logging
import time
import uuid
import jwt
from typing import Callable

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from libs.obsrv.log_record import TRACE_ID
from app.settings import settings
from libs.obsrv.main import get_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests, responses, and exceptions with trace ID."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log with trace ID.

        Args:
            request: The incoming request
            call_next: Next middleware/handler in chain

        Returns:
            Response from the handler
        """
        # Generate trace ID for this request
        trace_id = f"fastapi.request.${str(uuid.uuid4())}"

        # Store trace_id in request state and context variable
        request.state.trace_id = trace_id
        TRACE_ID.set(trace_id)

        # Log request
        start_time = time.time()
        self.logger.debug(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
            },
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            self.logger.debug(
                f"Request completed: {request.method} {request.url.path}",
                extra={
                    "status_code": response.status_code,
                    "duration_ms": int(duration * 1000),
                },
            )

            # Add trace ID to response headers
            response.headers["X-trace-ID"] = trace_id

            return response

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Log exception
            self.logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "error.type": type(e).__name__,
                    "error.message": str(e),
                    "duration_ms": int(duration * 1000),
                },
            )

            # Re-raise exception to be handled by FastAPI's exception handlers
            raise


class JWTMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # JWT secret is required in Settings, so it will always be set
        self.jwt_secret = settings.jwt_secret

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
