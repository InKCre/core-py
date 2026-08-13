# Extension Registry MVP Integration

- **Objective**: consume exact native Python Distributions from the public
  Registry through the single Core Extension Host while preserving one shared
  installed version and peer-specific enablement.
- **Guardrails**: use ordinary wheels, pip and global site-packages; keep
  Extension dependencies declared in wheel metadata but require them to be
  satisfied by the Core image's supported baseline; never resolve or mutate the
  Core dependency environment inside an enable request.
- **Verification**: focused state-machine, wheel, pip, lifecycle, migration, ACL,
  OpenAPI, container and six-wheel probes; `pdm run check`; exact-main image and
  wheel publication; public install/enable/run/disable/uninstall evidence is
  captured by the parent Registry task.
- **Current Truth**: native Registry Release and Simple APIs are public at
  `registry.inkcre.dev`; Core production runs the canonical `extensions` schema.
  Black-box install succeeded after canonicalizing Host SDK ranges. Enable then
  exposed unbounded pip dependency backtracking and exceeded Heroku's 30-second
  request limit without persisting enablement.
- **Next Step**: ship the image-owned dependency baseline and wheel-only runtime
  preflight, redeploy Core, then repeat install/enable/disable/uninstall and the
  browser Module Federation journey.

## Delivery Result

- The single canonical `inkcre.extensions` relation owns exact installed version,
  nickname, config/schema and peer IDs in `enabled[]`; target/binding relations
  and the legacy scanner were removed by the authorized clean cutover.
- Six first-party Extensions build as normal PEP 420 wheels, publish through the
  Registry's PyPI-compatible API, and load through the standard
  `inkcre.core.extensions` entry-point group.
- Core owns one Host, atomic enablement RPC, reversible lifecycle publication,
  source-job ownership and ordinary global site-packages consumption.
- Production black-box evidence drove two corrections before final promotion:
  strict npm/SemVer Host SDK range syntax and image-owned dependency admission.

## Supporting Material

- [Evidence](evidence.md): exact baseline symbols, contracts, and discovered
  hazards.
- [Impact Handshake](handshake.md): mutation address, state diff, blast radius,
  invariants, verification, and uncertainties.
- [Plan](plan.md): staged implementation and promotion gates.
