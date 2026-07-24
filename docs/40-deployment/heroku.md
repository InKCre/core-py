# Heroku

## Artifact And Authority Model

Heroku consumes the same provider-neutral OCI source proved in CI:

- `heroku-web` starts core-py;
- `heroku-release` is a no-op release guard;
- `Dockerfile.postgrest` adds only a `$PORT` adapter to digest-pinned PostgREST.

The protected GitHub delivery job runs database lifecycle commands before releasing images.
This is intentional: Heroku config vars are available to every dyno in an app, so putting a
migration-owner URL into Release Phase would also expose it to the web process.

Core Heroku config contains only an `inkcre_core` URL. PostgREST config contains only an
`authenticator` URL. The direct Neon owner URL exists only in the protected delivery job.
Heroku supplies compute, routing, and runtime configuration; it owns neither the build nor
the database.

`Procfile`, `requirements.txt`, and `app.json` remain legacy buildpack inputs for the
existing staging app until the legacy-retirement execution. They do not define preview or
production CD.

## Pull Request Previews

Trusted same-repository pull requests currently use:

- app name `inkcre-core-pr-<number>`;
- pipeline `inkcre-core`, stage `review`;
- container stack in the US region;
- one Eco `web` dyno;
- matching seven-day Neon branch `preview/pr-<number>`;
- no Heroku addon.

The branch workflow owns only exact isolated branch creation/deletion. After the repository,
portable-runtime, and branch checks pass for the exact PR SHA, preview delivery:

1. builds images before receiving deployment secrets;
2. verifies the exact branch and TTL;
3. removes inherited provider-created protocol roles only on first bootstrap;
4. runs the PR artifact's complete preview-profile initialization and readiness;
5. derives an `inkcre_core` URL without logging it;
6. configures and releases the Heroku app;
7. forces `web=1:eco` and probes `/livez` plus `/readyz`.

The owner URL and PostgREST database password never enter preview Heroku config.
PR close destroys only the deterministic app; the independent Neon workflow deletes only
the deterministic database branch.

The current `preview/pr-<number>` identity remains a known single-repository limitation.
Repository-qualified review identities are owned by the later multi-repository CD execution.

## Canonical Production

Production is one logical environment containing two peer transports:

| App | Responsibility | Database principal | Formation |
|---|---|---|---|
| `inkcre-core-production` | native core peer | `inkcre_core` | one Eco web dyno |
| `inkcre-postgrest-production` | browser HTTP peer transport | `authenticator` | one Eco web dyno |

Both apps use the container stack, US region, no addons, and the `production` stage of the
single `inkcre-core` pipeline. They address the exact canonical Neon `production` branch.

`.github/workflows/production-deploy.yml` runs only after repository/runtime checks pass for
the exact current `main` SHA, or by a main-only recovery dispatch. It builds core and
PostgREST before receiving deployment inputs.

Production delivery guards:

- exact live branch ID, name, historical parent, no TTL, and ready state;
- a fresh no-TTL recovery branch whose parent is the exact live branch;
- exact core and PostgREST app names, stack, region, addon absence, and pipeline stage;
- a one-time `peer-database-runtime-v1` bootstrap switch for provider-role replacement;
- every application-table row count before and after lifecycle convergence.

The first hard cut scales the old core web process to zero before replacing unsafe inherited
roles and moving the protocol schema. Later deliveries simply converge the idempotent
contract. Images and config releases are polled to a terminal state; registry login and
transfer alone receive bounded retries.

The acceptance probe requires:

- core liveness and full database readiness;
- PostgREST authenticated read and write;
- cleanup of the fixed probe row;
- wrong-secret HTTP 401;
- anonymous HTTP 401;
- both formations remaining Eco.

A failed probe rolls back both images when the database contract was already established.
During the one-time schema hard cut, an old core image is incompatible; failure therefore
leaves core stopped instead of performing a false rollback. No workflow runs an Alembic
downgrade.

## PostgREST Runtime Contract

PostgREST is a separate app, not a second process supervised inside the core dyno. It uses:

```text
PGRST_DB_SCHEMAS=inkcre
PGRST_DB_ANON_ROLE=anonymous
PGRST_DB_PRE_REQUEST=inkcre_internal.check_jwt
PGRST_JWT_AUD=inkcre-api
```

`PGRST_DB_URI` and `PGRST_JWT_SECRET` are runtime secrets. The pre-request function enforces
issuer, role, numeric dates, expiry, and maximum lifetime in addition to PostgREST signature
and audience validation.

## Secret Boundary

The GitHub `preview` environment owns its Heroku authorization, LLM inputs, and the two
database-role passwords. `NEON_API_KEY` remains a repository secret and `NEON_PROJECT_ID` a
repository variable.

The GitHub `production` environment independently owns:

- dedicated Heroku authorization;
- JWT signing secret;
- LLM inputs;
- `CORE_DATABASE_PASSWORD`;
- `POSTGREST_DATABASE_PASSWORD`.

It records exact non-secret app and Neon branch identities, the fresh recovery branch, and
the one-time bootstrap revision. Production admits deployments from `main` only and does
not reuse preview authorization, database passwords, or JWT secret.

The preview Heroku authorization named `GitHub InKCre/core-py preview CD` was created with a
365-day lifetime on 2026-07-23. Rotate it no later than 2027-07-23 and revoke the superseded
authorization after a green preview deployment.

## Migration Constraint

The protected job is the single migration writer and runs
`db init --profile runtime --environment preview|production`. Rolling a web image back does
not reverse database state. Every revision must pass the fresh digest-pinned
pgvector/PostgREST runtime check and the matching Neon preview before production delivery.

Preview and production automation is not authority to mutate or delete legacy staging
resources; those remain under the explicit retirement execution.
