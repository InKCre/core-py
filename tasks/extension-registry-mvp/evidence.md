# Evidence

## Registry Contract

- Canonical coordinate is `namespace/name`; each segment is lowercase ASCII and
  at most 64 characters.
- Extension Version is canonical strict SemVer without a leading `v` or build
  metadata.
- Public release lookup is
  `GET /v1/extensions/{namespace}/{name}/versions/{version}` and only a
  `published` release is installable.
- A target record contains `target_key`, canonical target-manifest digest,
  `artifact_format`, `entrypoint`, controlled conditions, and provenance.
- Python target format is `python-bundle-v1`; the accepted target key is
  `python-core-v1`.
- Runtime/API `0.1.2` supports Python 3.12 and declares HTTP dependencies through
  the `client` extra. Its immutable GitHub Release wheel is
  `inkcre_extension_registry-0.1.2-py3-none-any.whl` with SHA-256
  `ac8771ba3a92b5e50deee1ea6f5a81511b3e0f4d716c60e24d873c99b9641e56`.

## Core Baseline Evidence

- `app/business/extension/main.py` imports `extensions.<id>`, scans checked-in
  packages into the legacy table, and never downloads code.
- `app/schemas/extension/main.py` defines only legacy `inkcre.extensions` with
  `id`, `version`, `enabled[]`, nickname, config, and config schema.
- `app/routes/extension.py` exposes unnamespaced legacy install/enable/disable/
  config routes and has no uninstall route.
- `run.py` runs legacy artifact sync and starts legacy enabled rows at bootstrap.
- `SourceManager`, `ResolverManager`, and FastAPI dynamic routes currently have
  no complete reversible publication seam.
- `ExtensionManager.RUNNING_EXTENSIONS` is keyed by extension ID but its close
  path tests membership with a class object, so disable does not reliably close.
- `scripts/database_manifest.py` currently requires the pre-migration database
  table set to equal current metadata. Adding tables would therefore make the
  production before-manifest fail unless the additive-empty transition is
  represented explicitly.
- `inkcre` is exposed through PostgREST; new table invariants cannot rely only on
  Python validation.

## Worktree Boundary

- Fresh worktree:
  `/Volumes/WorkSSD/Development/InKCre/.worktrees/core-py-extension-registry-mvp`.
- Branch: `feat/extension-registry-mvp`, based on `origin/main@531b0d2`.
- The user's existing `core-py` worktree and its uncommitted files are excluded.
- Repository SVC adoption remains 10.0.1; installed CLI 11.0.1 reports
  `adoption-pending`, which is not part of this task.

## Stage A Deployment State Evidence

- Append-only migration `f2a6c8e4b1d7` adds `extension_installations` and
  `extension_peer_bindings`; a deferred three-column FK keeps every peer binding
  on the shared exact installation version, while DB checks enforce coordinate,
  SemVer, target-key, and digest grammar even through PostgREST.
- Manifest compatibility is lineage-bound: only predecessor head
  `d9f4e2a1b7c3` may omit the two new empty tables, and current head
  `f2a6c8e4b1d7` requires the complete table set. Both source and converged
  manifests must use schema `inkcre`; unknown and multi-head lineage fails.
- Migration, metadata, protocol, readiness, reset, ACL, profile, and local
  PostgreSQL transition checks passed without changing legacy `extensions`.

## Stage B Runtime Evidence

- Registry install resolves an exact published release and writes no binding.
  New enable matches the local platform profile, requires the exact admitted
  catalog slot and target digest, verifies manifest and bundle bytes, loads
  canonical `extensions.<id>` modules from that ZIP, starts runtime publication,
  and only then writes the peer binding.
- Existing bindings and bootstrap use persisted version/key/digest plus the local
  catalog without Registry access. Disable closes and withdraws routes, sources,
  resolvers, OpenAPI, and ZIP modules before deleting the binding; failure keeps
  the binding, while binding-write compensation forcibly removes an unbound
  runtime even if extension close itself fails.
- The real Twitter bundle preserves canonical source/resolver identities and can
  disable/re-enable. A process-wide atomic claim allows different extension IDs
  to start independently while preventing legacy and Registry managers from
  racing for the same canonical module ID; its concurrent claim and repeated
  publication-withdrawal behavior are covered directly.
- Generated OpenAPI now includes the namespaced installation, config, enable,
  disable, and uninstall surfaces; invalid live configuration is exposed as a
  client-correctable `422` rather than an internal error. Full type/lint and
  runtime focused tests passed.

## Stage C Target And Delivery Evidence

- `extensions/twitter/target-publish.json` fixes `inkcre/twitter@0.1.0`, target
  `python-core-v1`, format `python-bundle-v1`, entrypoint `bundle.zip`, and the
  exact integration, Extension API `^1.0.0`, and Python
  `>=3.12.0 <3.13.0` conditions.
- `scripts/build_extension_target.py` produces a sorted stdlib ZIP with fixed
  timestamp, regular-file mode, and uncompressed storage so zlib versions cannot
  alter immutable bytes; it includes
  `extensions/__init__.py` plus `extensions/twitter/**` while excluding caches,
  distribution output, and bytecode. An isolated import probe resolved
  `extensions.twitter` from the ZIP rather than the checked-in directory.
- Catalog generation validates config and canonical manifest semantics through
  pinned Registry Runtime/API models, recomputes the canonical target digest,
  and rejects bundle or manifest tampering before writing the local admission
  mapping. Real digest-bearing output remains ignored and uncommitted.
- The service image explicitly copies `release/extension-targets/` to
  `/app/extension-targets/`, normalizes directories to `0755` and files to
  `0644`, and revalidates catalog/manifest/bundle agreement as the non-root
  `inkcre` user before the immutable image is pushed.
- Exact-main workflow order is target build, immutable commit image push,
  Registry publication, returned public release/digest/provenance verification,
  then mutable `main` promotion. Same-digest reruns retain the immutable target's
  original source revision and build ID while the delivery summary separately
  records the current image revision; a different digest or publication failure
  stops promotion.
- Verification passed: 32 focused target/container tests; Ruff format/lint;
  focused Pyrefly; GitHub Actions pre-commit lint; YAML parsing; patch whitespace;
  public v0.1.2 wheel SHA-256; and a locked `[cli]` manifest/catalog build.
  Integration then passed the full PDM 2.27.0 repository contract (215 tests)
  and all pre-commit hooks.

## Stage C Build-Tool Lock

- The `extension-publisher` PDM group pins the public Registry wheel URL and
  SHA-256, its `cli` extra, and every transitive publisher dependency. It is
  excluded from the production default group and therefore does not add Typer
  or other publisher tooling to the application image.
- Exact-main CD installs only that group through PDM 2.27.0 with the frozen lock,
  then verifies the installed Registry version and Python 3.12 minor.

## Stage D Production Evidence

- Pull request `InKCre/core-py#47` passed the hermetic repository contract,
  dependency review, portable database runtime, isolated database provisioning,
  and real Heroku preview before squash merge as main revision
  `19632baa5ed1dbd8064387181e557a530a9eec84`.
- Artifact workflow run `31333702751` published
  `inkcre/twitter@0.1.0#python-core-v1` with target digest
  `sha256:70d12049bd31c27e8bf024d26f9df91761a44fe4b58a7110681b171c50d1d679`
  and promoted immutable image
  `ghcr.io/inkcre/core-py@sha256:b8f43a7a9a558e6bb4d86e2d31baffe826a250dcdf32c9faf457a279e836ad10`.
- Production workflow run `31333769383` succeeded. Public `/livez` and `/readyz`
  both returned `200`; readiness reported runtime `ready`, database environment
  `production`, and migration head `f2a6c8e4b1d7`.
- The first later same-digest proof, workflow run `31334256456`, correctly
  stopped before mutable image promotion because the delivery script expected
  `source_repository` in the CLI command summary even though that field belongs
  to the authoritative public release record. The follow-up validates only the
  CLI-owned summary fields, then verifies repository and retained producer
  provenance through `show-release`; the failed run did not trigger production.
