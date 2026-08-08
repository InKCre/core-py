# Executable Database Contract

## Authority Boundary

`core-py` owns the current executable PostgreSQL protocol artifact without becoming a
privileged central backend. Native runtimes and PostgREST callers are peer transports over
the `inkcre` schema.

The fixed principals are:

| Principal | Shape | Authority |
|---|---|---|
| `authenticated` | NOLOGIN, NOINHERIT | complete admitted `inkcre` protocol capability |
| `anonymous` | NOLOGIN, NOINHERIT | none |
| `authenticator` | LOGIN, NOINHERIT | may switch only to `authenticated` after JWT validation |
| `inkcre_core` | LOGIN, INHERIT | native runtime member of `authenticated` |

Migrations connect through `MIGRATION_DATABASE_URL`. The two login passwords are supplied
at execution time as `CORE_DATABASE_PASSWORD` and `POSTGREST_DATABASE_PASSWORD`; they never
live in a migration or image. Application and PostgREST runtimes never receive the migration
owner URL. Initialization always reconciles those two password-bearing roles, including after
restoring the password-free role definitions from a release artifact.

## Lifecycle

The OCI artifact exposes one ordered initializer and independently callable primitives:

```text
db init --profile runtime --environment preview|production
db init --profile development
db migrate
db provision-roles
db reconcile-builtins
db seed-dev
db ready --profile runtime|development --json
db reset-dev --confirm reset-development-data
db contract --json
db schema --json
```

`init` is the only command consumers need to know for a fresh database. Every command is
safe to repeat. Catalog reconciliation is import-safe and does not start FastAPI,
APScheduler, or extensions.

`reset-dev` requires both the exact confirmation text and a database-owned
`environment=development` identity. It refuses runtime, preview, production, missing, and
unknown identities. The development seed contains only fixed, minimal protocol state,
including client ID `00000000-0000-4000-8000-000000000001`; production rows are never seed.

## Readiness

`db ready --json` has a stable exit code and checks:

- artifact migration head equals database head;
- immutable environment and contract revision;
- role attributes and exact memberships;
- current table, sequence, function, schema, lineage, and internal-state ACLs;
- owner-specific default ACLs;
- the checked-in built-in catalog;
- the fixed development seed when the development profile is selected.

Errors are component-level and never contain a database URL or provider exception. The
FastAPI `/readyz` adapter uses the same check through the unprivileged runtime role.

## JWT And PostgREST

The canonical JWT contract is:

```text
algorithm: HS256
role: authenticated
issuer: inkcre-client
audience: inkcre-api
required: role, iss, aud, iat, exp
maximum lifetime: 24 hours
future iat tolerance: 60 seconds
```

PostgREST exposes only `inkcre`, connects as `authenticator`, uses `anonymous` as the
explicit denied fallback, and invokes `inkcre_internal.check_jwt` before every admitted
request. The FastAPI middleware validates the same vectors.

## Canonical Production Profile

[`deploy/profiles/production.json`](../../deploy/profiles/production.json) is the checked-in,
non-secret discovery surface for peers that join canonical production. It publishes the
stable client-web registration ID, core and PostgREST URLs, contract revision, migration
head, protocol schema, anonymous policy, and exact JWT claim contract.

The profile deliberately contains no credential, database URL, or mutable image tag.
Consumers supply the shared JWT secret through their own secret store. Runtime image digests
remain release evidence because writing a commit's own digest back into that commit would
create a circular artifact identity.

## Versioning

`db contract --json` reports `peer-database-runtime-v1` plus the image source revision.
Every production candidate also contains `/app/database-contract/`:

- `database-roles.sql` recreates the password-free global principals required by policies;
- `database-schema.sql` is a PostgreSQL 17 whole-database schema dump plus only the Alembic and
  contract-state rows needed to resume the lifecycle from the neutral `runtime` identity;
- `runtime-contract.json` records the executable contract that produced the dump;
- `manifest.json` binds both SQL files and the complete runtime contract to the opaque contract
  revision and source SHA.

The dump comes from a separate fresh database initialized with the runtime profile; it contains
no application row. `db schema --json` verifies the embedded files against that manifest.
Core-py publishes SQL, not client-specific generated types; consumers restore the role and schema
files, then use their own mature language tooling.

Published core images are addressed as:

```text
ghcr.io/inkcre/core-py:<40-character-commit>
ghcr.io/inkcre/core-py@sha256:<digest>
```

The digest is the consumption boundary. The commit tag identifies a published candidate and
`main` discovers the newest published main candidate. `stable` moves only after the exact image
content passes Heroku production smoke; consumers resolve it once to a digest before use.
