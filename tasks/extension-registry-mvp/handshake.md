# Impact Handshake

## Address And Object

- Runtime/API dependency: `pyproject.toml`, `pdm.lock`, and the Registry contract
  adapter under `app/business/extension/`.
- Deployment state: new SQLModel records under `app/schemas/extension/`, one
  append-only Alembic revision, database-contract constants/readiness/protocol/
  manifest projections, and generated OpenAPI/schema artifacts.
- Runtime: extension manager lifecycle, reversible route/source/resolver
  publication, startup binding recovery, namespaced management routes, and
  settings.
- Artifact admission: Twitter Python target config, deterministic bundle and
  admitted catalog, Docker image, tests, and exact-main artifact publication.

## State Diff

From a legacy artifact scan that treats every checked-in extension as installed
and uses one `enabled[]` array, to an additive Registry path with:

1. one shared exact installation per `namespace/name`;
2. zero or one exact target binding per installation and peer;
3. build-time admitted Python bytes only;
4. reversible enable/disable runtime effects;
5. uninstall guarded by the absence of all peer bindings.

The legacy table and scan keep their current meaning during this transition.

## Operation And Blast Radius

- Add two application tables, one migration head, and their contract/ACL/reset
  projections. This changes the schema consumed by PostgREST and `client-web`.
- Add Registry HTTP resolution at explicit install/enable operations; startup
  uses persisted exact bindings and embedded admission data, not mutable target
  discovery.
- Add a second extension state path alongside the legacy path. Built-in startup,
  source scheduling, resolver registration, OpenAPI, application image contents,
  production manifest capture, and downstream generated client types can move.
- Extend exact-main artifact publication to publish the admitted target without
  weakening the existing application-image delivery.

## Invariants

- No runtime arbitrary-code download, installation, dependency resolution, or
  import path supplied by Registry metadata.
- Registry `published` state does not mean installed, enabled, or running.
- Install creates no binding; binding creation happens only after compatible
  target selection, exact admission, and successful runtime start.
- Disable removes observable runtime effects before deleting its binding; a
  teardown failure keeps the binding for retry.
- Uninstall cannot cascade-delete or hide an enabled peer.
- One deployment row is the authority for the exact installed Extension Version;
  per-peer target bytes may differ but remain digest-pinned.
- Existing legacy rows, configuration, and enabled peers are not migrated or
  reinterpreted in this slice.
- Runtime configuration remains deployment state; Registry release metadata does
  not own it.

## Verification

- Schema model and DB constraint tests cover coordinate/version/digest grammar,
  composite keys, foreign keys, configuration ownership, and uninstall guards.
- Migration tests cover fresh upgrade, append-only history, protocol projection,
  ACL/readiness, schema artifacts, and only-additive-empty before/after manifest
  transitions.
- Runtime tests cover compatible admission, unknown or mismatched digest failure
  without binding, lifecycle rollback, route/source/resolver removal, restart,
  and the existing running-map bug.
- Container tests prove the exact admitted target is present and no downloader is
  introduced.
- Full local check and exact-main CI/image/production proofs bound repository and
  deployment effects.

## Uncertainty And Resolution

- Existing runtime APIs are not reversible. The runtime slice must first expose
  the smallest explicit publication handles; it must not fake disable by only
  deleting database state.
- Registry release records have no release-level digest. The installation stores
  exact version while each binding stores the target-manifest digest; no invented
  release digest is added.
- Target conditions and profile matching come from Runtime/API, while the local
  admitted catalog independently constrains which Python package can execute.
- Multi-peer upgrade coordination remains a deployment operation; this core
  slice must not silently mutate the shared version when bindings exist.
