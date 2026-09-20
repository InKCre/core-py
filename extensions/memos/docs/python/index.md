---
description: Install, configure, and operate the Python Memos Extension.
---

# Memos on Core

The Python Distribution exposes the Memos-compatible backend under the selected Core's `/memos`
route. Its configuration has one nullable field, `personal_access_token`. A configured token is
`memos_pat_` followed by exactly 32 ASCII letters or digits. A null value does not authorize any
client's protected requests.

Use the existing `core.extension.management.v1` capability to apply a `patch_config` command to
`inkcre/memos`, then `enable` on the intended Core. Configuration can be saved before enablement.
The Core validates the complete resulting config, persists it, and updates the live Extension.
Do not assume a direct database edit updates the running service.

The PAT is deployment configuration, not an OAuth session or a user-account token store. Replacing
or revoking it takes effect on subsequent protected requests and affects every connected client.
Keep it out of logs, URLs, screenshots, and public documentation artifacts.

Set Core's `http_public_base_url` to the externally reachable base URL. The client-facing server
address appends `/memos`; a deployment mounted below a base path must retain that path. HTTPS
termination and any necessary forwarding remain deployment responsibilities. The Extension does
not create tunnels or make a private address reachable from a phone.

For a non-mutating authentication check, request `GET /memos/api/v1/auth/me` with the PAT as a Bearer
token. This proves the route and token work from that caller, not that every Memos client is
compatible. The public instance profile does not require a PAT and is not an authentication check.

Enablement mounts the Extension's routes; disablement withdraws them. Installation, the per-Peer
enabled intent, and the running process remain separate states. Runtime and graph implementation
details are maintained in the producer's Memos Unit TDD, not duplicated in this operator guide.
