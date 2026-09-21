# Native Extension Distribution

Core stores one deployment row per exact Extension Release in `inkcre.extensions`: `name`,
`version`, `enabled[]`, `nickname`, `config`, and `config_schema`. Installation, peer enablement,
and process runtime remain distinct states. No first-party rows are seeded or synchronized.

For a new install or version change, Core requires an exact published Registry Release. Enabling
or cold-restoring an already-installed exact Release may consume a yanked Release, but missing or
blocked bytes leave the candidate unavailable without rewriting `enabled[]`.

Python acquisition uses the Release's same-origin `/simple/<normalized-project>/` association.
Core downloads one compatible exact wheel, then runs `pip install --dry-run --report` with that
wheel as the only available package source. The Core image owns the supported dependency baseline;
an Extension whose declared requirements are not already satisfied is rejected instead of
resolving or mutating dependencies during an HTTP request. Core then performs a normal
`sys.executable -m pip install` of only the Extension wheel into its virtual environment. The standard
`inkcre.core.extensions` entry point is discovered globally and every loaded Extension module is
verified against the installed wheel file record. There is no per-Extension target directory,
custom ZIP loader, module search-path rewrite, or runtime dependency-index access.

Any version change or rollback is rejected while any peer remains in `enabled[]`. Operators first
disable every peer, change the shared exact version, then re-enable peers. Replacing a wheel that
was already imported marks the process restart-required; Core does not hot-load the new class in
that process.

Peer enablement is mutated only by the atomic PostgREST function
`inkcre.set_extension_peer_enabled(p_name text, p_peer_id uuid, p_enabled boolean)`. Runtime start
precedes enable persistence. Runtime stop precedes disable persistence; if that persistence fails,
Core restarts the exact prior runtime while leaving durable intent unchanged.

The seven first-party Extensions are independent PEP 420 wheels with the standard entry-point group
and producer metadata in their `pyproject.toml`. That project version is the Python association's
Release authority and must equal the Extension Release Version shared by its Distribution
associations. Feature pull requests carry project-local Towncrier fragments and leave versions and
changelogs unchanged. After checked `main`, one generated Release PR consumes pending fragments,
applies each project's independent SemVer bump, and renders its changelog without publishing.
Repository orchestration owns project impact and next-version calculation；Towncrier owns fragment
validation and rendering。

The initial feature merge also wakes the publisher, but no project version has changed yet, so its
selection is a no-op. The Release PR merge runs repository checks against the generated release
state; only that checked `main` revision gives the existing publisher a new version to select and
publish. Leaving the Release PR open defers publication while later fragments update the same plan。

Repository CI discovers the producer set and rejects missing or invalid project intent。Publication
never runs from the Release PR。

The trusted pull-request preview controller reuses that same discovered producer set. Its dedicated
PDM `extension-preview` tooling group builds and verifies all seven wheels, then the released
`inkcre-extension-toolkit` projects one explicit Python inventory into a static sibling Registry.
The exact-head workflow run deploys that tree directly to the dedicated Cloudflare Pages project;
required checks neither upload nor hand off wheels or deployable Registry output. The facade exposes
only exact Release reads, PEP 503 Simple HTML, wheels, and PEP 658 metadata. It adds no Registry
runtime, mutable lifecycle, token, or Core-hosted static route.

Preview delivery treats a successful Pages deployment command as sufficient delivery evidence. It
passes the deterministic PR alias to Core without downloading every published file, comparing
bytes, bypassing caches, or waiting for edge convergence. Consumer acceptance remains a separate
manual or black-box activity and does not block the Heroku preview from starting.

`.github/workflows/extension-publish.yml` prepares the Python association with source provenance,
finalizes the newly built wheel using the released Toolkit's `python wheel finalize` command,
uploads through `/legacy/`, and publishes the exact Release. Automatic runs obtain `before_sha`
from the protected-main push and select only new projects or changed project versions;
unchanged matrix entries are explicit no-ops. The matrix and repository wheel checks consume the
same discovery result rather than separate project lists. An unprovable lineage or immutable
prepare conflict fails the job.

Preview and production both finalize before delivering the wheel. The installed runtime manifest belongs inside
`.dist-info/inkcre-extension.json`; Registry association metadata is not a replacement. The raw build output remains separate
from the finalized upload. Repairing a published wheel requires a new project version, not overwriting an old Release.

A checked commit may be older than current `main` only while it remains an ancestor. Immediately
before the first Registry mutation, each selected job fetches `main` again and requires its
artifact-input surface to be unchanged across `HEAD..origin/main`. A generated changelog-only or
different-Extension commit therefore does not discard a valid build; a later change to the same
artifact input stops the older job and leaves publication to the newer checked job.

`workflow_dispatch` selects one exact discovered producer and is an `INITIAL_ONLY` lane for a
version that does not yet exist. Because public
descriptors intentionally omit private producer provenance, a new workflow run cannot safely
resume an existing version: recovery must rerun the original Extension publication run so its
stable `github.run_id` build identity is preserved.

First-party global and Python documentation are static publication artifacts for the same exact
Release, not Core HTTP routes or wheel contents. Producer tooling obtains documentation addresses
from Registry and must not construct snapshot hosts from the Registry origin. The public deployment
currently routes a broad `*.inkcre.dev` wildcard to Registry so Heroku ACM's wildcard certificate can
serve `registry-docs-{snapshot}.inkcre.dev`; Registry then enforces the exact Host template and
returns 421 for other wildcard matches. Core deployment and Extension packages must not encode that
production DNS compromise or treat DNS/TLS success as proof that a documentation set exists.


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
