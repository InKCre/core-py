# First-Party Native Extension Wheels

> Applies to wheel producers under `extensions/`; the Core application image does not copy this source tree.

- Each child is a PEP 420 `extensions.<extension_id>` wheel. Never add `extensions/__init__.py`.
- Each wheel declares complete direct dependencies, exactly one `inkcre.core.extensions` entry point, and the required namespaced product/Host SDK metadata.
- Extension lifecycle registration must be reversible within one process so disable/re-enable can rebuild sources and resolvers.
- Extension-specific setup may publish typed Peer inbound capabilities and exact public callback routes; it must not require a generic Host wizard protocol or duplicate Source/Cron/Job authority in Extension state.
- `scripts/extension_distribution.py` owns build-shape validation; `scripts/extension_release.py`, Changie, and the publish workflow own release admission.
- Release name/version is immutable. Any changed artifact input requires an admitted version and changelog transition before publication.
- Resolver IDs remain namespaced and versioned. Source execution uses the ordinary Job path; storage owns opaque pointers and bytes, not semantic interpretation.
- Runtime lifecycle and catalog changes follow `app/business/extension/AGENTS.md`; extension-specific durable design belongs in `docs/30-unit-tdd/`.
- Required check: run distribution/release checks and affected extension tests; verify lock changes when dependency metadata changes.
