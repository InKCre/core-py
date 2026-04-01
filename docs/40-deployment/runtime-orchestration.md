# Runtime Orchestration

## Why This Doc Exists

Startup and background execution span application bootstrap, scheduler setup, extension lifecycle, source collection, and embedding maintenance. These interactions are easy to misunderstand from one file at a time.

## Cross-Unit Truths

### 1. Application bootstrap has an explicit order

Current startup flow in `run.py`:

1. register the current client
2. set up built-in storages
3. start the scheduler
4. register periodic jobs
5. sync extensions unless `SKIP_EXTENSIONS_SYNC=1`
6. start enabled extensions
7. set up source collection schedules

Preserve this ordering unless there is a deliberate design change.

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

## Authoritative Code Anchors

- `run.py`
- `app/scheduler.py`
- `app/business/source/main.py`
- `app/business/source/collect_job.py`
- `app/business/sink/embedding.py`
- `.github/workflows/openapi-doc.yml`

## What Does Not Belong Here

- specific cron choices for one source
- one-off debugging notes
- backlog items about future scheduler redesign
