# Implementation Plan

## Stage A — Contract And Deployment State (complete)

- Pin `inkcre-extension-registry[client]` Runtime/API `0.1.2` from the immutable
  GitHub Release wheel and refresh the frozen PDM lock. This repository has no
  separate requirements export.
- Add `extension_installations` and `extension_peer_bindings` without changing
  legacy `extensions`.
- Keep coordinate segments separate in SQL for canonical querying and composite
  referential integrity. The installation owns exact version, config, and config
  schema; the binding repeats that exact version and owns peer, target key, and
  target-manifest digest.
- Add database CHECK/PK/FK constraints so PostgREST writes cannot bypass the
  canonical shape.
- Add the append-only migration and update constants, metadata, protocol,
  readiness, reset, profile head, schema and manifest-transition tests.
- Gate: focused schema/migration/contract tests and migration history are green.

## Stage B — Reversible Runtime And Manager API (complete)

- Extract a narrow runtime record from the legacy SQLModel coupling.
- Add explicit route/source/resolver publication handles and teardown ordering;
  fix the running-map identity bug and atomically arbitrate the canonical module
  ID across legacy and Registry managers.
- Add Registry installation/binding manager operations and namespaced routes.
- Install validates a published exact release but creates no binding. Enable uses
  Runtime/API matching plus the embedded admitted catalog, starts successfully,
  then creates a binding. Disable tears down before deleting. Uninstall requires
  zero bindings.
- Bootstrap starts only current-peer Registry bindings and does not let legacy
  scan create Registry installations.
- Gate: state-machine, failure atomicity, import-safety, OpenAPI, and lifecycle
  tests are green.

## Stage C — Python Target And Delivery (complete locally)

- Define `inkcre/twitter@0.1.0` target `python-core-v1` with actual Python,
  integration, and lifecycle/API requirements.
- Build the deterministic Twitter bundle, publish it through the pinned Registry
  CLI, and generate an admitted catalog from the same manifest before building
  the application image.
- Copy bundle/manifest/catalog into the image. Runtime accepts only exact catalog
  identity and digest; root PDM lock remains dependency authority.
- Extend exact-main artifact delivery with source revision, build ID, target key,
  and digest evidence while retaining current image/deploy gates.
- Gate: reproducible target, tamper rejection, image inspection, full `pdm run
  check`, and exact-main target/image publication are green.

## Stage D — Production And Downstream Handoff (current)

- Merge through `core-py` required checks; wait for exact-main migration, image,
  readiness, and target publication.
- Record the immutable core image digest and Registry target digest.
- Hand the released database contract and Runtime/API `0.1.2` to `client-web`;
  only then regenerate its database types and implement its peer binding path.
- Final production lifecycle acceptance is owned by the parent Registry task and
  requires both peer targets under `inkcre/twitter@0.1.0`.
