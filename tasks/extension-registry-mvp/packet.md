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
- **Current Truth**: Registry Runtime/API `0.1.2` is released as an immutable
  Python 3.12-compatible wheel with an explicit `client` extra. The Registry API
  has a published release record containing immutable target records. This branch
  now has additive Registry installation/binding state, exact admitted ZIP loading,
  reversible runtime publication, deterministic Twitter target generation, and
  exact-main target/image delivery while preserving the legacy table and scanner.
- **Next Step**: commit and publish this branch through required checks, capture
  the immutable image and Registry target identities, complete production
  migration/readiness, then hand the released database contract to `client-web`.

## Stage C Delivery Result

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

## Supporting Material

- [Evidence](evidence.md): exact baseline symbols, contracts, and discovered
  hazards.
- [Impact Handshake](handshake.md): mutation address, state diff, blast radius,
  invariants, verification, and uncertainties.
- [Plan](plan.md): staged implementation and promotion gates.
