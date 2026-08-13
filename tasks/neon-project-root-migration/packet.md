# Neon Project Root Migration

- **Objective**: migrate canonical production, the sanitized `preview-base`, and every active
  repository-owned PR preview from Neon project `small-feather-66252738` into one new Neon
  project whose root/default branch is canonical `production`; rotate the project-scoped Neon
  API key, synchronize GitHub and runtime coordinates, verify the cutover, then retire the old
  project.
- **Guardrails**: do not expose credentials or production values; preserve every production
  application row, schema object, role contract, and runtime consumer; keep `preview-base`
  data-free; rebuild previews only for open trusted PRs; retain an encrypted verified backup
  and a working rollback path until the new production and previews pass; do not delete the old
  project before every cutover gate is proven.
- **Verification**: encrypted custom archive plus checksum; matching value-free manifests and
  Alembic head; empty provider schema diff; passing checked-in readiness; exact role/catalog
  checks; successful core and PostgREST production probes; successful preview delivery for all
  open trusted PRs; GitHub variables point only to the new identities; old API key no longer
  authenticates after rotation; final Neon inventory contains the new project and not the old
  project.
- **Current Truth**: migration completed on 2026-08-13. Active project
  `proud-sky-36728055` has root/default `production`, one no-TTL recovery child, sanitized
  `preview-base`, and seven-day branches for open PRs 45 and 52. GitHub and every Heroku
  consumer reference the new project. The old project is soft-deleted and recoverable until
  2026-08-20T11:39:39Z; both old project keys are revoked.
- **Next Step**: keep the encrypted archive through the old-project recovery window, review the
  local automation hardening diff, and commit only after an explicit human command.

## Impact Handshake

- **Address and Object**: Neon organization `org-falling-queen-46920568`; retired project
  `small-feather-66252738`; active project `proud-sky-36728055`; GitHub repository
  `InKCre/core-py` repository/environment secrets and variables; canonical deployment truth in
  `docs/40-deployment/`; exact workflow/config references discovered by the audit.
- **State Diff**: old immutable-root project owns production and previews -> new project root
  owns canonical production, sanitized `preview-base`, and rebuilt active previews; all consumers
  reference the new project/key/branch identities; old project is deleted only after verification.
- **Operation**: create and restore provider resources, rotate a project API key, update external
  configuration, rebuild disposable preview branches, cut over runtime connections, update local
  deployment truth, and finally delete the old project.
- **Blast Radius Forecast**: Neon production and preview databases; GitHub preview and production
  workflows; core/PostgREST/Render/Heroku runtime connections; recovery checkpoints; operational
  documentation and tests that encode branch topology.
- **Invariants Check**: no product behavior change; no loss or leakage of production data; no
  plaintext backup at rest; no credential in logs/files/task material; no closed-PR preview
  recreation; no old-project deletion while any runtime or workflow still depends on it.
- **Verification**: pre/post manifests, checksums, schema and role checks, readiness/probes,
  provider and GitHub inventories, active-preview workflow results, and explicit rollback probes.
- **Uncertainty**: no unresolved uncertainty affects the completed cutover. PR 45 remains on the
  single-Core delivery shape captured by its original event and will gain the current PostgREST
  preview on its next synchronize event.

## Completion Evidence

- New provider topology:
  - `production`: `br-old-recipe-azsvonnw`, root/default, ready, no TTL
  - recovery: `br-hidden-bar-azrlrdel`, direct child of production, ready, no TTL
  - `preview-base`: `br-summer-violet-azswiwfq`, direct child of production, ready, no TTL,
    zero application rows before preview bootstrap
  - PR 45: `br-spring-waterfall-azfql7jo`, child of `preview-base`, seven-day TTL
  - PR 52: `br-jolly-water-azqn2jbk`, child of `preview-base`, seven-day TTL
- GitHub repository secret `NEON_API_KEY` was rotated to project-scoped key metadata ID
  `3263246`. Repository and production-environment project IDs now reference the new project;
  production branch parent is the literal `null`; production branch and recovery IDs match the
  active topology.
- Encrypted production archive:
  `/Volumes/WorkSSD/Development/InKCre/backups/core-py/2026-08-13/project-root-migration/production-final-cutover-20260813.dump.age`
  with SHA-256 `d770e13746e891ad45560b86faec54b80e6f9fc6bb070281b6e82f14d36c1da5`.
  No plaintext archive was written at rest.
- Final source and target value-free manifests matched byte-for-byte. Normalized schema-only
  dumps matched with SHA-256
  `0fb3e9568ae6af80a675feb1fbd321c260d6e62f58f12bf4f3ab2dd01f970836`.
- Production and both Core previews returned HTTP 200 for liveness and readiness. Production
  and PR 52 PostgREST passed authenticated read/write, guarded Extension mutation, wrong-secret,
  anonymous-denial, and cleanup probes against their exact deployed source contracts.
- Database and application reruns for PRs 45 and 52 completed successfully after rebuilding
  their disposable resources. PR 45 intentionally retains its original single-Core preview
  shape; the next synchronize event will converge it to the latest two-app workflow.
- Production workflow run `31695670276` proved the new Neon branch/key/recovery guards,
  migration, readiness, and manifest transition. Its release step rejected Heroku's successful
  same-image no-op; independent production probes passed and the local action now treats that
  response idempotently.
- Old API key metadata IDs `2586162` and `3262801` were revoked. Deleting the old project
  also removed the repository-level Neon settings managed by its integration, so key
  `3263094` was replaced and revoked after those settings were restored explicitly. The old project
  `small-feather-66252738` is absent from active inventory and present only in recoverable
  inventory through 2026-08-20T11:39:39Z.
