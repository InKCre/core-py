# Execution 02 — Hermetic Tests And Portable Artifact

## MVT Core

- Objective & Hypothesis: make repository-wide test collection safe and green, then build
  one immutable OCI artifact that contains the application, checked-in extensions,
  migration revisions, and a small provider-neutral process/probe contract. The hypothesis
  is that removing import-time external effects and proving the exact image against a
  disposable PostgreSQL/pgvector database will create a trustworthy unit for later Heroku
  and Neon automation.
- Guardrails Touched: production behavior remains explicit; tests must not read a
  credential-bearing `.env` or contact external services; built-in extensions are fixed
  image content; runtime may not install/download code; release generation remains
  forbidden; production data and current Heroku/Neon resources remain untouched in this
  packet.
- Verification: collect and run the complete repository test suite in a sanitized
  environment; build the image from a clean Git context; inspect required paths in the
  image; migrate a disposable pgvector database; start the image with platform-style
  configuration; verify liveness, readiness, migration head, and shutdown; run the same
  contract in CI.

## Classification And Mode

- Input types:
  - Reality: extension tests currently fail during collection and may expose `.env` inputs.
  - Constraint: the existing Docker final stage omits required source and migration files,
    hard-codes its port, and does not represent the fixed built-in profile.
  - Artifact: hermetic test harness, OCI image, process/probe contract, and CI evidence.
- Active modes:
  - Diagnose for import-time failures and image contents.
  - Execute after each failure mechanism is evidenced.

## Impact Handshake

- Address and Object:
  - extension schemas/import topology and their tests;
  - application construction, runtime bootstrap, scheduler ownership, and health endpoints;
  - `Dockerfile`, `.dockerignore`, Compose, image commands, and CI;
  - root PDM dependency/command contract and deployment documentation.
- Current State:
  - full collection stops on stale mail schema usage, RSS import-time database behavior, and
    a Twitter circular import;
  - the full test command can read a developer `.env`;
  - the final image omits `libs/`, `extensions/`, and checked-in revision files;
  - the image command hard-codes port 8000;
  - application module import performs extension synchronization and can write to the
    database before the server is ready;
  - the web process owns the scheduler, so replica scaling can duplicate periodic work.
- Requested Operation:
  - isolate collection and unit tests from developer credentials and external systems;
  - repair stale and circular extension seams without changing product semantics;
  - make application construction import-safe and runtime bootstrap explicit;
  - produce and verify one complete OCI artifact with explicit `web` and `migrate`
    operations;
  - define scheduler ownership explicitly, without silently enabling multiple writers.
- Explicit Exclusions:
  - no production migration, dump, restore, stamp, baseline replacement, or catalog write;
  - no Heroku app/config/release mutation and no Neon branch/database mutation;
  - no preview lifecycle or production CD workflow in this packet;
  - no dynamic third-party extension installation in the release artifact;
  - no deployment to `main`.
- Invariants:
  - `migrations/versions/**` remains unchanged;
  - tests never reveal or depend on real `.env` values;
  - the release artifact contains only checked-in code plus locked dependencies;
  - liveness does not require the database; readiness must fail for unreachable or
    incompatible database state;
  - migration remains a separate, single-writer operation;
  - the existing production-data source is never used as a disposable test target.
- Likely Files:
  - `tests/`, extension modules, `run.py`, application settings/bootstrap modules;
  - `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `Procfile`, `pyproject.toml`;
  - `.github/workflows/ci.yml`, runtime docs, and this packet.
- Uncertainty:
  - no local Docker-compatible CLI has yet been confirmed;
  - current revisions contain provider-sensitive role/extension statements that may fail on
    a stock disposable PostgreSQL image;
  - scheduler extraction may require a separately bounded follow-up if it crosses business
    ownership contracts.

## Acceptance Criteria

1. `pdm run test` collects and runs from a sanitized environment without reading the
   repository `.env`, contacting external services, or printing secret-shaped values.
2. Mail, RSS, Telegram, and Twitter extension unit tests collect without application
   startup or database writes.
3. Application import and OpenAPI generation do not write to the database.
4. The release image contains `app/`, `libs/`, `utils/`, the fixed `extensions/` profile,
   Alembic configuration, and every integrity-recorded revision.
5. Image dependencies come from the root frozen lock; no extension-local PDM environment or
   runtime download is required.
6. The web command honors `$PORT`; migrate is an explicit separate command.
7. Liveness is process-only. Readiness checks database reachability and expected Alembic
   head without mutating schema.
8. CI builds the image and proves a fresh disposable database migration plus image
   import/start/probe smoke.
9. Local documentation and CI name any unclosed scheduler or provider constraints
   honestly.

## Verification Plan

```bash
pdm run doctor
pdm run test
pdm run check
pdm run pre-commit run --all-files
```

Container-capable CI additionally proves:

```text
build immutable image
inspect required files and commands
start disposable pgvector/PostgreSQL
run image migrate operation
assert Alembic current == repository head
start image web operation with a dynamic PORT
assert liveness succeeds
assert readiness succeeds only after migration
stop image cleanly
```

## Promotion And Follow-Up

- Stable local runtime mechanics belong in `docs/40-deployment/`.
- Any cross-unit extension/runtime contract pressure is captured here before a separate
  shared-doc workflow.
- After this packet is green and committed, open the provider-wiring packet for Heroku
  artifact delivery and Neon disposable environments.

## Shared-Truth Pressure

- The previous product-level extension distribution language may still imply runtime
  installation. The release contract now uses a fixed checked-in profile with root-locked
  dependencies and deliberately has no runtime downloader. Reconcile that shared contract
  in `inkcre/docs` through the separate Hub workflow; do not edit `docs/_shared` here.

## Execution Evidence

- `pdm run check`: green, including 83 repository tests.
- `pdm run pre-commit run --all-files`: green.
- `git diff --check`: green.
- Application import and OpenAPI construction run in a subprocess with dotenv disabled and
  an unreachable placeholder database.
- Docker and Compose source contracts are checked in; no compatible local container runtime
  is installed, so the GitHub Actions artifact job is the required build/migrate/probe
  execution proof.
- Initial artifact CI exposed that `data/ai/prompts/*.txt` existed locally under a broad
  `data/` ignore rule and therefore was absent from Git and the build context. The prompt
  sources are now explicitly tracked while runtime data remains ignored; the artifact job
  must rerun to complete container proof.
- The next artifact run built and migrated successfully, then `alembic check` exposed eight
  `TEXT` versus SQLModel `AutoString/VARCHAR` metadata drifts. The models now declare those
  published `TEXT` types explicitly; existing revision files remain unchanged.

## Explicit Residuals

- The web process still owns APScheduler and therefore remains constrained to one replica.
- The test suite emits deprecation warnings from the `twikit`/`js2py` dependency path; these
  do not affect test isolation but should be removed through a dependency or adapter update.
- Provider wiring, disposable Neon branches, production backup/restore, and Heroku release
  changes remain outside this packet.
