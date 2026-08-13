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
7. persist registered source types
8. persist the complete locally registered Job Handler catalog
9. persist peer-local registered AI dialect contracts
10. publish the complete config-derived capability snapshot and renew the database-time Peer lease
11. start the scheduler and register Peer refresh、Cron materialization and pending-Job checks
12. report readiness as true

Database waiting is retryable and does not block `/livez`. A failure after the database
preflight moves runtime state to `failed`; it is observable through `/readyz` and is not
silently retried because extension startup can have partial effects.

### 2. Cron and Job are the one durable background-work path

- `CronManager.check()` evaluates only the current database-time minute，serializes each Cron and materializes at most one
  typed Job for the matching occurrence；it does not catch up missed occurrences。
- `JobManager.check()` filters pending Jobs through the peer-local Handler registry and `can_handle()` before scheduling an
  atomic database claim。Only the winning Peer executes；each run closes once to finished、failed、timed-out or aborted。
- source ordinary collect/backfill、lexical maintain/rebuild、semantic maintain/rebuild and media interpretation are exact Job
  types。Their domain Managers do not acquire Cron semantics merely because a Handler calls them。

Job has no implicit retry。A source may persist checkpoints as useful progress，but Job does not require or interpret them。

### 3. Pending work is drained by periodic checks

- Cron occurrence and pending Job checks run every 30 seconds
- Peer advertisement/lease refresh uses owner-supplied TTL and renewal interval settings；it republishes config-derived
  inbound URLs before renewing liveness
- retrieval maintenance is scheduled only through persisted Cron + exact typed Job parameters。There is no separate
  peer-local semantic-maintenance timer or implicit default-Profile loop。Collection and Block writes do not update lexical
  or embedding records implicitly。

Deployment tooling, not a second environment setting, owns the public HTTP URL projection. It writes
`config.http_public_base_url` on the exact registered Peer and waits until the running process republishes all four fixed
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
- `app/business/source/job.py`
- `app/business/ai/main.py`
- `app/business/agent/main.py`
- `app/business/agent/thread.py`
- `app/business/semantic_retrieval/main.py`
- `app/business/lexical_retrieval/main.py`
- `app/business/job.py`
- `app/business/cron.py`
- `app/business/peer/main.py`
- `app/business/peer/http.py`
- `scripts/generate-openapi.py`

## What Does Not Belong Here

- specific cron choices for one source
- one-off debugging notes
- backlog items about future scheduler redesign
