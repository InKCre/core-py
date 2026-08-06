# Development Environment

## Local Requirements

- Python 3.12
- PDM 2.27.0
- local Docker, or one Docker daemon reachable through an SSH-config alias
- a populated `.env` file

The checked-in Python selector is `.python-version`. The foundation CI uses the same
Python selector and PDM version.

## Local Startup

The supported complete runtime is an SVC worktree capability:

```bash
svc status . --json
svc dev ensure database --repo . --json
```

It starts PostgreSQL/pgvector, performs deterministic development initialization, then
starts both core-py and PostgREST. Committed `svc.json` selects local Docker. An ignored
`svc.local.json` may select `ssh`, one SSH-config alias, and the remote Docker executable;
tracked files never own a hostname, user, key, or machine path.

The SSH provider sends an allowlisted build context and one bounded Compose payload to the
remote host. Remote services publish dynamic remote-loopback ports and an instance-owned
OpenSSH control tunnel maps independent local-loopback ports to them.

Runtime state is written to `.runtime/database/<core-svc-instance>/`. Its `runtime.json`,
`profile.json`, and `readiness.json` record:

- owner repository and core-py SVC instance;
- exact Compose project and Docker daemon ID;
- source revision and dirty-source fingerprint;
- database contract revision and migration head;
- core and PostgREST loopback URLs.

Peers must consume that exact profile/descriptor. Sharing only an SSH alias, daemon, port,
or contract version does not prove that core-py and client-web use the same database.
Only core-py owns Compose startup, reset, volume deletion, credentials, and tunnel cleanup.

## Shared Runtime Boundary Diagnostics

An attached peer proves the selected database runtime by matching the owner descriptor and
readiness evidence for:

- runtime instance and owner repository;
- Compose project and Docker daemon ID;
- source fingerprint, database contract revision, and migration head;
- core-py and PostgREST loopback endpoints.

This is a contract-compatible attachment, not proof that the peer's pinned core-py image and
the running owner image are byte-for-byte identical. A different source revision or image is
valid while the contract revision and migration head remain compatible. When diagnosing
implementation-specific behavior, compare `source_revision` and `core_image` in
`runtime.json` with the peer's pinned image digest before assuming artifact equality.

The Compose network and PostgreSQL endpoint are currently derived from the exact Compose
project, source fingerprint, checked-in service wiring, and recorded local/remote ports; they
are not published as independent profile identity fields. If a future issue suggests that two
peers reached different databases, compare `runtime.json`, `profile.json`, and
`readiness.json` from the owner before inspecting provider state. Do not accept matching
daemon IDs, ports, or contract revisions alone. If owner, project, fingerprint, endpoints,
or readiness do not converge, stop reuse and let core-py re-establish the runtime.

External peers must not reset or tear down a core-py-owned runtime. The command path rejects
both operations; current dedicated external-attachment regression coverage proves teardown
rejection but does not separately exercise reset rejection. Treat that missing negative case,
and first-class network/database endpoint identity, as the first places to strengthen if a
shared-runtime boundary failure is observed.

For Python-only iteration against an already initialized database:

```bash
cp .env.example .env
pdm install -G dev --frozen-lockfile
pdm run doctor
pdm run check
pdm run dev
```

`doctor` and `check` do not start the application or connect to a database. The full
repository contract checks tool versions, lock/export consistency, migration integrity,
formatting, lint, settings isolation, and the complete unit-test suite.

Use narrower read-only checks while iterating:

```bash
pdm run check:foundation
pdm run format:check
pdm run lint
pdm run test
svc dev status database --repo . --json
pdm run dev:database ready
```

The test harness disables dotenv before application imports. Repository checks do not read a
developer `.env` or use its database and API credentials.

## Required Environment Variables

The checked-in baseline is `.env.example`.

Required for direct Python execution:

- `DATABASE_URL`
- `JWT_SECRET`

Lifecycle execution additionally requires:

- `MIGRATION_DATABASE_URL`
- `CORE_DATABASE_PASSWORD`
- `POSTGREST_DATABASE_PASSWORD`

Commonly needed:

- `CLIENT_ID`
- `CLIENT_NAME`
- `CLIENT_BASE_URL`
- `LLM_SP_AK`
- `LLM_SP_BASE_URL`
- `OBSRV__*`

## Database Branch Workflow In CI

The repository currently uses Neon branch automation for pull requests.

- `branching-database.yml` creates or reuses `preview/core-py/pr-<number>` for trusted PRs
- every preview branch is a seven-day child of the sanitized `preview-base`
- the branch workflow only establishes the exact isolated branch identity
- the exact PR artifact owns initialization and readiness during application delivery
- PR close deletes only the matching deterministic Neon branch

## Migration Commands

- `pdm run db:generate "message"` creates a candidate revision for review.
- `pdm run db:record` appends reviewed new revisions to the integrity manifest.
- `pdm run db:migrate` applies checked-in revisions.
- `pdm run db:init --profile development` creates the complete deterministic baseline.
- `pdm run db:ready --profile development --json` verifies it without mutation.
- `pdm run db:reset-dev --confirm reset-development-data` restores the same guarded
  baseline and refuses every non-development database.
- `pdm run check:migrations` checks the local graph, metadata registration, and release
  contract without connecting to a database.
- CI validates `migrations/revision-integrity.json` on pull requests and managed-branch
  pushes. A base branch without the manifest is a one-time hard-cut bootstrap; after that,
  protected entries and revision contents may not be modified, deleted, or renamed.

Generation and application are deliberately separate operations.

## Bounded Runtime Cleanup

```bash
pdm run dev:database reset --yes
pdm run dev:database stop
```

Both commands resolve the current core-py SVC worktree identity. Reset remains protected by
the database-owned development marker. Stop removes only the descriptor's exact Compose
project, volume, credentials, and SSH control tunnel.
