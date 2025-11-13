# Cloudflare Workers Deployment Checklist

Use this checklist to ensure you've completed all necessary steps for deploying InKCre Core to Cloudflare Workers.

## Pre-Deployment Setup

- [ ] Sign up for a Cloudflare account at [cloudflare.com](https://cloudflare.com)
- [ ] Install Node.js and npm (required for Wrangler CLI)
- [ ] Install Wrangler CLI: `npm install -g wrangler`
- [ ] Authenticate Wrangler: `wrangler login`
- [ ] Have PostgreSQL database accessible from internet

## Database Configuration

- [ ] Create Hyperdrive configuration:
  ```bash
  wrangler hyperdrive create inkcre-db \
    --connection-string="postgresql://user:password@host:5432/dbname"
  ```
- [ ] Note the Hyperdrive ID from output
- [ ] Run database migrations from local environment:
  ```bash
  pdm run alembic upgrade head
  ```

## Project Configuration

- [ ] Copy `requirements-worker.txt` to `requirements.txt` (or update for Workers compatibility)
- [ ] Edit `wrangler.toml` and update Hyperdrive binding with your ID
- [ ] Verify `wrangler.toml` settings (name, main, compatibility_date)

## Environment Variables

- [ ] Set database connection string:
  ```bash
  wrangler secret put DB_CONN_STRING
  # Enter: postgresql://user:password@<HYPERDRIVE_ID>.hyperdrive.local:5432/dbname
  ```
- [ ] Set Worker environment flag:
  ```bash
  wrangler secret put CF_WORKER
  # Enter: true
  ```
- [ ] Set OpenAI API key (if using AI features):
  ```bash
  wrangler secret put OPENAI_API_KEY
  # Enter: sk-...
  ```
- [ ] Set any other required secrets (Tencent Cloud, etc.)

## Deployment

- [ ] Test locally if possible
- [ ] Deploy to Cloudflare Workers:
  ```bash
  wrangler deploy
  ```
- [ ] Note the deployed URL (e.g., `https://inkcre-core.your-subdomain.workers.dev`)

## Post-Deployment Verification

- [ ] Test health check endpoint:
  ```bash
  curl https://your-worker.workers.dev/heartbeat
  # Should return: {"status": "ok", "worker": true}
  ```
- [ ] Test database connectivity (try a simple read operation)
- [ ] Verify API endpoints are working
- [ ] Check logs in Cloudflare dashboard for any errors

## Scheduled Tasks Setup

- [ ] Go to Cloudflare dashboard → Workers → Your Worker
- [ ] Navigate to Triggers → Cron Triggers
- [ ] Add cron schedules for your collection endpoints:
  - Example: `0 * * * *` (every hour)
  - Target: `https://your-worker.workers.dev/source/{source_id}/collect`
- [ ] Verify cron triggers are executing correctly

## Optional Enhancements

- [ ] Set up custom domain for your Worker
- [ ] Configure KV namespace for caching (if needed)
- [ ] Set up R2 bucket for file storage (if needed)
- [ ] Enable Workers AI for ML features (if needed)
- [ ] Set up monitoring and alerts
- [ ] Configure rate limiting

## Troubleshooting

If you encounter issues:

1. **Check logs**: `wrangler tail` for real-time logs
2. **Verify environment variables**: Ensure all secrets are set correctly
3. **Test Hyperdrive**: Verify database connectivity
4. **Check compatibility**: Review dependencies for Workers compatibility
5. **Review documentation**: See CLOUDFLARE_DEPLOYMENT.md for detailed guidance

## Rollback Plan

If deployment fails:

- [ ] Keep your traditional deployment running as backup
- [ ] Document any errors from Workers dashboard
- [ ] Revert to previous version: `wrangler rollback`
- [ ] Review IMPLEMENTATION_NOTES.md for compatibility issues

## Success Criteria

Deployment is successful when:

- ✅ Health check returns `{"status": "ok", "worker": true}`
- ✅ Database operations work correctly
- ✅ All API endpoints respond as expected
- ✅ Cron triggers execute scheduled tasks
- ✅ No errors in Workers dashboard logs
- ✅ Performance meets expectations (cold start time, response time)

## Next Steps

After successful deployment:

1. Monitor performance and adjust as needed
2. Set up CI/CD for automated deployments
3. Configure production environment variables
4. Set up proper domain and SSL
5. Implement monitoring and alerting
6. Document any custom configurations
