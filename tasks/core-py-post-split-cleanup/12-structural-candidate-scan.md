# Structural Candidate Scan

## Goal

Identify unit-local truths that are slow-moving enough to qualify for `docs/30-unit-tdd/`, instead of being left in local tactical guides or shared docs.

## Candidate A: Business Pipeline and Authority Split

### Short Name

`extension -> source/resolver -> info_base -> sink`

### Why It Looks Real

This is not a single-directory hazard. It spans multiple business subtrees:

- `app/business/extension/main.py`
- `app/business/source/main.py`
- `app/business/source/collect_job.py`
- `app/business/info_base/main.py`
- `app/business/info_base/block.py`
- `app/business/info_base/resolver/main.py`
- `app/business/info_base/storage/main.py`
- `app/business/sink/main.py`
- `app/business/sink/embedding.py`

### Observed Structural Facts

1. extensions are the plugin-owned entrypoint for runtime expansion
2. extension startup registers API routes and initializes source / resolver classes
3. source, resolver, and storage all rely on import-time subclass registration into global managers
4. source and extension code may propose blocks / subgraphs, but `InfoBaseManager` owns recursive graph persistence
5. block creation may trigger embedding upsert, but embedding semantics and retrieval still belong to `sink/`
6. sink consumes info-base content through resolver text/embedding paths rather than owning persistence

### Why It Survives Refactors

Even if file names or directory splits change, `core-py` still needs answers to:

- where plugins extend the system
- who owns graph persistence
- who owns embedding lifecycle and retrieval semantics
- how source/output layers are allowed to depend on info-base internals

That makes this a real v9.3 structural candidate, not a local tripwire.

### Initial Gate Result

- unit-local: yes
- cross-subtree: yes
- slow-moving: probably yes
- better than duplicating across local guides: yes
- already shared product-tdd or deployment truth: no

Status: `admit-candidate`

## Rejected Candidate B: Source Scheduling Mechanics

### Why Rejected

Current scheduling behavior is not cleanly stable:

- `SourceManager.set_up_collect_jobs()` directly schedules `collect`
- `SourceCollectJobManager.check()` schedules pending jobs
- source code itself contains a TODO that the direct scheduling path should be replaced by collect jobs

This is migration debt or design instability, not durable slow-moving structure.

Status: `reject-for-now`

## Rejected Candidate C: Resolver and Storage Registry Internals

### Why Rejected

These are real hazards, but still naturally local to `resolver/` and `storage/`:

- lazy-import and circular-import seams
- import-time registration side effects
- raw-content vs solved-content behavior
- built-in storage negative ID rules

They should first be strengthened in local guides before any centralized unit doc is considered.

Status: `keep-local`

## Rejected Candidate D: Sink Retrieve-Mode Details

### Why Rejected

`embedding / reasoning / feature` mode details are still too implementation-shaped and partly incomplete. They belong in local sink guidance unless a slower, unit-wide retrieval architecture emerges later.

Status: `keep-local`

## Current Conclusion

Phase 2 does **not** justify creating `docs/30-unit-tdd/` immediately.

But it does justify keeping one sharply bounded candidate alive:

- `business pipeline and authority split`

If this candidate still survives after local-guide cleanup, it is the first thing that should be admitted into `docs/30-unit-tdd/`.
