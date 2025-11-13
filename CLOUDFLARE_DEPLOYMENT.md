# Deploying InKCre Core to Cloudflare Workers

This guide explains how to deploy the InKCre Core application to Cloudflare Workers.

## Prerequisites

1. **Cloudflare Account**: Sign up at [cloudflare.com](https://cloudflare.com)
2. **Wrangler CLI**: Install the Cloudflare Workers CLI
   ```bash
   npm install -g wrangler
   ```
3. **Hyperdrive Database**: Set up a Hyperdrive connection to your PostgreSQL database

## Setup Steps

### 1. Prepare Dependencies

Cloudflare Workers requires specific dependency configuration:

```bash
# Use the Workers-optimized requirements file
cp requirements-worker.txt requirements.txt

# Or manually ensure you're using psycopg instead of psycopg2-binary
# Edit requirements.txt and replace:
# psycopg2-binary>=2.9.10,<3.0.0
# with:
# psycopg>=3.1.0
```

### 2. Configure Hyperdrive

Create a Hyperdrive configuration for your PostgreSQL database:

```bash
wrangler hyperdrive create inkcre-db \
  --connection-string="postgresql://user:password@your-postgres-host:5432/dbname"
```

Note the Hyperdrive ID from the output. You'll need it for the connection string.

### 3. Update wrangler.toml

Edit `wrangler.toml` and uncomment the Hyperdrive binding section, adding your Hyperdrive ID:

```toml
[[hyperdrive]]
binding = "HYPERDRIVE"
id = "<your-hyperdrive-id-here>"
```

### 4. Set Environment Variables

Set the database connection string using the Hyperdrive local endpoint:

```bash
# Using wrangler secret for sensitive data
wrangler secret put DB_CONN_STRING
# Enter: postgresql://user:password@<HYPERDRIVE_ID>.hyperdrive.local:5432/dbname

# Set the Worker environment flag
wrangler secret put CF_WORKER
# Enter: true
```

You can also configure other environment variables as needed (OpenAI API keys, etc.).

### 5. Deploy to Cloudflare Workers

```bash
wrangler deploy
```

## Database Migrations

Run database migrations before deploying:

```bash
# In your local environment with direct database access
pdm run alembic upgrade head
```

Note: Alembic migrations should be run from your local environment or CI/CD pipeline, not from Workers.

## Scheduled Tasks

In traditional deployment, the application uses APScheduler for background tasks. In Cloudflare Workers, use **Cron Triggers** instead:

1. Go to your Worker in the Cloudflare dashboard
2. Navigate to **Triggers** → **Cron Triggers**
3. Add cron schedules to call your collection endpoints:
   ```
   # Example: Run every hour
   0 * * * *  →  https://your-worker.workers.dev/source/{source_id}/collect
   ```

## Compatibility Notes

### Supported Features
- ✅ FastAPI ASGI application
- ✅ Database operations via Hyperdrive
- ✅ API routes and endpoints
- ✅ CORS middleware
- ✅ Extension system

### Limitations
- ❌ APScheduler (use Cron Triggers instead)
- ❌ Long-running background tasks (Workers have execution time limits)
- ❌ File system access (use KV, R2, or other storage services)
- ⚠️  Some libraries with native C extensions may not work (test thoroughly)

### Library Compatibility

Some dependencies may need alternatives:

- **psycopg2-binary** → Consider using **psycopg** (pure Python) if there are issues
- **numpy** → May have limited functionality in Workers environment
- Check compatibility of AI/ML libraries (OpenAI, LiteLLM should work)

## Testing

Test your deployment:

```bash
# Health check
curl https://your-worker.workers.dev/heartbeat

# Should return: {"status": "ok", "worker": true}
```

## Monitoring

Monitor your Worker in the Cloudflare dashboard:
- View logs in real-time
- Check request analytics
- Monitor error rates and performance

## Local Development

For local development, continue using the standard approach:

```bash
# Set environment variable for local development
export CF_WORKER=false

# Run with uvicorn
pdm run uvicorn run:api_app --reload
```

## Troubleshooting

### Connection Issues
- Verify Hyperdrive configuration
- Check that `DB_CONN_STRING` uses the `.hyperdrive.local` endpoint
- Ensure database credentials are correct

### Deployment Errors
- Check `wrangler tail` for real-time logs
- Verify all dependencies are compatible with Workers
- Check Workers dashboard for error details

### Performance Issues
- Hyperdrive provides connection pooling - don't use SQLAlchemy pooling
- Monitor cold start times
- Consider caching strategies

## Resources

- [Cloudflare Workers Python Docs](https://developers.cloudflare.com/workers/languages/python/)
- [Hyperdrive Documentation](https://developers.cloudflare.com/hyperdrive/)
- [Workers Limits](https://developers.cloudflare.com/workers/platform/limits/)
- [Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/)
