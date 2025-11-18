# Logging Usage Examples

This document provides practical examples of how to use the logging features in InKCre.

## Basic Usage in Route Handlers

```python
from fastapi import Request, APIRouter
from app.logging_config import get_logger, log_with_track_id
import logging

router = APIRouter()
logger = get_logger()

@router.post("/example")
def create_example(request: Request, data: dict):
    # Get the trackId from the request
    track_id = request.state.track_id
    
    # Log with trackId and custom context
    log_with_track_id(
        logger,
        logging.INFO,
        "Creating example resource",
        track_id=track_id,
        data_size=len(data),
        user_action="create"
    )
    
    try:
        # Your business logic here
        result = process_data(data)
        
        log_with_track_id(
            logger,
            logging.INFO,
            "Example resource created successfully",
            track_id=track_id,
            result_id=result.id
        )
        
        return result
        
    except ValueError as e:
        log_with_track_id(
            logger,
            logging.ERROR,
            f"Failed to create example resource: {str(e)}",
            track_id=track_id,
            error_type="ValidationError"
        )
        raise
```

## Using Logger Directly

```python
from app.logging_config import get_logger

logger = get_logger()

# Simple info log
logger.info("Operation started")

# Log with structured data
logger.info(
    "Block created",
    extra={
        "block_id": 123,
        "resolver": "webpage",
        "storage": "local",
        "content_length": 1500
    }
)

# Debug logging for development
logger.debug(
    "Block already exists, skipping creation",
    extra={"block_id": 123, "operation": "fetchsert"}
)

# Warning for potential issues
logger.warning(
    "Block not found for editing",
    extra={"block_id": 999, "user_id": 42}
)
```

## In Business Logic Classes

```python
from app.logging_config import get_logger

logger = get_logger()

class MyManager:
    @classmethod
    def create_resource(cls, data: dict) -> Resource:
        logger.info(
            "Creating resource",
            extra={
                "resource_type": data.get("type"),
                "data_keys": list(data.keys())
            }
        )
        
        # Create resource
        resource = Resource(**data)
        
        logger.info(
            "Resource created successfully",
            extra={
                "resource_id": resource.id,
                "resource_type": resource.type
            }
        )
        
        return resource
```

## Example Log Output

### Console Output
```
2025-10-30 09:42:17,007 - inkcre - INFO - Request started: GET /blocks/recent
2025-10-30 09:42:17,015 - inkcre - INFO - Block created successfully
2025-10-30 09:42:17,023 - inkcre - INFO - Request completed: GET /blocks/recent
```

### Better Stack (Structured JSON)
```json
{
  "timestamp": "2025-10-30T09:42:17.007Z",
  "level": "INFO",
  "message": "Block created successfully",
  "trackId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "block_id": 123,
  "resolver": "webpage",
  "method": "GET",
  "path": "/blocks/recent",
  "status_code": 200,
  "duration_ms": 16
}
```

## Searching Logs in Better Stack

With structured logging, you can easily search and filter:

```
# Find all logs for a specific request
trackId:"a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# Find all block creation operations
message:"Block created successfully"

# Find errors for a specific block
block_id:123 AND level:ERROR

# Find slow requests (over 1 second)
duration_ms:>1000

# Find specific resolver operations
resolver:"webpage" AND operation:"create"
```

## Error Handling Example

```python
from fastapi import Request, HTTPException
from app.logging_config import get_logger, log_with_track_id
import logging

logger = get_logger()

@app.get("/blocks/{block_id}")
def get_block(block_id: int, request: Request):
    track_id = request.state.track_id
    
    log_with_track_id(
        logger,
        logging.INFO,
        "Fetching block",
        track_id=track_id,
        block_id=block_id
    )
    
    try:
        block = BlockManager.get(block_id)
        
        if block is None:
            log_with_track_id(
                logger,
                logging.WARNING,
                "Block not found",
                track_id=track_id,
                block_id=block_id
            )
            raise HTTPException(status_code=404, detail="Block not found")
        
        log_with_track_id(
            logger,
            logging.INFO,
            "Block retrieved successfully",
            track_id=track_id,
            block_id=block_id,
            resolver=block.resolver
        )
        
        return block
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
        
    except Exception as e:
        # Middleware will log this, but you can add extra context
        log_with_track_id(
            logger,
            logging.ERROR,
            f"Unexpected error fetching block: {str(e)}",
            track_id=track_id,
            block_id=block_id,
            error_type=type(e).__name__
        )
        raise
```

## Configuration Example

Create a `.env` file in your project root:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/inkcre

# Better Stack Logging (optional)
LOGTAIL_SOURCE_TOKEN=your_source_token_here
LOGTAIL_HOST=https://in.logtail.com

# Other config...
```

If `LOGTAIL_SOURCE_TOKEN` is not set, logs will only appear in console, which is fine for development.

## Tips

1. **Always include trackId in request handlers** - Makes it easy to trace all logs for a request
2. **Use structured data in `extra`** - Better for searching and analysis
3. **Log at appropriate levels** - DEBUG for development, INFO for normal flow, WARNING for issues, ERROR for failures
4. **Include business context** - IDs, types, operations help understand what's happening
5. **Don't log sensitive data** - Passwords, tokens, personal info should never be logged

## Running with Logging

```bash
# Development (console only)
python -m uvicorn run:api_app --reload

# Production with Better Stack
LOGTAIL_SOURCE_TOKEN=your_token python -m uvicorn run:api_app --host 0.0.0.0 --port 8000
```
