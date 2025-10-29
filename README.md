# InKCre-Core

Backend of InKCre - An information base to collect, organize information automatically and provide powerful ways to search it.

## Deployment Options

### Traditional Deployment
Run with uvicorn:
```bash
pdm run uvicorn run:api_app --reload
```

### Cloudflare Workers
InKCre Core can be deployed to Cloudflare Workers for serverless deployment with edge computing benefits.

See [CLOUDFLARE_DEPLOYMENT.md](CLOUDFLARE_DEPLOYMENT.md) for detailed deployment instructions.