"""Tests for logging configuration and middleware."""

import logging
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.logging_config import get_logger, log_with_track_id, setup_logging


class TestLoggingConfiguration:
    """Test logging configuration setup."""
    
    def test_setup_logging_creates_logger(self):
        """Test that setup_logging creates a logger with the correct name."""
        logger = setup_logging()
        assert logger.name == "inkcre"
        assert logger.level == logging.INFO
    
    def test_setup_logging_has_console_handler(self):
        """Test that setup_logging adds a console handler."""
        logger = setup_logging()
        handlers = logger.handlers
        assert len(handlers) >= 1
        # At least one handler should be a StreamHandler
        assert any(isinstance(h, logging.StreamHandler) for h in handlers)
    
    def test_get_logger_returns_same_instance(self):
        """Test that get_logger returns the same logger instance."""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2
        assert logger1.name == "inkcre"
    
    def test_setup_logging_without_logtail_token(self):
        """Test that logging works without Logtail configuration."""
        # Save and clear env vars
        original_token = os.environ.get("LOGTAIL_SOURCE_TOKEN")
        original_host = os.environ.get("LOGTAIL_HOST")
        
        try:
            os.environ.pop("LOGTAIL_SOURCE_TOKEN", None)
            os.environ.pop("LOGTAIL_HOST", None)
            
            logger = setup_logging()
            
            # Should still have console handler
            assert len(logger.handlers) >= 1
            # Should not raise any errors
            logger.info("Test log message")
            
        finally:
            # Restore env vars
            if original_token is not None:
                os.environ["LOGTAIL_SOURCE_TOKEN"] = original_token
            if original_host is not None:
                os.environ["LOGTAIL_HOST"] = original_host
    
    @patch("app.logging_config.LOGTAIL_AVAILABLE", True)
    @patch("app.logging_config.LogtailHandler")
    def test_setup_logging_with_logtail_token(self, mock_logtail_handler):
        """Test that Logtail handler is added when token is provided."""
        # Save and set env vars
        original_token = os.environ.get("LOGTAIL_SOURCE_TOKEN")
        original_host = os.environ.get("LOGTAIL_HOST")
        
        try:
            test_token = "test_token_12345"
            test_host = "https://test.logtail.com"
            os.environ["LOGTAIL_SOURCE_TOKEN"] = test_token
            os.environ["LOGTAIL_HOST"] = test_host
            
            # Create a mock handler instance with proper level attribute
            mock_handler_instance = MagicMock()
            mock_handler_instance.level = logging.INFO
            mock_logtail_handler.return_value = mock_handler_instance
            
            logger = setup_logging()
            
            # Verify LogtailHandler was called with correct token
            mock_logtail_handler.assert_called_once_with(source_token=test_token)
            
            # Verify handler was added to logger
            assert mock_handler_instance in logger.handlers or len(logger.handlers) >= 2
            
        finally:
            # Restore env vars
            if original_token is not None:
                os.environ["LOGTAIL_SOURCE_TOKEN"] = original_token
            else:
                os.environ.pop("LOGTAIL_SOURCE_TOKEN", None)
            
            if original_host is not None:
                os.environ["LOGTAIL_HOST"] = original_host
            else:
                os.environ.pop("LOGTAIL_HOST", None)
    
    def test_log_with_track_id(self):
        """Test that log_with_track_id adds track_id to extra context."""
        logger = get_logger()
        
        # Create a custom handler to capture log records
        test_handler = logging.Handler()
        captured_records = []
        
        def capture_emit(record):
            captured_records.append(record)
        
        test_handler.emit = capture_emit
        logger.addHandler(test_handler)
        
        try:
            track_id = "test-track-id-123"
            log_with_track_id(
                logger,
                logging.INFO,
                "Test message",
                track_id=track_id,
                custom_field="custom_value"
            )
            
            # Check that record was captured
            assert len(captured_records) == 1
            record = captured_records[0]
            
            # Verify trackId is in the record
            assert hasattr(record, "trackId")
            assert record.trackId == track_id
            
            # Verify custom field is in the record
            assert hasattr(record, "custom_field")
            assert record.custom_field == "custom_value"
            
        finally:
            logger.removeHandler(test_handler)
    
    def test_log_with_track_id_without_track_id(self):
        """Test that log_with_track_id works without track_id."""
        logger = get_logger()
        
        # Should not raise any errors
        log_with_track_id(
            logger,
            logging.INFO,
            "Test message without track_id",
            custom_field="value"
        )


class TestLoggingMiddleware:
    """Test logging middleware for FastAPI."""
    
    def test_middleware_generates_track_id(self):
        """Test that middleware generates and adds track_id."""
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from app.middleware import LoggingMiddleware
        
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)
        
        @app.get("/test")
        def test_endpoint(request: Request):
            # Check that track_id is available in request state
            return {"track_id": getattr(request.state, "track_id", None)}
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "track_id" in data
        assert data["track_id"] is not None
        
        # Verify track_id in response headers
        assert "X-Track-ID" in response.headers
        assert response.headers["X-Track-ID"] == data["track_id"]
    
    def test_middleware_logs_request(self):
        """Test that middleware logs requests."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.middleware import LoggingMiddleware
        
        # Setup logger to capture logs
        logger = get_logger()
        test_handler = logging.Handler()
        test_handler.level = logging.INFO
        captured_records = []
        
        def capture_emit(record):
            captured_records.append(record)
        
        test_handler.emit = capture_emit
        logger.addHandler(test_handler)
        
        try:
            app = FastAPI()
            app.add_middleware(LoggingMiddleware)
            
            @app.get("/test")
            def test_endpoint():
                return {"status": "ok"}
            
            client = TestClient(app)
            response = client.get("/test")
            
            assert response.status_code == 200
            
            # Check that logs were captured
            assert len(captured_records) >= 2  # At least request start and complete
            
            # Find request start log
            start_logs = [r for r in captured_records if "Request started" in r.getMessage()]
            assert len(start_logs) >= 1
            
            # Find request complete log
            complete_logs = [r for r in captured_records if "Request completed" in r.getMessage()]
            assert len(complete_logs) >= 1
            
        finally:
            logger.removeHandler(test_handler)
    
    def test_middleware_logs_exceptions(self):
        """Test that middleware logs exceptions."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.middleware import LoggingMiddleware
        
        # Setup logger to capture logs
        logger = get_logger()
        test_handler = logging.Handler()
        test_handler.level = logging.INFO
        captured_records = []
        
        def capture_emit(record):
            captured_records.append(record)
        
        test_handler.emit = capture_emit
        logger.addHandler(test_handler)
        
        try:
            app = FastAPI()
            app.add_middleware(LoggingMiddleware)
            
            @app.get("/error")
            def error_endpoint():
                raise ValueError("Test error")
            
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/error")
            
            # Should return 500 error
            assert response.status_code == 500
            
            # Check that error was logged
            error_logs = [r for r in captured_records if r.levelno == logging.ERROR]
            assert len(error_logs) >= 1
            
            error_log = error_logs[0]
            assert "Request failed" in error_log.getMessage()
            assert hasattr(error_log, "error_type")
            assert error_log.error_type == "ValueError"
            
        finally:
            logger.removeHandler(test_handler)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
