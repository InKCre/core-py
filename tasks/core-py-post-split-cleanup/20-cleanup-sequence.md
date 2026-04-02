# Cleanup Sequence

## Recommended Order

1. strengthen `app/business/source/AGENTS.md` from overview into local-guide shape
2. strengthen `app/business/sink/AGENTS.md` from overview into local-guide shape
3. expand `app/business/info_base/resolver/AGENTS.md` so resolver-local hazards and contracts stop depending on parent guide only
4. expand `app/business/info_base/storage/AGENTS.md` beyond built-in ID notes
5. scan whether any slow-moving `core-py` architecture still spans multiple business subtrees and survives directory refactors
6. only then decide whether a minimal `docs/30-unit-tdd/` seed is justified
7. finally, check whether `core-py` needs any local `docs/00-meta/` beyond the shared baseline

## What Might Still Need Centralized Unit Memory

Only candidates like these should even be considered:

- a unit-local contract that genuinely spans multiple business subtrees and cannot be placed near one code boundary
- a service-wide internal architecture rule that is stable, expensive to rediscover, and not already deployment/shared truth
- a slow-moving internal technology or layering choice whose meaning survives file moves and subtree reshuffles

Current leading candidate:

- the `extension -> source/resolver -> info_base -> sink` authority pipeline

## What Probably Stays In Local Guides

- source lifecycle details
- sink retrieval/embedding mechanics
- resolver/storage implementation boundaries
- extension runtime mechanics

These now have, or should have, natural local homes.

## What Probably Does Not Need Local `00-meta/`

`core-py` should not create a large local meta engine unless one of these appears:

- unit-specific execution workflows not covered by the shared baseline
- repeated agent failure that comes from missing local SOPs rather than missing architecture or local hazards
- a diagnostic protocol that is genuinely local to `core-py`
