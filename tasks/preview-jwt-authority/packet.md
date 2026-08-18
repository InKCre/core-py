# Preview JWT Authority

## Objective

Make the repository-level `JWT_SECRET` the single signing-key authority for canonical
production and same-repository pull-request previews.

## Guardrails

- The secret value remains outside Git, logs, artifacts, and workflow summaries.
- Core and PostgREST receive the same exact value.
- Preview provider authorization and database-role passwords remain environment-specific.
- JWT format, claims, database admission, and application behavior do not change.

## Verification

- Workflow contract tests prove Preview reads `secrets.JWT_SECRET` directly.
- No source or durable documentation references `PREVIEW_JWT_SEED` or the derivation script.
- The full repository contract passes.
- GitHub exposes the expected repository Secret name without exposing its value.
- PR 52 Core and PostgREST converge to the Keychain-held value and pass the PostgREST
  authenticated/wrong-secret/anonymous transport probe.

## Current Truth

- Production already consumes repository-level `secrets.JWT_SECRET` because the production
  environment does not shadow that name.
- Preview currently consumes environment-level `PREVIEW_JWT_SEED` and derives a per-PR key.
- The deployment owner has selected one shared key and authorized local Keychain storage.
- The repository Secret, Production Core/PostgREST, PR 52 Core/PostgREST, and the browser
  Preview setting have been converged to the selected key without exposing it in Git.
- Local focused and full repository contracts pass. The live PostgREST transport probe is
  independently blocked because PR 52 intentionally uses the pre-Peer Client schema while
  the current preview controller unconditionally invokes the newer Peer advertisement script.
- The compatibility fix keeps Peer convergence mandatory for capable images and skips only
  images that prove they do not contain `scripts/configure_peer_runtime.py`; health and
  authenticated PostgREST probes remain mandatory in both cases.

## Next Step

Verify and admit the narrow preview-controller compatibility fix to `main`, rerun PR 52
Preview initialization, and verify the live authenticated transport against the Client
baseline.
