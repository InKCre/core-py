# Heroku

## Artifact And Authority Model

Heroku consumes the same canonical provider-neutral OCI image published to GHCR:

- the exact GHCR digest is tagged and pushed as the Heroku `web` image without rebuilding core;
- `heroku-release` is a lightweight no-op guard containing no core code;
- `Dockerfile.postgrest` adds only a `$PORT` adapter, using a digest-pinned static BusyBox
  interpreter because the digest-pinned PostgREST runtime contains no shell.

The protected GitHub delivery job runs database lifecycle commands before releasing images.
This is intentional: Heroku config vars are available to every dyno in an app, so putting a
migration-owner URL into Release Phase would also expose it to the web process.

Core Heroku config contains only an `inkcre_core` URL. PostgREST config contains only an
`authenticator` URL. The direct Neon owner URL exists only in the protected delivery job.
Heroku supplies compute, routing, and runtime configuration; it owns neither the build nor
the database.

The retired buildpack surfaces (`Procfile`, `requirements.txt`, and `app.json`) are no longer
checked in. PDM owns dependency resolution and the OCI Dockerfiles own every deployed process,
so leaving Heroku does not require reconstructing runtime behavior from provider-specific
files.

## Pull Request Previews

Trusted same-repository pull requests currently use:

- app names `inkcre-core-py-pr-<number>` and `inkcre-postgrest-pr-<number>`;
- sibling static Registry alias
  `https://pr-<number>.inkcre-core-py-extension-registry-preview.pages.dev`;
- pipeline `inkcre-core`, stage `review`;
- container stack in the US region;
- one Eco `web` dyno for each peer transport;
- matching seven-day Neon branch `preview/core-py/pr-<number>`;
- no Heroku addon.

The branch workflow owns only exact isolated branch creation/deletion. After the repository,
portable-runtime, and branch checks pass for the exact PR SHA, preview delivery:

1. installs the frozen `extension-preview` PDM group, builds all discovered first-party wheels,
   and asks `inkcre-ext preview build` for one Python-only static Registry facade;
2. builds images before receiving deployment secrets;
3. reverifies the exact PR head, deploys the facade directly to the dedicated Pages project,
   asserts the deterministic `pr-<number>` alias, and compares every remote descriptor, Simple
   page, wheel, and PEP 658 metadata file with the exact-head local output;
4. verifies the exact database branch and TTL;
5. removes inherited provider-created protocol roles only on first bootstrap;
6. runs the PR artifact's complete preview-profile initialization and readiness;
7. derives an `inkcre_core` URL without logging it;
8. configures `EXTENSION_REGISTRY_URL` to the verified sibling alias before releasing or scaling
   Core, then configures and releases both apps against the exact database branch;
9. forces both formations to `web=1:eco`, probes Core `/livez` plus `/readyz`, and
   verifies authenticated PostgREST read/write plus anonymous and wrong-secret denial.

Required preview configuration is the exact non-secret project variable
`CLOUDFLARE_EXTENSION_PREVIEW_PROJECT=inkcre-core-py-extension-registry-preview`, plus the
preview-environment `CLOUDFLARE_ACCOUNT_ID` and minimally scoped `CLOUDFLARE_API_TOKEN` secrets.
Fork pull requests never enter this environment. PR-close delivery replaces the exact Pages
branch alias with a trusted no-cache tombstone before deleting the two deterministic Heroku apps;
the independent Neon workflow remains the database-branch cleanup authority.

The repository-level `JWT_SECRET` is the single signing-key authority for canonical
production and same-repository previews. Delivery passes that value directly to both Preview
apps on every run, so Core and PostgREST remain aligned across redeployments or app
recreation. The value stays in GitHub Secrets and never enters source, artifacts, logs, or
workflow summaries.

The owner URL never enters preview Heroku config. The Core app receives only the `inkcre_core`
URL and public sibling Registry origin; the PostgREST app receives only the `authenticator` URL.

Repository-qualified app and branch identities keep a core-py PR and a client-web PR with
the same number from addressing the same review resources.

## Canonical Production

Production is one logical environment containing two peer transports:

| App | Responsibility | Database principal | Formation |
|---|---|---|---|
| `inkcre-core-production` | native core peer | `inkcre_core` | one Eco web dyno |
| `inkcre-postgrest-production` | browser HTTP peer transport | `authenticator` | one Eco web dyno |

Both apps use the container stack, US region, no addons, and the `production` stage of the
single `inkcre-core` pipeline. They address the exact canonical Neon `production` branch.
Peers discover their non-secret connection contract through
[`deploy/profiles/production.json`](../../deploy/profiles/production.json); credentials never
enter that profile.

`.github/workflows/production-deploy.yml` runs only after `artifact-publish.yml` succeeds for
the exact current `main` SHA, or by a main-only recovery dispatch. It pulls the SHA-addressed
GHCR service image, verifies its embedded schema evidence, and builds only the no-op release
guard and separate PostgREST adapter before receiving deployment inputs.

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

The production probe records the GHCR digest, transferred local image ID, and Heroku release
identities. Registry manifest digests may differ after transfer, so the guarantee is one local
config/layer lineage and source SHA, not textual equality between registry digest strings.

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

The mutable GHCR `stable` tag advances only after this probe succeeds. Publication without
production admission leaves `stable` unchanged; an automatic failed-probe rollback therefore
continues to resolve to the previous production image.

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

The GitHub `preview` environment owns its Heroku and Cloudflare authorization, LLM inputs, and
the two database-role passwords. `JWT_SECRET` and `NEON_API_KEY` remain repository secrets,
while `NEON_PROJECT_ID` and `CLOUDFLARE_EXTENSION_PREVIEW_PROJECT` remain repository variables.

The GitHub `production` environment independently owns:

- dedicated Heroku authorization;
- LLM inputs;
- `CORE_DATABASE_PASSWORD`;
- `POSTGREST_DATABASE_PASSWORD`.

It records exact non-secret app and Neon branch identities, the fresh recovery branch, and
the one-time bootstrap revision. Production admits deployments from `main` only and does
not reuse preview authorization or database passwords. Preview and production deliberately
share only the repository signing-key authority.

The preview Heroku authorization named `GitHub InKCre/core-py preview CD` was created with a
365-day lifetime on 2026-07-23. Rotate it no later than 2027-07-23 and revoke the superseded
authorization after a green preview deployment.

## Migration Constraint

The protected job is the single migration writer and runs
`db init --profile runtime --environment preview|production`. Rolling a web image back does
not reverse database state. Every revision must pass the fresh digest-pinned
pgvector/PostgREST runtime check and the matching Neon preview before production delivery.

## Retired Runtime

There is no persistent staging environment. The `inkcre-core` pipeline contains exactly the
two canonical production apps above; review apps exist only for an eligible pull request and
are removed when it closes.

The pipeline is intentionally not connected to a GitHub repository in Heroku. GitHub Actions
is the only review-environment controller and couples each deterministic app through the
Heroku Platform API. Reconnecting Heroku's legacy GitHub integration would create an
all-events repository webhook and a competing review-app authority.

The former `inkcre-core-staging` and `inkcre-pgrst` apps were deleted on 2026-07-24. Deleting
the staging app also removed its Logtail addon and Better Stack drain. Neither app had a
custom domain. GitHub no longer contains their staging environment or the all-events Heroku
webhook.
