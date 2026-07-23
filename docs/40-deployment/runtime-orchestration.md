# Runtime Orchestration

## Why This Doc Exists

Startup and background execution span application bootstrap, scheduler setup, extension lifecycle, source collection, and embedding maintenance. These interactions are easy to misunderstand from one file at a time.

## Cross-Unit Truths

### 1. Application bootstrap has an explicit order

Current bootstrap flow in `run.py`:

1. expose process-only liveness and report readiness as false
2. wait asynchronously until the database is reachable at the artifact's Alembic head
3. register the current client
4. persist registered storage types and set up built-in storage instances
5. sync the fixed extension profile unless `SKIP_EXTENSIONS_SYNC=1`
6. start enabled extensions, which registers source and resolver classes in memory
7. persist registered source types and set up source collection schedules
8. start the scheduler and register periodic jobs
9. report readiness as true

Database waiting is retryable and does not block `/livez`. A failure after the database
preflight moves runtime state to `failed`; it is observable through `/readyz` and is not
silently retried because extension startup can have partial effects.

### 2. There are two background collection mechanisms today

- source instances with `collect_at` are scheduled directly by `SourceManager.set_up_collect_jobs()`
- persisted pending collect jobs are picked up by `SourceCollectJobManager.check()`

This is a hybrid runtime model. Any future simplification must be deliberate because it changes cross-unit behavior.

### 3. Pending work is drained by periodic checks

- source collect job checks run every 30 seconds
- missing embedding checks run every 60 seconds

These are runtime guarantees, not route-layer behavior.

### 4. Shutdown must close long-lived runtime resources

- the APScheduler instance is shut down in application lifespan shutdown
- running extensions are closed asynchronously so they can persist config and release resources

### 5. OpenAPI generation intentionally skips extension sync

- CI sets `SKIP_EXTENSIONS_SYNC=1` when generating `docs/openapi.json`
- This prevents extension startup side effects from being required for schema generation

Application module import constructs routes and in-memory registries only. Database
registration and extension synchronization begin inside lifespan startup, never during
module import.

### 6. Health probes have separate semantics

- `/livez` and compatibility alias `/heartbeat` only prove that the web process can answer
- `/readyz` is read-only and requires both the exact Alembic head and completed runtime
  bootstrap
- health routes do not require JWT credentials and never include connection errors or
  database URLs in their payloads

### 7. Scheduler ownership is intentionally single-replica

The web process still owns APScheduler. Until scheduler work moves to a dedicated process,
deployments must keep web formation at one replica to avoid duplicate periodic work.

## Authoritative Code Anchors

- `run.py`
- `app/health.py`
- `app/runtime.py`
- `app/scheduler.py`
- `app/business/source/main.py`
- `app/business/source/collect_job.py`
- `app/business/sink/embedding.py`
- `.github/workflows/openapi-doc.yml`

## What Does Not Belong Here

- specific cron choices for one source
- one-off debugging notes
- backlog items about future scheduler redesign
