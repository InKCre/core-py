# Phase 4: `core-py` Rollout

## Purpose

Onboard `core-py` as the first consumer repo without breaking local readability or local ownership boundaries.

## Required Documents

### 1. Rollout Sequence

Must define step order for:

- finalizing the classification set for rollout
- creating the source subtree in `.github`
- exporting first mirrored docs
- landing the first sync PR in `core-py`
- validating local and mirrored paths

### 2. Local Path Transition Note

Must define:

- which existing `core-py/docs` files are removed, replaced, or relocated
- which files stay local
- which files are renamed into `30-unit-tdd`

### 3. Verification Checklist

Must define checks for:

- clone readability
- mirrored provenance visibility
- unchanged local docs
- valid README and AGENTS links after rollout

### 4. Rollback Plan

Must define:

- what to do if first sync produces wrong file ownership
- whether rollback happens in `.github`, `core-py`, or both
- how to restore local docs if a split decision was wrong

## Recommended Rollout Principle

Move the smallest safe set first.

That likely means:

- one or a few clearly product-scope docs
- no mixed files until split decisions are accepted

## Review Questions

- Which files are safe for the first rollout batch?
- Should `AGENTS.md` and `README.md` be updated in the same PR or a follow-up PR?
- Do we need a temporary compatibility note for old paths?

## Exit Criteria

- one accepted rollout sequence
- one accepted verification checklist
- one accepted rollback path
