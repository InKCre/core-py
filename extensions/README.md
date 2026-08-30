# InKCre Extensions

First-party Extension producer sources live here。Folder name is the extension ID；extensions are disabled by
default。The Extension Host consumes exact Registry Releases as ordinary wheels；it does not resolve or download
arbitrary untrusted code。

Shared extension/graph/resolver/storage contracts live in the Hub Product TDD。This guide owns the current core-py
package seams；Memos and RSS details live in their Unit TDDs。

## Package Shape

```text
extensions/<extension_id>/
  __init__.py      ExtensionBase subclass and lifecycle composition
  schema.py        extension/source canonical config or content models
  source.py        optional SourceBase implementation
  resolver.py      optional exact resolver contract
  api.py           optional extension-owned HTTP surface
  pyproject.toml   Distribution identity, version, dependencies, and build metadata
  .changes/        feature fragments pending an independent Release PR
  CHANGELOG.md     generated Python Distribution release history
```

Dependencies admitted by an extension must also be frozen in the owning root profile/lock；an isolated extension lock
is not enough for the production artifact。

## First-party release intent

Every immediate Extension project declaring `[tool.inkcre-extension]` is an independent Python Distribution producer。
Its `pyproject.toml [project].version` is the Python Distribution version authority and must equal the Extension Release
Version used by every Distribution association；the root Core version has an independent lifecycle。

Feature changes add a project-local fragment but leave version and changelog preparation to the
independent Release PR：

```bash
pdm run towncrier create --config towncrier.toml --dir extensions/rss +.changed.md
pdm run check:releases --base origin/main
```

Towncrier validates and renders the six shared fragment types。Repository orchestration discovers
affected projects，chooses the highest maturity-aware bump and updates `pyproject.toml`。Pull-request
CI rejects artifact input without matching intent and rejects feature-branch version/changelog
preparation。Post-main publication still enumerates Extensions only and selects changed versions。

## Extension Lifecycle

```python
class Extension(
  ExtensionBase[ExtensionConfig],
  ext_id="example",
  config_cls=ExtensionConfig,
):
  @classmethod
  def _init_resolvers(cls):
    from .resolver import ExampleResolver  # noqa: F401

  @classmethod
  def _init_sources(cls):
    from .source import Source  # noqa: F401

  @classmethod
  def _register_apis(cls, router):
    register_api(router)
```

- Import hooks only register runtime classes in memory；explicit bootstrap reconciles database catalogs。
- Enable/start publishes source/API runtime capability；disable/close removes its route set。
- Installed exact decoders remain available for persisted blocks even when the extension is disabled。
- Extension config update is merge → complete typed validation → durable write → live assignment。Disabled extension
  can be configured before enable。

## Extension API Authentication

Extension routes inherit core peer JWT by default。An external protocol may deliberately request an auth-neutral root，
then make authentication visible on child routers：

```python
class Extension(...):
  @classmethod
  def api_dependencies(cls):
    return []

  @classmethod
  def _register_apis(cls, root):
    root.include_router(public_router)
    root.include_router(
      protocol_router,
      dependencies=[fastapi.Depends(require_protocol_token)],
    )
```

Do not add a global JWT path override or a core User model for one protocol。The extension owns only its bounded route
authentication；graph/database authority remains unchanged。

## Sources

A source owns native fetch/adapter/policy and maps information into blocks/relations through info-base managers or an
owning repository/application service。

- Config belongs to the source instance；long-lived cursor/validators belong to source state；one-run overrides and
  diagnostics belong to collect job。
- Manual and scheduled triggers create ordinary `PENDING` collect jobs and share the atomic-claim runner。
- `collect(job)` raises failures；the owning unit defines partial effects and state-advance boundary。
- Exact native identity outranks heuristic duplicate reduction。Do not fuzzy-overwrite uncertain graph state。
- `_organize()` is a legacy abstract method, not an automatic post-collection lifecycle。Use an explicit no-op until a
  real organization command is designed。

## Resolvers

Resolvers interpret a block's hydrated content plus required direct relations。IDs are exact、namespaced and versioned，
for example `extensions.example.item.v1`。

Concrete resolvers must implement async `get_text()`。Unsupported capability raises
`UnsupportedResolverCapability`；supported-but-no-result returns `None`；unknown exact ID fails。`refresh` replaces a
local snapshot，while `materialize_missing` only permits an absent derivation。

Use one of the nine `core.<kind>.v1` semantic content blocks for text、HTML、image、audio、video、PDF、EPUB、ZIP or
file bytes。Protocol/source metadata may remain a separate metadata block connected by an owning relation。

## Storage

Storage handlers turn their opaque pointer into bytes；they do not classify content。Writable storage owns pointer
serialization and byte C/R/U/D。Application/source code calls the common create seam and persists the returned pointer，
without hard-coding PostgreSQL/S3/Nextcloud pointer grammar。

Current built-ins are generic HTTP read (`-1`) and PostgreSQL binary C/R/U/D (`-4`)。Do not recreate media-specific
HTTP storage types。

## Reference Units

- [Memos extension](../docs/30-unit-tdd/memos-extension.md)：external protocol API、auth、family graph、semantic
  attachments、best-effort cleanup。
- [RSS extension](../docs/30-unit-tdd/rss-extension.md)：incremental source state、exact reconciliation、collect jobs、
  full text and enclosure materialization。
