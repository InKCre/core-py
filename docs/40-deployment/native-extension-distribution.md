# Native Extension Distribution

Core stores one deployment row per exact Extension Release in `inkcre.extensions`: `name`,
`version`, `enabled[]`, `nickname`, `config`, and `config_schema`. Installation, peer enablement,
and process runtime remain distinct states. No first-party rows are seeded or synchronized.

For a new install or version change, Core requires an exact published Registry Release. Enabling
or cold-restoring an already-installed exact Release may consume a yanked Release, but missing or
blocked bytes fail closed without rewriting `enabled[]`.

Python acquisition uses the Release's same-origin `/simple/<normalized-project>/` association.
Core downloads one compatible exact wheel, then runs `pip install --dry-run --report` with that
wheel as the only available package source. The Core image owns the supported dependency baseline;
an Extension whose declared requirements are not already satisfied fails closed instead of
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
Release authority. One Changie project per producer owns the generated version entry, changelog,
and mechanical `pyproject.toml` replacement; it does not publish. Repository CI discovers the
producer set and rejects missing Changie coverage, generated-state drift, invalid fragments, or an
artifact-input change that does not advance the version. A changelog-only correction is explicitly
outside the artifact-input surface.

`.github/workflows/extension-publish.yml` prepares the Python association with source provenance,
uploads through `/legacy/`, and publishes the exact Release. Automatic runs obtain `before_sha`
from the verified CI check suite and select only new projects or changed project versions;
unchanged matrix entries are explicit no-ops. The matrix and repository wheel checks consume the
same discovery result rather than separate project lists. An unprovable lineage or immutable
prepare conflict fails the job.

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
