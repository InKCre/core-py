# Logging Configuration

This document describes the logging setup for InKCre, including integration with Better Stack (formerly Logtail).

## Overview

The application uses Python's standard logging module with optional Better Stack integration for centralized log management. Logs are always written to console, and optionally sent to Better Stack when configured.

## Configuration

### Environment Variables

- `LOGTAIL_SOURCE_TOKEN`: Better Stack source token for log ingestion (optional)
- `LOGTAIL_HOST`: Better Stack host URL (optional, defaults to Better Stack's default host)

### Example Configuration

```bash
# .env file
LOGTAIL_SOURCE_TOKEN=your_token_here
LOGTAIL_HOST=https://in.logtail.com
```

If these environment variables are not set, the application will still work but logs will only be written to console.

## Features

### 1. Request Tracking

Every HTTP request is assigned a unique `trackId` that is:
- Available in `request.state.track_id` within route handlers
- Included in all logs related to that request
- Returned in the `X-Track-ID` response header

This makes it easy to trace all logs related to a specific request.

### 2. Structured Logging

Logs include structured metadata using the `extra` parameter:

```python
from app.logging_config import get_logger, log_with_track_id

logger = get_logger()

# Basic logging
logger.info("Block created", extra={"block_id": 123, "resolver": "webpage"})

# Logging with trackId
log_with_track_id(
    logger,
    logging.INFO,
    "Processing request",
    track_id=request.state.track_id,
    user_id=user.id,
    action="create_block"
)
```

### 3. Exception Logging

The middleware automatically logs unhandled exceptions with full context:
- Request method and path
- Track ID
- Error type and message
- Request duration

### 4. Logpoints in Business Logic

Key operations in the `block` and `relation` modules include logging:

**Block Operations:**
- `BlockManager.create()` - logs block creation with resolver and storage info
- `BlockManager.fetchsert()` - logs new block creation or existing block retrieval
- `BlockManager.edit_block()` - logs block edits and errors

**Relation Operations:**
- `RelationManager.create()` - logs relation creation
- `RelationManager.fetchsert()` - logs relation creation or retrieval

## Usage in Route Handlers

You can access the track ID in any route handler:

```python
from fastapi import Request
from app.logging_config import get_logger

logger = get_logger()

@app.get("/example")
def example_endpoint(request: Request):
    track_id = request.state.track_id
    
    logger.info(
        "Processing example request",
        extra={"trackId": track_id, "custom_field": "value"}
    )
    
    return {"status": "ok", "track_id": track_id}
```

## Log Levels

The application uses standard Python log levels:

- `DEBUG`: Detailed information for diagnosing problems (e.g., "Block already exists")
- `INFO`: General informational messages (e.g., "Block created successfully")
- `WARNING`: Warning messages (e.g., "Block not found for editing")
- `ERROR`: Error messages (automatically logged by middleware for exceptions)

## Viewing Logs

### Console Logs

Logs are always written to stdout in the format:
```
2025-10-30 09:42:17,007 - inkcre - INFO - Block created successfully
```

### Better Stack

If configured, logs are sent to Better Stack where you can:
- Search and filter logs by trackId, level, or custom fields
- Set up alerts for errors or specific patterns
- Analyze log patterns and trends
- Correlate logs across multiple requests

## Testing

The logging functionality includes comprehensive tests in `tests/test_logging.py`:

```bash
# Run logging tests
pytest tests/test_logging.py -v

# Run all tests
pytest tests/ -v
```

## Best Practices

1. **Use structured logging**: Always include relevant context in the `extra` parameter
2. **Include trackId**: When logging within a request context, include the trackId
3. **Choose appropriate log levels**: Use DEBUG for detailed diagnostics, INFO for normal operations, WARNING for potential issues, and ERROR for failures
4. **Avoid logging sensitive data**: Never log passwords, tokens, or personal information
5. **Keep messages concise**: Log messages should be clear and actionable

## Troubleshooting

### Logs not appearing in Better Stack

1. Verify `LOGTAIL_SOURCE_TOKEN` is set correctly
2. Check that `logtail-python` package is installed
3. Review console logs for any warnings about Better Stack setup
4. Verify network connectivity to Better Stack host

### Missing trackId in logs

1. Ensure the logging middleware is properly registered in `run.py`
2. Verify the middleware is added before CORS middleware
3. Check that you're using `log_with_track_id()` or including trackId in the `extra` dict

## References

- [Better Stack Python Logging Documentation](https://betterstack.com/docs/logs/python/)
- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [FastAPI Middleware Documentation](https://fastapi.tiangolo.com/tutorial/middleware/)
