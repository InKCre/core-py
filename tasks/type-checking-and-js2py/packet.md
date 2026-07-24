# Type Checking And Js2Py Task Packet

## MVT Core

- Objective & Hypothesis: explain and bound the repository's `Js2Py_3.13` dependency, then
  introduce one reproducible static type-checking contract without turning dynamic framework
  boundaries into broad ignores. The working hypothesis is that exactly pinned
  `Pyrefly 1.1.1` can gate the fixed runtime artifact if Pydantic, SQLModel/SQLAlchemy,
  extension registries, and untyped third-party packages are treated as explicit boundaries;
  `mypy` is the defined fallback if Pyrefly requires broad suppression.
- Guardrails Touched: preserve the production Twitter/Twikit behavior; keep PDM and its lock
  authoritative; include the fixed built-in extension profile in the eventual gate; do not
  enable Ruff `ANN` as a substitute for semantic checking; do not add global
  `ignore_missing_imports`, broad excludes, or a baseline file that hides future errors;
  keep `docs/_shared/**`, production data, provider state, and the unrelated
  `portless.json` unchanged.
- Verification: establish the exact dependency and runtime-use chain; run a selected checker
  before choosing suppressions; require precise error-code ignores at unavoidable dynamic
  boundaries; make one PDM command authoritative locally and in CI; finish with
  `pdm run check`, pre-commit, lock/export checks, and a protected PR.

## Classification And Mode

- Constraint: add a static type contract without changing product behavior.
- Reality: 215 test warnings originate from a transitive JavaScript interpreter, and no type
  checker is currently installed or executable through the repository contract.
- Active mode: Solidify. Implementation and local verification are complete; the remaining
  work is publishing the protected change and observing remote CI.

## Current Understanding

### Why Js2Py exists

- The root fixed built-in profile depends on `twikit 2.3.3`.
- `twikit` directly requires `Js2Py-3.13`, which installs the `js2py_` import package.
- Twikit imports `js2py_` from `twikit.ui_metrics` and uses `EvalJs` to execute Twitter's
  obfuscated login UI-metrics function. Twikit documents this as reducing account-suspension
  risk during credential login.
- The production `extensions` record currently selects backend `twikit` for Twitter and has
  one enabled client. Removing Twikit or Js2Py would therefore change current production
  behavior, not merely remove an unused development package.
- Twikit's cookie fast path can skip executing UI metrics on some starts, but importing
  `twikit` still imports Js2Py. The dependency and warning therefore remain even when a
  valid cookie file avoids a fresh login.
- The current PyPI Twikit release is still `2.3.3` and still declares `Js2Py-3.13`; there is
  no upstream version-only upgrade that removes it.

### Warning diagnosis

- `pdm run pytest tests/extensions/test_twitter.py -q` passes but reports 215 identical
  warnings from `js2py_/utils/injector.py:200`.
- The warning is Python 3.12 deprecation of code-object `co_lnotab` in favor of `co_lines`.
- This is import-time third-party compatibility noise, not a failing application assertion.
  Disabling Twikit UI metrics would not remove the import-time warning and could weaken the
  login behavior that Twikit intends to preserve.

### Type-checking baseline

- No `mypy`, Pyright, BasedPyright, or `ty` dependency/configuration exists.
- Across `app`, `libs`, `utils`, `extensions`, `scripts`, and `tests`, 388 of 428 functions
  have every non-`self`/`cls` parameter annotated; 249 have return annotations. The source
  is typed enough for a semantic baseline, but tests intentionally account for much of the
  missing return annotation surface.
- Ruff `ANN` would currently produce 228 findings. Annotation presence is not equivalent to
  type correctness, so it is excluded from the first semantic gate.
- Dynamic pressure is concentrated at SQLModel/SQLAlchemy expressions, JSON fields,
  FastAPI decorators, and runtime extension/source/resolver registries.
- Most framework dependencies ship type information. `apscheduler` and the installed
  `twikit` distribution need explicit third-party boundary treatment.
- Ruff is not a semantic type checker. `ty` remains beta and has no stable API. Pyright is
  mature but introduces an official Node-based toolchain. Mypy is a mature Python-native
  fallback with Pydantic's official plugin.
- Pyrefly `1.1.1` is production/stable, installs as a Python development dependency, checks
  unannotated function bodies by default, and has built-in Pydantic v2 support. Its incomplete
  dynamic/ORM support must still pass the zero-baseline proof before it becomes authority.
- The first explicit-path run reported 91 `missing-import` errors because project-root and
  script execution paths were not yet modeled. After adding `.` and `scripts` as search paths
  and pointing the probe at the PDM interpreter, the same 9,786-line shipped surface reported
  one repository-owned error in 0.25 seconds.
- The only error visible to the first explicit-path probe was a package-internal type-only
  import written as a top-level import in `app/business/source/main.py`; that probe was not
  sufficient evidence for a project gate.
- Project mode invalidated that first conclusion by traversing the complete configured import
  graph: it exposed 45 errors and 10 warnings. The earlier missing import had truncated useful
  cross-module evidence, so the task re-entered Diagnose instead of treating the probe as proof.
- The full inventory separated into:
  - real repository defects, including reversed embedding arguments, stale schema exports,
    nonexistent resolver/storage methods, an invalid route call, nonexistent GitHub resolver
    state, and unchecked third-party workflow responses
  - SQLModel class/instance duality and generic class attributes that require narrow explicit
    typing boundaries
- Default Pyrefly now reports zero errors and zero warnings across shipped code, checked-in
  migrations, scripts, and tests without a baseline, preset downgrade, global ignore, or source
  exclusion. The 13 test-only findings were assertion-narrowing gaps and typed test-double
  boundaries; all were fixed rather than excluding tests.
- While running the full Ruff surface, a tracked Twitter cookie conversion script was found to
  contain credential material despite claiming to read stdin. The script now reads stdin only;
  affected Twitter credentials must be rotated because removing the current copy does not erase
  Git history.

## Candidate Execution Contract

1. Add exactly pinned `Pyrefly 1.1.1` as one development dependency and configure it in
   `pyproject.toml`.
2. First run the checker over the shipped Python artifact:
   `app`, `libs`, `utils`, `extensions`, `scripts`, `migrations`, and `run.py`.
3. Include checked-in migration revisions and tests because both surfaces pass the same default
   contract without weakening the shipped-code gate.
4. Use precise rule or path overrides only when a third-party boundary is proven to lack
   usable type information.
5. Fix repository-owned errors. At truly dynamic boundaries, require narrow
   `# type: ignore[error-code]` or an explanatory cast/protocol; do not add new bare ignores.
6. Add `pdm run typecheck`, compose it into `pdm run check`, teach `doctor` the tool, and add
   a local pre-commit hook. CI inherits the gate through its existing frozen
   `pdm run check`.
7. If Pyrefly requires a baseline, global suppression, or broad source exclusion to pass,
   reject it and rerun the contract with `mypy` plus Pydantic's official plugin.

## Impact Handshake Draft

- Address and Object: `pyproject.toml`, `pdm.lock`, `requirements.txt`,
  `scripts/doctor.py`, `.pre-commit-config.yaml`, and checker-driven fixes in shipped Python
  modules.
- State Diff: annotations are advisory and unchecked -> one locked semantic type contract is
  part of the canonical repository check.
- Operation: install/configure one checker, collect the real baseline, fix repository-owned
  errors, add narrow third-party overrides, then connect the green command to local and CI
  gates.
- Blast Radius Forecast: developer environment, pre-commit latency, CI duration, typed
  framework seams, and fixed built-in extensions.
- Invariants Check: no runtime behavior, database schema/data, provider configuration,
  Twitter backend, or extension membership changes.
- Verification: checker baseline reaches zero without global suppression; full repository
  contract and protected PR pass.
- Uncertainty: the 28 existing inline suppressions predate or sit alongside this task; the new
  generic-class suppressions are precise, but a later cleanup can independently audit whether
  every historical suppression is still necessary.

## User-Confirmed Constraints

- Sir permits introducing a type-checking gate.
- Sir explicitly started implementation on 2026-07-24.

## Verification Evidence

- `pdm run typecheck`: zero diagnostics across 127 project modules and 11,687 project lines
  under Pyrefly's default preset; 28 precise existing/new inline suppressions remain visible in
  the summary.
- `pdm run check`: foundation, lock, production requirements export, migration contract,
  formatting, lint, type checking, and all 101 tests pass.
- `pdm run pre-commit run --all-files`: all nine hooks pass, including the new Pyrefly hook.
- The production requirements export remains unchanged because Pyrefly is dev-only.
- The 215 Js2Py warnings are absent under a module/message/category-specific pytest filter;
  unrelated warnings remain visible.

## Next Step

Publish the branch as a draft PR, observe remote CI, and rotate the credential material removed
from the tracked Twitter helper because Git history remains affected.
