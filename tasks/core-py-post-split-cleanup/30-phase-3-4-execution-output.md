# Phase 3-4 Execution Output

## Decision

The user confirmed that the following slow-moving unit-local structure should be admitted into `docs/30-unit-tdd/`:

- `extension -> source/resolver -> info_base -> sink`

This candidate is now treated as admitted unit architecture, not just a possible candidate.

## Durable Changes Executed

### New Unit-TDD

- created `docs/30-unit-tdd/business-pipeline-and-authority.md`

### Local Guide Upgrades

- rewrote `app/business/source/AGENTS.md` into a tactical local guide
- rewrote `app/business/sink/AGENTS.md` into a tactical local guide
- rewrote `app/business/info_base/resolver/AGENTS.md` into a tactical local guide
- rewrote `app/business/info_base/storage/AGENTS.md` into a tactical local guide
- added routing from `app/business/AGENTS.md` to the new unit-tdd

### Entry-Point Routing

- updated `README.md` so the documentation map points directly at the admitted unit-tdd file

## Not Admitted

Still not admitted into `docs/30-unit-tdd/`:

- source scheduling details
- resolver-local import hazards
- storage built-in ID conventions
- sink retrieve-mode implementation details

These remain tactical and stay in local `AGENTS.md`.
