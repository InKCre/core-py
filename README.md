# InKCre-Core

Backend of InKCre - an information base to collect and organize information automatically.

## Features

- **Knowledge Graph Management**: Store and organize information using blocks and relations
- **Automatic Organization**: AI-powered information categorization and linking
- **Vector Search**: Semantic search using embeddings
- **Extensible Architecture**: Plugin system for custom integrations
- **Observability**: Comprehensive logging with Better Stack integration

## Logging & Observability

InKCre includes built-in logging with optional Better Stack (Logtail) integration:

- Request tracking with unique `trackId` for each request
- Structured logging with contextual metadata
- Automatic exception capture and reporting
- Console and cloud logging support

See [Logging Documentation](docs/logging.md) for configuration and usage details.

### Configuration

```bash
# Optional: Enable Better Stack logging
LOGTAIL_SOURCE_TOKEN=your_token_here
LOGTAIL_HOST=https://in.logtail.com
```

## Deployment

### Heroku Deployment

This project is ready to deploy to Heroku. See the [Heroku Deployment Guide](docs/heroku_deployment.md) for detailed instructions.

Quick deploy:

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)
