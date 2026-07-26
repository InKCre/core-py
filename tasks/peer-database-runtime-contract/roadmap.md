# Peer Database Runtime Contract Roadmap

## Target Outcome

One versioned database protocol and lifecycle contract serves every authenticated InKCre peer.
Humans and agents can start, diagnose, reset, test, preview, and deploy it without copying SQL,
guessing initialization order, depending on Neon-specific owners, or addressing production by
accident.

The durable environment policy is:

```text
main -> canonical production
PR(repo, number) -> isolated review environment with TTL
no persistent staging
```

All Heroku web formations remain Eco.

## Completion Status

Executions 01–09 completed on 2026-07-24 and remain operationally green. Canonical production
and the standard PostgreSQL/PostgREST acceptance path are healthy; client-web consumes the
pinned executable contract and has protected-main CI plus isolated database E2E; review
identities are repository-qualified; legacy staging control-plane resources are retired.

The 2026-07-26 closure audit reopened Execution 00 because core-py, client-web, and Hub `main`
no longer shared one published Product TDD authority. Execution 10 has now published that
authority on canonical Hub commit `a0ba0d4`, moved both Spokes to it, and locally proved the
core-owned SSH Docker runtime plus client-web's exact external attachment. Spoke publication
is the only remaining handoff step.

Cloudflare Pages production and preview delivery are now proven and continue under
client-web's own DX packet. They are not part of core-py's remaining scope.

## Execution 00 — Solidify Cross-Unit Contract

- promote stable peer topology, trust-domain, protocol, JWT, and environment claims to the
  `InKCre/docs` Hub Product TDD through the canonical shared-doc workflow;
- keep provider mechanics in core-py/client-web deployment docs;
- select the shared protocol schema name and admitted relation/function surface;
- confirm separate deployable PostgREST app versus a composite gateway; default recommendation
  remains separate processes in one logical environment/pipeline;
- define contract versioning and compatibility policy.

Exit proof:

- one owner exists for every cross-unit claim;
- both Spokes consume the same published Hub commit;
- no frontend/backend hierarchy is reintroduced.

## Execution 01 — P0 Identity And Credential Containment

- reproduce the live role topology on a disposable Neon branch and standard PostgreSQL;
- define fail-closed role reconciliation;
- replace the privileged `anonymous` shape with NOLOGIN/no capability;
- introduce an unprivileged `authenticator` login and authenticated membership;
- remove PostgREST dependence on `neondb_owner`;
- rotate the audit-exposed legacy staging credential while preserving or retiring consumers
  atomically;
- prove canonical production data and application readiness remain unchanged.

Exit proof:

- anonymous cannot connect, impersonate, read, or write;
- authenticator has no direct application privileges and can only become authenticated;
- production and staging manifests are unchanged;
- no credential appears in migration, image, logs, or task artifacts.

## Execution 02 — Portable Migration And Protocol Baseline

- create a fresh-installable baseline that contains no environment-specific role DDL;
- preserve production through checkpoint, encrypted archive, disposable restore, schema
  equivalence, and controlled lineage transition;
- introduce a dedicated shared database protocol schema instead of treating persistence
  tables as permanent public API;
- publish explicit read/write/function/sequence privileges for the authenticated capability
  role;
- establish owner-specific default ACLs and readiness checks;
- keep migration authority separate from peer runtime authority.

Exit proof:

- fresh standard PostgreSQL/pgvector reaches one unique head;
- repeated migrate is a no-op;
- native and PostgREST peers observe the same admitted protocol behavior;
- production row counts and selected value fingerprints are equivalent across the cutover.

## Execution 03 — Lifecycle CLI And Deterministic State

Deliver an OCI command surface:

```text
db init --profile runtime|development
db migrate
db provision-roles
db reconcile-builtins
db seed-dev
db ready --profile runtime|development --json
db reset-dev
db contract --json
```

- separate artifact-owned catalogs from development seed;
- require stable client IDs;
- make built-in extension/source/storage discovery import-safe and scheduler-free;
- add a database-owned development marker plus explicit destructive confirmation;
- make reset refuse canonical production, preview, and unknown databases;
- emit a versioned readiness/contract schema with stable exit codes.

Exit proof:

- init, migrate, role provisioning, catalog reconciliation, and seed all pass twice;
- reset produces the same baseline fingerprint twice;
- no lifecycle command starts FastAPI, an extension runtime, or APScheduler.

## Execution 04 — Standard PostgreSQL/PostgREST Acceptance Harness

Use digest-pinned PostgreSQL/pgvector and PostgREST images to prove:

```text
fresh database
-> init
-> ready
-> start PostgREST
-> authenticated read
-> authenticated write
-> bad secret 401
-> anonymous 401
-> reset-dev
-> identical baseline
```

Also prove migration-head mismatch, missing ACL/default ACL, role drift, absent seed, duplicate
execution, and non-development reset refusal.

Exit proof:

- the complete chain runs in CI without Neon or Heroku;
- failures retain bounded secret-safe diagnostics rather than sleeps or raw connection errors.

## Execution 05 — Versioned Artifact And Local Runtime

- publish core-py runtime images to GHCR by commit and digest with OCI revision metadata;
- pin PostgREST and pgvector images by digest;
- add development and ephemeral-test Compose profiles;
- give every runtime an explicit identity and collision-safe ports/volumes;
- expose machine-readable contract revision and readiness;
- keep one-command cleanup bounded to the selected development/test identity.

Exit proof:

- a clean machine can start the complete runtime from pinned artifacts;
- two isolated test/worktree environments can coexist;
- local cleanup cannot address production or another agent's runtime.

## Execution 06 — Canonical Production PostgREST

- create a digest-pinned production PostgREST Heroku app connected only to canonical production;
- couple it to the single InKCre pipeline production stage;
- force one Eco web dyno;
- inject authenticator credential and shared JWT secret at runtime;
- configure strict audience/claim validation and explicit anonymous denial;
- verify valid read/write, wrong-secret 401, readiness, scale-to-zero wake, and rollback;
- publish the non-secret canonical PostgREST URL, client ID, contract revision, and issuer/
  audience as a deployment profile.

Exit proof:

- canonical client-web can discover production without embedding a credential;
- PostgREST never connects as `neondb_owner`;
- core-py and PostgREST accept the same JWT test vectors.

## Execution 07 — client-web Contract Consumption And DX

- preserve and integrate the existing dirty Phase 2/3 client-web work before new mutation;
- fast-forward/cut over protected `main`, then retire long-lived `develop`;
- remove the obsolete Copilot setup workflow;
- add a typed non-secret deployment profile for canonical production;
- detect legacy staging/PostgREST hosts and guide users through migration;
- retain the JWT secret only in browser/webext-owned storage and exclude it from exports;
- consume a pinned core database contract and generate/check typed PostgREST relation types;
- make runtime contract drift a required `pnpm check` failure;
- teach `pnpm run doctor` to report Docker, image digest, contract version, readiness profile,
  local config provenance, and legacy endpoint status without printing secrets;
- make `pnpm dev` ensure the supported local web and database capabilities;
- make `pnpm test:e2e` own an ephemeral initialized/reset database and exact built browser
  artifacts.

Exit proof:

- a new contributor runs frozen install then one dev command;
- no SQL, role bootstrap, seed ordering, fixed port, or startup sleep exists in client-web;
- TypeScript sees the admitted database protocol instead of unbounded `any`;
- stale contract digest or legacy endpoint fails with an actionable message.

## Execution 08 — Review And Production CD Topology

- restrict previews to eligible internal PRs targeting protected `main`;
- key every environment by repository plus PR number;
- keep one logical InKCre Heroku pipeline and zero persistent staging apps;
- use Eco for every Heroku review and production web dyno;
- create/update/delete the exact matching Neon branch and required runtime apps idempotently;
- keep Cloudflare Pages previews static and secret-free;
- run full data E2E against an isolated CI runtime; allow a human Pages preview to import its
  own credential explicitly;
- record artifact digest, contract revision, URLs, branch identity, and cleanup status as one
  logical review-environment result.

Exit proof:

- two peer repositories can open PR number `N` without resource collision;
- fork PRs receive no deployment credential;
- PR close removes only its environment;
- a failed check cannot update production.

## Execution 09 — Legacy Retirement And Control-Plane Cleanup

- migrate known browser/webext consumers through the client detection window;
- remove the all-events legacy Heroku GitHub webhook;
- detach and remove the old Logtail drain/addon according to retention policy;
- remove `inkcre-core-staging` and legacy `inkcre-pgrst`;
- remove stale GitHub environments/workflow registrations;
- delete stale Git `develop`/`staging` branches after protection checks;
- delete Neon `develop` and later `staging` only after recovery retention gates;
- retain or deliberately reclassify `master`, the pre-cutover checkpoint, and encrypted
  archive;
- update deployment docs and close the task packet after durable promotion.

Exit proof:

- no active code, config, hook, app, domain, branch, or documented command addresses staging;
- canonical production and review smoke remain green after a bounded observation window;
- rollback artifacts remain available for the agreed retention period.

## Execution 10 — Shared Authority And Remote Docker Convergence

- promote the peer topology, protocol, JWT, and environment contract into the canonical SVC
  10.0.1 Hub structure;
- publish one Hub source commit, then move both Spoke shared refs to that exact commit without
  mixing Hub, ref-bump, or Spoke-local commits;
- adopt SVC 10.0.1 in core-py's local guidance;
- preserve local Docker as the portable default while supporting an ignored, machine-local
  SSH Docker target compatible with `wsl.win-ws.localhost`;
- expose a stable runtime-instance identity covering owner, Compose project, network,
  database endpoint, contract revision, and lifecycle scope;
- refuse reuse when core-py and client-web resolve different instance identities, even when
  they happen to address the same daemon or port.

Exit proof:

- Hub owns the peer database contract in its SVC 10.0.1 structure;
- core-py and client-web consume the same published Hub commit;
- core-py local guidance resolves entirely through SVC 10.0.1;
- core-py can run its database lifecycle against the remote Docker host without installing a
  local daemon;
- both Spokes report the same explicit runtime-instance identity and contract revision before
  sharing a database;
- no cross-Spoke shared-ref/freshness CI gate is introduced.

## client-web DX Delta

| Today | Target |
|---|---|
| User/agent supplies URL, client ID, JWT secret, SQL state, and startup order manually | Canonical non-secret profile supplies URL/client/contract; user supplies only the credential |
| No local PostgREST capability | `pnpm dev` ensures a ready, pinned local runtime |
| PostgREST wrapper is effectively untyped | Generated relation/function types are checked against a pinned contract |
| Empty table, missing role, stale migration, and wrong seed look like generic request failures | `doctor` and JSON readiness name the failed contract component |
| Tests depend on whatever database happens to be configured | E2E owns an ephemeral init/reset baseline and cannot address production |
| Browser localStorage may silently retain retired endpoints | Legacy endpoint is detected with an explicit migration path |
| PR identity is only a number and can collide across repos | Review identity is repository + PR and cleanup is exact |
| Long-lived develop/staging state drifts | Protected main plus isolated PR environments |
| Agents copy commands and infer ownership from docs | One executable contract, digest, machine-readable status, and bounded cleanup |
