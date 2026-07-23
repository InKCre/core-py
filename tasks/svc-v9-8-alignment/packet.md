# SVC v9.8 Alignment Task Packet

## MVT Core

- Objective & Hypothesis: align `core-py` and its shared Hub projection from SVC v9.6 to v9.8 without changing product or runtime behavior.
- Guardrails Touched: edit Hub truth source-first; do not bump `docs/_shared` before the Hub commit is pushed; keep Hub changes, the Spoke ref bump, and Spoke-local docs in separate commits.
- Verification: Hub v9.8 guidance matches upstream SVC commit `b87c3a6`; shared-ref checks pass before and after the bump; current Spoke entrypoints resolve to v9.8 with no non-historical v9.6 references.

## Current State

- Current Understanding: Hub v9.8 source commit `8d5f69f` and Spoke shared-ref commit `16f54c5` are published; the Spoke-local dispatcher and task-workspace projection now pass path, reference, and diff checks.
- User-Confirmed Constraints: the user explicitly authorized the isolated Hub, shared-ref, and Spoke-local commit/push sequence; unrelated `pyproject.toml`, `portless.json`, and `tasks/developer-experience-engineering/` changes stay outside this task.
- Active Mode or Transition Note: Constraint; Execute is on the final Spoke-local alignment slice.
- Next Step: publish the isolated Spoke-local documentation commit.

## Shared-Doc Pressure

- Local seam: root `AGENTS.md` and `README.md` still consume the removed `_svc_v9_6.md` path after the shared-ref bump.
- Missing shared rule: resolved by Hub commit `8d5f69f`.
- Local consequence: the Spoke dispatcher must now switch atomically to the published v9.8 paths and behavior.
- Verification pressure after return: run the canonical submodule check, verify every current entrypoint resolves, and confirm non-historical active docs have no `_svc_v9_6.md` reference.

## Execution Notes

- key findings:
  - Hub remote currently has no v9.7 or v9.8 branch, tag, or commit.
  - upstream SVC commit `b87c3a6` contains the v9.6-to-v9.8 migration semantics.
  - the current shared-doc skill path is version-independent and does not require migration.
- decisions made:
  - preserve historical task notes unchanged.
  - do not create shared `15-alignment/` content without concrete coordination pressure.
  - stage the Hub source update before any Spoke pointer or entrypoint switch.
- final outcome: Hub, shared-ref, and Spoke-local alignment slices are complete; the final local-doc commit and push publish this packet and the v9.8 entrypoints together.

## Verification Evidence

- Hub v9.8 source commit `8d5f69f` is reachable on `origin/codex/svc-v9-8-alignment`.
- Spoke shared-ref commit `16f54c5` is published on `origin/develop`.
- Canonical submodule `pre-bump` and `pre-commit` checks passed for Hub commit `8d5f69f`.
- Root `AGENTS.md` and `README.md` resolve `_svc_v9_8.md` and `implementation-taste.md`.
- Active non-task docs contain no `_svc_v9_6.md` path.
- `git diff --check` passes for the Spoke-local slice.

Reproducible checks:

```bash
git submodule status -- docs/_shared
git log -1 --oneline 16f54c5
rg -n '_svc_v9_6\.md' \
  AGENTS.md README.md CONTRIBUTING.md .agents \
  docs/30-unit-tdd docs/40-deployment \
  -g '*.md'
git diff --check
```

Observed results:

- `docs/_shared` resolves to `8d5f69fe46ae8c673aecc0399f37678acce8eb5b`.
- `16f54c5` is the isolated shared-ref commit on `develop`.
- the active-path search returns no `_svc_v9_6.md` reference.
- the diff check returns no errors.
