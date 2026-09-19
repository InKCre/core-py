# Runtime Orchestration

## Why This Doc Exists

Startup and background execution span application bootstrap, scheduler setup, extension lifecycle, source collection, and AI dialect registration. These interactions are easy to misunderstand from one file at a time.

## Runtime Truths

### 0. Prepared Core versions select normal production

Successful checked-main commits continue to produce immutable SHA/digest evidence and the mutable
`main` image candidate. Normal production delivery and `stable` promotion run only when the root
Core version changed in that protected-main commit. An Extension-only Release is therefore a Core
deployment no-op. The selected artifact remains identified by exact source SHA/digest; explicit
`workflow_dispatch` is the recovery lane for redeploying a current artifact.

### 1. Application bootstrap has an explicit order

Current bootstrap flow in `run.py`:

1. expose process-only liveness and report readiness as false
2. wait asynchronously until the complete runtime database contract is ready
3. register the current Peer identity and the built-in Peer HTTP outbound/business inbounds
4. persist registered storage types and set up built-in storage instances
5. cold-restore this Peer's exact enabled Extension Releases through Registry-native wheel
   acquisition and standard entry-point discovery unless `SKIP_EXTENSION_START=1`
6. start restored extensions, which registers process-monotonic Source/Resolver/Sink types and publishes reversible routes、
   Peer inbounds and public claims
7. persist registered source types
8. persist the complete locally registered Job Handler catalog
9. persist peer-local registered AI dialect contracts
10. persist registered Sink types and start this Peer's enabled Sink instances
11. publish the complete config-derived capability snapshot and renew the database-time Peer lease
12. start the scheduler and register Peer refresh、Cron materialization and pending-Job checks
13. report readiness as true

Source classes are the sole schema authority for Extension-contributed Source types。Database initialization does not seed
disabled Extension Source schemas；Extension startup publishes them before step 7 persists the complete runtime registry。

Database waiting is retryable and does not block `/livez`. A failure after the database
preflight moves runtime state to `failed`; it is observable through `/readyz` and is not
silently retried because extension startup can have partial effects.

### 2. Cron and Job are the one durable background-work path

- `CronManager.check()` evaluates only the current database-time minute，serializes each Cron and materializes at most one
  typed Job for the matching occurrence；it does not catch up missed occurrences。
- `JobManager.check()` selects pending Jobs with a registered Handler. `run()` restores parameters and checks `can_handle()`
  before an atomic database claim. Only the winning Peer executes; each run conditionally closes once to a terminal status.
- `abort_requested` is durable intent, not evidence of completion. A pending Job can close immediately; a running Job
  remains running until its execution task has exited and released its resources. Repeating abort preserves terminal state.
- source ordinary collect/backfill、lexical maintain/rebuild、semantic maintain/rebuild and media interpretation are exact Job
  types。Their domain Managers do not acquire Cron semantics merely because a Handler calls them。

Job has no implicit retry。A source may persist checkpoints as useful progress，but Job does not require or interpret them。

### 3. Pending work is drained by periodic checks

- Cron occurrence and pending Job checks run every 30 seconds
- the process checks abort intent for its active Job IDs every 2 seconds; the domain handler does not poll the Job table
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

- scheduler admission is paused first; tracked callbacks are cancelled and awaited, then JobManager stops admitting work and drains any remaining active tasks
- running Sink instances close before Extension teardown, so an external endpoint cannot observe disappearing
  Extension-delivered behavior while it is still published
- running extensions are closed asynchronously so they can release resources
- APScheduler shuts down after those resources close; its `wait=True` does not itself await async cleanup, so callbacks are tracked and drained before resource teardown
- a runtime that reached ready clears its Peer lease after scheduler/extension shutdown；abrupt loss relies on expiry
- PostgreSQL logging drains after business resources close; the shared async database pool is disposed last

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

Readiness 复用 `app/database_contract` 的同步 psycopg 检查，在 `asyncio.to_thread` 内创建、使用并关闭
独立连接，不使用业务 Session。它与 CLI 共用完整判断规则，是明确保留的隔离同步适配边界；
取消 HTTP 等待不会中断已经运行的 worker，但连接仍由该 worker 的 context manager 关闭。
业务数据库访问与日志写入均使用原生 async，不把这个例外推广到业务查询。

### 7. PostgreSQL logging has a bounded async lifecycle

同步 logging 调用只捕获 LogModel 和当时的 trace/span，再写入线程安全的有界队列。
`lifespan` 启动单个异步 writer，每批最多 100 条，在独立事务中写入，绝不加入业务事务。
队列最多保存 1024 条；满时丢弃 backend 记录并向 stderr 报告，控制台 handler 保持独立。
数据库写失败时丢弃该批并向 stderr 报告异常类型，不递归调用日志系统。

关闭时先停止接受新 backend 记录，最多等待五秒排空；超时取消写入并丢弃剩余记录，之后才释放
连接池。日志仍为 best-effort telemetry，不承诺进程崩溃后的交付。导入模块不启动 writer、不连接数据库。

### 8. Each Peer may own a scheduler

APScheduler belongs to each web process. Cron row serialization, occurrence identity and the conditional pending-Job
claim coordinate multiple Peers through PostgreSQL; a single-replica recommendation is not the concurrency mechanism.
An attempt is not reclaimed or retried when its Peer disappears. Expiry and the next independently scheduled occurrence
retain their existing meanings.

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
- `app/business/sink/main.py`
- `scripts/generate-openapi.py`

## What Does Not Belong Here

- specific cron choices for one source
- one-off debugging notes
- backlog items about future scheduler redesign
