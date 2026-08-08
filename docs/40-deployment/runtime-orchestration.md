# Runtime Orchestration

## Why This Doc Exists

Startup and background execution span application bootstrap, scheduler setup, extension lifecycle, source collection, and AI dialect registration. These interactions are easy to misunderstand from one file at a time.

## Cross-Unit Truths

### 1. Application bootstrap has an explicit order

Current bootstrap flow in `run.py`:

1. expose process-only liveness and report readiness as false
2. wait asynchronously until the complete runtime database contract is ready
3. register the current Peer identity and the built-in Peer HTTP outbound/business inbounds
4. persist registered storage types and set up built-in storage instances
5. sync the fixed extension profile unless `SKIP_EXTENSIONS_SYNC=1`
6. start enabled extensions, which registers source and resolver classes in memory
7. persist registered source types and set up source collection schedules
8. persist peer-local registered AI dialect contracts
9. publish the complete config-derived capability snapshot and renew the database-time Peer lease
10. start the scheduler and register Peer refresh、pending-collection plus default-Profile semantic-maintenance jobs
11. report readiness as true

Database waiting is retryable and does not block `/livez`. A failure after the database
preflight moves runtime state to `failed`; it is observable through `/readyz` and is not
silently retried because extension startup can have partial effects.

### 2. There are two background collection mechanisms today

- source instances with `collect_at` are scheduled directly by `SourceManager.set_up_collect_jobs()`
- persisted pending collect jobs are picked up by `SourceCollectJobManager.check()`

This is a hybrid runtime model. Any future simplification must be deliberate because it changes cross-unit behavior.

### 3. Pending work is drained by periodic checks

- source collect job checks run every 30 seconds
- Peer advertisement/lease refresh uses owner-supplied TTL and renewal interval settings；it republishes config-derived
  inbound URLs before renewing liveness
- semantic retrieval periodically calls the same bounded `SemanticRetrievalManager.maintain()` path for only the
  deployment-selected default Profile；without a default the job is a no-op

The interval、success bound、batch size and scan page size are peer-local runtime settings。Collection and Block writes do
not invoke embedding implicitly；all non-default Profiles require an explicit maintain/rebuild call。

Deployment tooling, not a second environment setting, owns the public HTTP URL projection. It writes
`config.http_public_base_url` on the exact registered Peer and waits until the running process republishes all three fixed
inbounds plus a live lease. Preview/production delivery uses `scripts/configure_peer_runtime.py`; local development uses the
same database-owned config semantics through its runtime owner.

### 4. Shutdown must close long-lived runtime resources

- the APScheduler instance is shut down in application lifespan shutdown
- running extensions are closed asynchronously so they can release resources
- a runtime that reached ready clears its Peer lease after scheduler/extension shutdown；abrupt loss relies on expiry

Active Agent Turns are ordinary caller-owned asyncio Tasks，not scheduler jobs or deployment work records。The MVP Thread
persistence backend is process-local memory，so process shutdown does not promise Thread resume。Cancelling an awaiting
caller propagates to unfinished Tool tasks；already completed external/graph effects are not rolled back or compensated。

### 5. OpenAPI generation is import-only

- `pdm run python scripts/generate-openapi.py` generates `docs/openapi.json` locally
- application lifespan does not run during schema generation, so extension synchronization
  and database-backed bootstrap are not required
- hosted API documentation is not currently published by this repository

Application module import constructs routes and in-memory registries only. Database
registration and extension synchronization begin inside lifespan startup, never during
module import.

### 6. Health probes have separate semantics

- `/livez` and compatibility alias `/heartbeat` only prove that the web process can answer
- `/readyz` is read-only and requires the complete role/ACL/catalog/migration contract plus
  completed runtime bootstrap
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
- `app/business/ai/main.py`
- `app/business/agent/main.py`
- `app/business/agent/thread.py`
- `app/business/semantic_retrieval/main.py`
- `app/business/peer/main.py`
- `app/business/peer/http.py`
- `scripts/generate-openapi.py`

## What Does Not Belong Here

- specific cron choices for one source
- one-off debugging notes
- backlog items about future scheduler redesign
