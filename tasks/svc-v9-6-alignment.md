# SVC v9.6 Alignment

## MVT Core

- Objective & Hypothesis: align `core-py` to the latest shared SVC baseline, adopt the optional multi-repo extension explicitly, and hard-cut old v9.3 shared entrypoints.
- Guardrails Touched: `docs/_shared/` stays read-only from Spoke context; shared-doc source changes must be pushed before the local shared-ref bump.
- Verification: root docs point to v9.6 shared paths, the repo-root wrapper points to `edit-svc-shared-docs`, and `docs/_shared` is bumped to a pushed Hub commit after validation.

## Exploration Scaffold

- Perturbation: shared framework upgrade request plus newly published multi-repo extension support.
- Input Type: Constraint
- Active Mode or Transition Note: Solidify -> Execute for shared-ref alignment and local documentation updates.
- Governing Anchors: `AGENTS.md`, `docs/_shared/00-meta/_svc_v9_6.md`, `docs/_shared/00-meta/multi-repo.md`, `docs/_shared/00-meta/input-constraint.md`, `docs/_shared/00-meta/skills/edit-svc-shared-docs/`.
- Impact Hypothesis: future shared-doc work will route through explicit Hub/Spoke rules instead of the older embedded v9.3 assumptions.
- Temporary Assumptions: historical task notes may still mention v9.3 paths, but current entrypoints should hard-cut to v9.6 immediately.
- Negotiation Triggers: pause if the upgrade requires rewriting local implementation docs into shared truth or changing runtime behavior.
- Promotion Candidates: a tighter Spoke root dispatcher, shared-ref workflow wording, and task-packet guidance.

## Execution Notes

- key findings: `core-py` already satisfies the multi-repo admission rule because it consumes Hub truth through `docs/_shared/`.
- decisions made: hard-cut shared path references; rename the wrapper skill to `edit-svc-shared-docs`; keep historical task notes untouched.
- final outcome: pending shared-ref bump and final validation.
