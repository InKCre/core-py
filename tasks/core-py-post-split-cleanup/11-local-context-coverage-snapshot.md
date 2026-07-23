# Local Context Coverage Snapshot

## Strong Enough Now

- `app/business/extension/AGENTS.md`
  - already in local-guide shape
  - owns runtime lifecycle, metadata, and state-transition mechanics
- `app/business/info_base/AGENTS.md`
  - already in local-guide shape
  - owns ingestion mechanics, dedup, resolver/storage boundary, embedding trigger ownership

## Usable But Still Overview-Shaped

- `app/business/source/AGENTS.md`
  - has useful terminology and workflow notes
  - still reads more like a subsystem overview than a change-hazard guide
  - does not call out the important split between:
    - source type registration via `SourceBase.__init_subclass__`
    - source instance lifecycle in `SourceManager`
    - collect job execution in `SourceCollectJobManager`
  - does not surface the current scheduler ambiguity:
    - `SourceManager.set_up_collect_jobs()` directly schedules `collect`
    - `SourceCollectJobManager.check()` separately schedules pending collect jobs
  - does not state where source-local state is allowed to live (`SourceModel.state` vs job state)
- `app/business/sink/AGENTS.md`
  - useful concept map
  - still overview-heavy, not yet strong on change boundaries / invariants
  - does not make the key authority split explicit:
    - sink owns embeddings and retrieval semantics
    - info-base may trigger embedding upsert but is not the embedding owner
  - does not call out that `feature` retrieve mode is not implemented, so changes there are architecture-adjacent but still incomplete
- `app/business/AGENTS.md`
  - good broad map
  - not a replacement for stronger local guides in subtrees below it

## Too Thin For v9.3 Tactical Expectations

- `app/business/info_base/resolver/AGENTS.md`
  - currently only one import warning
  - missing raw vs solved content boundary
  - missing resolver identity / dedup warning around `get_existing()`
  - missing import-time registry side effect via `Resolver.__init_subclass__`
- `app/business/info_base/storage/AGENTS.md`
  - only built-in storage ID notes
  - missing storage registry side effect via `Storage.__init_subclass__`
  - missing dynamic-import fallback warning in `StorageManager.get_storage()`
  - missing explicit storage-only responsibility:
    - fetch raw content from a pointer
    - do not absorb resolver semantics

## Post-Split Risk

If future cleanup jumps straight to `docs/30-unit-tdd/`, these weak local containers will stay weak, and centralized prose will start absorbing truths that should have stayed near code.

## Implication

The first cleanup target should be local-context quality, not centralized unit-TDD creation.

## Explicit Limit Of This Snapshot

This file only evaluates tactical local-context quality.

It does **not** answer whether `core-py` has slow-moving structural truths that deserve `docs/30-unit-tdd/` under v9.3.
