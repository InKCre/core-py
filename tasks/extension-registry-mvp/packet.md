# Extension Registry MVP Integration

- **Objective**: integrate `core-py` with the public InKCre Extension Registry so
  a deployment can install one exact namespaced Extension Version, enable a
  compatible and build-admitted Python target for this peer, disable it without
  residual runtime effects, and uninstall it only after all peer bindings are
  absent.
- **Guardrails**: preserve the checked-in, build-time trust boundary; never
  download or import arbitrary Python code at runtime; keep legacy
  `inkcre.extensions` semantics intact during the MVP transition; preserve one
  shared installed version and per-peer enablement; do not modify the user's
  original worktree or adopt SVC 11.0.1 in this repository.
- **Verification**: focused state-machine, contract, lifecycle, migration, ACL,
  manifest-transition, OpenAPI, and container tests; `pdm run check`; exact-main
  image publication and production migration/readiness; Registry target digest
  matches the admitted bytes in the image; production install/enable/run/disable/
  uninstall evidence is captured by the parent Registry task.
- **Current Truth**: Registry Runtime/API `0.1.2` is released. Core main revision
  `19632baa` is in production at migration head `f2a6c8e4b1d7`; its immutable
  image and `python-core-v1` target are digest-pinned, and public liveness and
  readiness are green. The legacy table and scanner remain intact beside the new
  Registry installation/binding path.
- **Next Step**: production black-box installation found that all six producer
  documents used the PEP 440 comma conjunction `>=0.1.0,<0.2.0`, while the
  language-neutral Host SDK contract and Core consumer use npm/SemVer ranges.
  Publish only the canonical `>=0.1.0 <0.2.0` spelling, enforce it during wheel
  construction, repair the public-demo associations, and repeat the actual
  install/enable/disable/uninstall journey.

## Delivery Result

- `inkcre/twitter@0.1.0#python-core-v1` now has exact Python, integration, and
  Extension API conditions plus a deterministic checked-in-source bundle build.
- The pinned Registry CLI owns canonical manifest bytes. A strict generated
  catalog binds that digest to `/app/extension-targets/twitter/bundle.zip` and
  its manifest; Docker copies the complete generated tree for non-root runtime
  admission.
- Exact-main CD builds and pushes the immutable commit image before target
  publication, validates the public exact target and retained provenance, and
  moves GHCR `main` only after publication succeeds. A publication failure
  cannot trigger automatic production delivery.
- Focused target/container checks, format, lint, type checking, workflow lint,
  YAML parsing, wheel checksum, and a real CLI build passed. The publisher and
  all transitive build dependencies now have a separate frozen PDM group.
  Integration ran the full repository contract with PDM 2.27.0: 215 tests and
  all foundation, formatting, lint, type, migration, and settings gates passed;
  all pre-commit hooks also passed inside the frozen project environment.
- Exact-main artifact publication and production delivery succeeded. The public
  Registry now exposes the Python target, and Core production is ready on the new
  schema.

## Supporting Material

- [Evidence](evidence.md): exact baseline symbols, contracts, and discovered
  hazards.
- [Impact Handshake](handshake.md): mutation address, state diff, blast radius,
  invariants, verification, and uncertainties.
- [Plan](plan.md): staged implementation and promotion gates.
