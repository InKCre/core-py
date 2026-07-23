# Dependency Security And Actions Runtime Packet

## MVT Core

- Objective & Hypothesis: eliminate the 59 open GitHub Dependabot alerts reported for
  `requirements.txt` and remove the GitHub Actions Node 20 deprecation warning without
  changing product behavior. The working hypothesis is that the exported requirements and
  PDM lock are stale enough to retain vulnerable transitive versions, and that a reviewed
  lock refresh plus an official PDM setup-action upgrade can restore a green, reproducible
  dependency baseline.
- Guardrails Touched: `pdm.lock` remains the Python dependency authority and
  `requirements.txt` remains a byte-checked production export; Python stays on 3.12 and PDM
  stays pinned unless evidence requires a deliberate toolchain change; the application,
  migration graph, production data, Heroku configuration, and Neon topology are out of
  scope; no vulnerability is dismissed merely to reduce the alert count.
- Verification: reproduce the alert inventory through GitHub's Dependabot API; resolve every
  vulnerable package to a patched locked version; prove lock/export consistency; run the
  full repository, migration, settings, pre-commit, and OCI/fresh-database checks; confirm
  GitHub reports zero open alerts for the merged production manifest; confirm Actions no
  longer emits the Node 20 warning.

## Current Understanding

- GitHub reports exactly 59 open alerts: 2 critical, 17 high, 23 medium, and 17 low.
- Every alert is in the `pip` ecosystem and points to `requirements.txt`; no other manifest
  currently contributes to the count. The export exactly matches `pdm.lock`, so the problem
  is genuinely vulnerable locked versions rather than manifest drift.
- The alerts collapse to a small vulnerable package set led by `aiohttp` (29 alerts) and
  `litellm` (11 alerts), plus Mako, Starlette, filelock, idna, msgpack,
  pydantic-settings, python-dotenv, requests, and urllib3.
- The checked-in workflows use `pdm-project/setup-pdm@v4` in three places. That tag declares
  `runs.using: node20`; official tag `v4.5` declares Node 24 and preserves every input used by
  this repository.
- `litellm` is a direct dependency but has no source import. `libs/ai.py` uses the OpenAI SDK
  directly, while the local guide's LiteLLM claim is stale.
- Starlette cannot be patched within the current FastAPI `0.116.x` constraint. FastAPI
  `0.139.2` supports the patched Starlette `1.3.1`, but the cross-version upgrade requires
  middleware, routing, OpenAPI, and runtime smoke verification.
- Starlette `1.3.1` deprecates using the legacy `httpx` package for `TestClient`; `httpx2`
  belongs in the development group so tests exercise the maintained client without changing
  the production graph.
- GitHub's official dependency review action `v5.0.0` uses Node 24 and can reject newly
  introduced High/Critical runtime or development vulnerabilities on pull requests without
  making local hermetic checks network-dependent.
- `portless.json` is unrelated user work and must remain untracked and unstaged.

## User-Confirmed Constraints

- Sir explicitly approved resolving all 59 dependency vulnerabilities.
- Sir explicitly approved upgrading the action that triggers the Node 20 warning.
- The prior hard-cut authorization does not broaden this packet into database, runtime, or
  product changes.

## Active Mode

Execute: the advisory-to-package map, compatible security floors, unused LiteLLM dependency,
FastAPI/Starlette compatibility boundary, and official setup action upgrade are now
evidence-backed.

## Diagnostics Matrix

| Observation | Leading hypothesis | Required evidence |
|---|---|---|
| 59 alerts all point to `requirements.txt` | One synchronized but outdated lock/export fans out into many advisories | Compare locked versions with every advisory's first patched version |
| Most alerts cluster in `aiohttp` and `litellm` | A small direct upgrade set may remove most alerts | Resolve dependency graph and compatible latest versions |
| Several transitive packages are vulnerable | Direct pins may not be necessary | Prove a normal PDM resolution selects patched transitive versions |
| `setup-pdm@v4` emits Node 20 warning | The action needs a new official major/runtime | Verify upstream release/runtime metadata and migration notes |

## Scope And Invariants

- Target surfaces:
  - `pyproject.toml`
  - `pdm.lock`
  - `requirements.txt`
  - `.github/workflows/ci.yml`
  - `.github/workflows/openapi-doc.yml`
  - `.github/workflows/branching-database.yml`
  - dependency-security CI policy if justified by the diagnosis
- Explicit exclusions:
  - application feature changes
  - schema or migration revision changes
  - Heroku and Neon mutations
  - blanket Dependabot dismissals
- Invariants:
  - frozen production install succeeds
  - the production export exactly matches the lock
  - one supported Python minor remains authoritative
  - CI and local checks exercise the same dependency graph

## Next Step

Remove the unused LiteLLM dependency, raise direct security floors, upgrade FastAPI across
the Starlette compatibility boundary, resolve one coherent PDM lock/export, and move the
three PDM setup steps to official Node 24 tag `v4.5`. Add a pull-request dependency review
gate for recurrence prevention.

## Execution Evidence

### Resolved dependency graph

- Removed unused `litellm` from both `pdm.lock` and the production requirements export.
- Resolved every reported vulnerable package at or above its highest required fixed version:
  - `aiohttp 3.14.3`
  - `filelock 3.32.0` (development only after LiteLLM removal)
  - `idna 3.18`
  - `Mako 1.3.12`
  - `msgpack 1.2.1`
  - `pydantic-settings 2.14.2`
  - `python-dotenv 1.2.2`
  - `requests 2.34.2`
  - `Starlette 1.3.1`
  - `urllib3 2.7.0`
- FastAPI resolved to `0.139.2`; the full suite exercises the new Starlette boundary.
- Added development-only `httpx2 2.8.0`, removing the new Starlette TestClient deprecation
  without adding it to the production export.

### Actions runtime and recurrence guard

- All three PDM setup steps now use official `pdm-project/setup-pdm@v4.5`; its checked
  `action.yml` declares `runs.using: node24`.
- Pull requests run official `actions/dependency-review-action@v5.0.0`, also on Node 24, and
  reject newly introduced High/Critical vulnerabilities in runtime or development scope.

### Local verification

- `pdm install -G dev --frozen-lockfile`
- `pdm run check`: 97 tests passed in addition to foundation, migration, and settings checks.
- `pdm run pre-commit run --all-files`
- `python -m pip check`
- exact lock/export consistency checks
- static assertions for every Dependabot security floor
- controlled OpenAPI generation with a synthetic configuration

### Pull-request verification

PR #25 verified commit `03852ac991ace2680a06525a24c423ceaaf7287b`:

- `Dependency security review`: passed; the requirements diff introduced no known
  High/Critical vulnerability.
- `Hermetic repository contract`: passed on `setup-pdm@v4.5`.
- `Portable artifact and fresh database`: passed.
- `Provision and migrate`: passed against the PR's Neon branch.
- Workflow logs contain no Node 20 deprecation warning. The only setup-step warning was a
  harmless cache-save race with another job using the same cache key.

The remaining proof is promotion to the default branch followed by a fresh Dependabot query
and the normal production delivery checks for that exact `main` commit.
