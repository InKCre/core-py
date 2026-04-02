# Phase 5 Split Matrix

## `docs/15-alignment/glossary.md`

Status: completed in Phase 5A.

| section / term cluster | target owner | target path | action | notes |
| --- | --- | --- | --- | --- |
| `info-base`, `extension`, `client`, `collect job` as product/domain terms | shared | `InKCre/docs/15-alignment/product-glossary.md` | merge / confirm | already mostly present in shared glossary; use Phase 5 only to close gaps, not duplicate |
| `info_base`, Python package/module naming | local | `app/business/info_base/AGENTS.md` | move | implementation-specific naming; not product glossary material |
| `source type`, `source instance`, `sources_collect_jobs` vocabulary | local | `app/business/source/AGENTS.md` | move | current wording is tied to table and runtime model |
| `extension runtime class`, persisted extension config wording | local | `app/business/extension/AGENTS.md` | move | runtime-class wording is local implementation truth |
| `block content`, `raw content`, `solved content` | local | `app/business/info_base/AGENTS.md` and `app/business/info_base/resolver/AGENTS.md` if needed | move | resolver/storage boundary is local technical vocabulary |
| ownership shortcuts (`sources gather`, `info-base persists`, etc.) | shared candidate | `InKCre/docs/20-product-tdd/cross-unit-contracts.md` or keep local | review before move | move only if another unit needs the same responsibility map |

## `docs/20-product-tdd/extension-runtime.md`

| current cluster | target owner | target path | action | notes |
| --- | --- | --- | --- | --- |
| one extension ID per deployment / installation state authority | shared candidate | `InKCre/docs/20-product-tdd/system-state-and-authority.md` | rewrite if pressure is proven | express without `ExtensionModel` method-level detail |
| installed vs enabled vs running distinctions | shared candidate | `InKCre/docs/20-product-tdd/cross-unit-contracts.md` | rewrite if API/UI contracts depend on it | good candidate if other units need the state model |
| filesystem-first discovery, metadata file lookup, sync reconciliation | local | `app/business/extension/AGENTS.md` | move | tightly coupled to local package layout and sync implementation |
| `on_start`, `on_close`, router registration, resolver/source init | local | `app/business/extension/AGENTS.md` | move | runtime lifecycle mechanics are code-local |
| enable / disable / start behavior with method names | local with possible shared summary | `app/business/extension/AGENTS.md` first | local-first | add shared summary later only if another unit depends on the state transitions |

## `docs/20-product-tdd/info-base-ingestion.md`

| current cluster | target owner | target path | action | notes |
| --- | --- | --- | --- | --- |
| blocks/relations are persisted authority | shared candidate | `InKCre/docs/20-product-tdd/system-state-and-authority.md` | rewrite if pressure is proven | good shared candidate if other units consume the same graph semantics |
| sources/extensions propose graph data; info-base owns persistence | shared candidate | `InKCre/docs/20-product-tdd/cross-unit-contracts.md` | rewrite if pressure is proven | keep wording at ownership level, not manager level |
| `fetchsert`, dedup rules, persistence order | local | `app/business/info_base/AGENTS.md` | move after local-guide upgrade | current wording depends on manager methods and local implementation |
| resolver vs storage responsibilities | local first, shared candidate second | `app/business/info_base/AGENTS.md` | local-first | only move to shared if another unit actually depends on the same separation contract |
| embedding is sink-owned | shared candidate | `InKCre/docs/20-product-tdd/cross-unit-contracts.md` | rewrite if pressure is proven | candidate because it is a cross-domain ownership statement |

## Recommended Execution Order

1. rewrite `app/business/info_base/AGENTS.md` into a v9.2 local guide
2. extract local runtime details from `docs/20-product-tdd/extension-runtime.md` into `app/business/extension/AGENTS.md`
3. extract local ingestion mechanics from `docs/20-product-tdd/info-base-ingestion.md` into `app/business/info_base/AGENTS.md`
4. only then populate shared `InKCre/docs/20-product-tdd/*` with the small set of statements that pass the shared-admission gate

## Recommendation

Do not execute the remaining two splits in one commit.  
`extension-runtime.md` and `info-base-ingestion.md` should remain gated until their shared slices can be expressed without `core-py` implementation leakage.
