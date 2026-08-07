# Semantic-retrieval acceptance corpus

This directory owns only human-readable acceptance authority. `manifest.json` describes producer inputs, symbolic aliases,
quality judgments and source provenance. The harness resolves aliases to actual database IDs only after the real Memos,
RSS/Atom and HTML/storage paths create their graphs. Alias strings must never enter production schemas, models, payloads or
domain APIs.

`sqlite-architecture.html` is a pinned snapshot of SQLite's official Architecture document. SQLite states that its code and
documentation are dedicated to the public domain. The manifest records the retrieval date, source URL, provenance URL and
SHA-256 digest so a future refresh is an explicit review rather than an invisible network dependency.

Generated graph rows, vectors and provider responses are not corpus authority and must not be committed.
