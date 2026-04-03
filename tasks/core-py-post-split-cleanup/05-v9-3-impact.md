# v9.3 Impact Note

## Why This Matters

The existing cleanup task was written against v9.2 assumptions.

v9.3 changes the framing in three material ways:

1. `docs/30-unit-tdd/` is restored for slow-moving logical unit architecture
2. Local `AGENTS.md` are narrowed to tactical hazards and localized tripwires
3. `docs/00-meta/` becomes an explicit engine layer for working modes and SOPs

So the old cleanup thesis cannot stand unchanged.

## What Changes In This Task

### `30-unit-tdd/` Is No Longer Treated As Near-Forbidden

Under v9.2, the task assumed local context should absorb nearly everything.

Under v9.3, the correct question is:

"After tactical hazards are pushed down into local guides, does `core-py` still have slow-moving logical architecture that deserves a compact unit-level design memory?"

### Local Guide Work Still Remains Necessary

v9.3 does **not** weaken the case for strengthening:

- `app/business/source/AGENTS.md`
- `app/business/sink/AGENTS.md`
- `app/business/info_base/resolver/AGENTS.md`
- `app/business/info_base/storage/AGENTS.md`

Those are still the natural homes for tactical constraints.

### `00-meta/` Needs A Multi-Repo Interpretation

`core-py` already consumes a shared baseline via `docs/_shared/00-meta/`.

This task should therefore ask:

- is the shared baseline enough for `core-py` right now?
- does the shared `00-meta/` already own any shared agent skills / SOPs that should stay shared?
- does `core-py` need local wrappers or unit-specific SOPs?

It should **not** blindly create a large local `docs/00-meta/` tree.

## What Does Not Change

- do not recreate mixed docs under `docs/15-alignment/` or `docs/20-product-tdd/`
- do not move runtime/ops truth out of `docs/40-deployment/`
- do not bypass `tasks/` for exploratory reasoning
- do not re-centralize extension/info-base tactical notes that now have natural local homes

## Risk To Keep Explicit

The original mismatch that existed at task creation time has now been resolved for `core-py`:

- shared source repo baseline is now `InKCre/docs/00-meta/_svc_v9_3.md`
- this unit now consumes that baseline through `docs/_shared/00-meta/_svc_v9_3.md`
- shared agent skills / SOPs are now consumed through `docs/_shared/00-meta/skills/`

The remaining risk is narrower:

- future cleanup may still try to invent a local `docs/00-meta/` tree by habit, even though no repo-local meta engine has been admitted
- cleanup work must still avoid inventing local `docs/00-meta/` structure before real unit-specific workflow pain is demonstrated
