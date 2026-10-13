# First-Party Extension Distribution

Core stores one deployment row per exact Extension Release in `inkcre.extensions`: `name`,
`version`, `enabled[]`, `nickname`, `config`, and `config_schema`. Installation, peer enablement,
and process runtime remain distinct states. No first-party rows are seeded or synchronized.

For a new install or version change, Core requires an exact published Registry Release. Enabling
or cold-restoring an already-installed exact Release may consume a yanked Release, but missing or
blocked bytes leave the candidate unavailable without rewriting `enabled[]`.

Python acquisition uses the Release's same-origin `/simple/<normalized-project>/` association.
Every enable or cold restore first reads the exact Registry Release, checks its lifecycle state and
Host SDK association, then discovers the exact record already installed in the Core interpreter.
Core reuses that Distribution only when its Project, entry point and Host SDK match the current
Registry association. A damaged or conflicting installed record fails; it is not silently replaced.
A missing record enters the independently released Runtime SDK acquisition path.

The frozen Runtime SDK 0.1.5 downloads one compatible exact wheel without resolving dependencies
from Registry, then performs ordinary `sys.executable -m pip install` in the Core virtual environment.
That install may resolve Python dependencies from pip's package index; this SDK version has no
`--dry-run` dependency preflight or no-dependency-mutation guarantee. Exact installed-record reuse
skips this repeated acquisition and installation but does not change the miss path's policy.
The standard `inkcre.core.extensions` entry point is discovered globally and every loaded Extension
module is verified against the installed wheel file record. There is no per-Extension target
directory, custom ZIP loader or module search-path rewrite. Registry failure or a blocked Release
still prevents restoration even when its Distribution is installed; installed yanked Releases retain
their existing warning and admission behavior.

Any version change or rollback is rejected while any peer remains in `enabled[]`. Operators first
disable every peer, change the shared exact version, then re-enable peers. Replacing a wheel that
was already imported marks the process restart-required; Core does not hot-load the new class in
that process.

Peer enablement is mutated only by the atomic PostgREST function
`inkcre.set_extension_peer_enabled(p_name text, p_peer_id uuid, p_enabled boolean)`. Runtime start
precedes enable persistence. Runtime stop precedes disable persistence; if that persistence fails,
Core restarts the exact prior runtime while leaving durable intent unchanged.

The seven first-party Extensions remain independent PEP 420 wheels with the standard entry-point
group and producer metadata in their `pyproject.toml`. Feature pull requests carry project-local
Towncrier fragments and leave versions and changelogs unchanged. After checked `main`, one generated
Release PR consumes pending fragments, applies each project's independent SemVer bump, and renders
its changelog without publishing. `scripts/release.py`, Towncrier, and the Extension `pyproject.toml`
remain the version authority. Web producer metadata is generated from that Core version when the
candidate is captured; Web Changesets continue to own the app and SDK versions.

The initial feature merge wakes the publisher, but no Extension version has changed yet, so the
selection is a no-op. The Release PR merge runs repository checks against the generated release
state; only that checked `main` revision gives the publisher a new version to select. Leaving the
Release PR open defers publication while later fragments update the same plan. Publication never
runs from the Release PR.

The trusted pull-request preview controller continues to build and verify the discovered Core wheel
set and deploy its static sibling Registry. The facade exposes only exact Release reads, PEP 503
Simple HTML, wheels, and PEP 658 metadata. It adds no Registry runtime, mutable lifecycle, token, or
Core-hosted static route. Preview delivery passes the deterministic PR alias to Core; consumer
acceptance remains a separate browser or black-box activity.

`.github/workflows/extension-publish.yml` selects changed Core Extension versions, checks the exact
Core source, and checks out Web `main` once to fix its source SHA. It saves one plan containing both
SHAs, the selected versions, and every full `PrepareReleaseRequest`. Web's candidate builder matches
those Release names against its own producer manifests, writes the agreed version into each matching
Web package, builds and verifies the Module Federation snapshot, and saves the ZIP and digest into
the same candidate. A matching Web producer must produce its snapshot successfully; an Extension
without a Web producer remains Python-only. Core builds and verifies finalized wheels, then checks
that every declared association has matching saved bytes and provenance. The Runtime SDK install
manifest remains inside `.dist-info/inkcre-extension.json`; Registry association metadata does not
replace it.

The candidate artifact is saved before Registry writes and retained for 90 days. Capture fixes the
Core event revision and the Web checkout from `main` in the candidate plan. The protected production
job restores those exact bytes, checks their source identities, workflow-run identity, associations,
and digests, prepares every selected Release with all of its associations, uploads all
Distributions, and only then publishes each Release. A retry reruns the publish job from the
original workflow run and candidate; it does not rebuild from current `main` or create a second
version decision. An expired or ambiguous candidate fails closed. `workflow_dispatch` remains an
`INITIAL_ONLY` lane for one exact Extension
version that has not yet been published.

First-party global and Python documentation are static publication artifacts for the same exact
Release, not Core HTTP routes or wheel contents. Producer tooling obtains documentation addresses
from Registry and must not construct snapshot hosts from the Registry origin. The public deployment
currently routes a broad `*.inkcre.dev` wildcard to Registry so Heroku ACM's wildcard certificate can
serve `registry-docs-{snapshot}.inkcre.dev`; Registry then enforces the exact Host template and
returns 421 for other wildcard matches. Core deployment and Extension packages must not encode that
production DNS compromise or treat DNS/TLS success as proof that a documentation set exists.

`.github/workflows/extension-documentation-publish.yml` is the protected manual publication lane
for first-party producer documentation. It builds every scope under the selected producer with the
pinned shared VitePress toolchain, reads the current scope ETags, and saves complete Toolkit
candidates before any Registry write. The publish job restores those exact candidates, revalidates
their source against current `main`, publishes them, and checks their public snapshot origins.
Recovery reruns only the failed publish job; rerunning all jobs is rejected because it would create
new snapshot identities. Candidate artifacts are retained for 90 days.

Official production publication and deployment jobs require
`github.repository == 'InKCre/core-py'`. A fork may build and test normally, but it cannot enter the
official production environment merely because its `main` branch published an artifact. Fork
owners deploy through the explicit Render or Heroku self-host workflow instead.


## Async Host compatibility window

Core Host 0.2 uses Runtime SDK async startup and persistence capabilities. Host operations and
Extension config/state mutations must be awaited; in-memory config projection and typed mutation
callbacks remain synchronous. ExtensionStateService owns each short business transaction;
app/persistence/extension owns SQL and session creation. Row locks serialize state transforms, and
the shared enabled RPC retains ownership of enabled[].

Registry-origin database reads finish before Registry HTTP and wheel acquisition. The existing
blocking artifact clients run in a worker without a database session. Startup failure or cancellation
withdraws the current publication and releases its runtime claim.

Core Host SDK 0.3 adds `app.http.get_public_http_base_url()` without changing the async lifecycle
or persistence API. Its authority is `app/version.py`, independently of the Core service package
version in `pyproject.toml`; preparing a service Release PR does not change the Host SDK version.

GitHub, Learn English, Mail, RSS, Telegram, and Twitter retain their SDK 0.2 lower bound and support
SDK 0.3 through `>=0.2.0 <0.4.0`. Memos uses the new HTTP address API and requires
`>=0.3.0 <0.4.0`. Compatibility metadata changes require new immutable Extension
releases; an old wheel's range must not be widened. Before upgrading a deployment, disable affected
old Extensions, adopt the matching Core/Extension releases, restart where a loaded wheel was replaced,
and then enable them. A persisted old enabled[] intent is not silently removed on failed cold restore.
For Extensions with both Python and Module Federation distributions, prepare both at the same new
Extension version, even when the browser code is unchanged. Do not upgrade only the Python
association and lose the browser distribution required by the installed Extension. Compatible
artifacts must be available before the deployment upgrade.
