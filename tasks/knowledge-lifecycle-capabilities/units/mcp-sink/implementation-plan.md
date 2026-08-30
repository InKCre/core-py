# MCP Sink Implementation Plan

> Proposed execution baseline after the accepted product、technical and acceptance design。This plan does not authorize
> source implementation；implementation begins only after preflight、Impact Handshake and explicit Human approval。

## Delivery Topology

```text
ext-reg Runtime source
  -> release runtime-core-py
  -> core-py pins the exact released wheel
  -> core Extension Host adopts monotonic type publication
  -> core Sink domain + MCPSink
  -> preview MCP endpoint
  -> deterministic MCP journeys
  -> manual ChatGPT + Secure MCP Tunnel journey
```

The Runtime release is a real upstream dependency，not a local patch copied into core-py。The two repositories therefore use
separate feature branches and PRs。core-py may prepare against a locally built Runtime while iterating，but its reviewable and
accepted dependency must be the exact independently released wheel。

## Workstream A — Simplify Extension Runtime Publication

Owner：`../ext-reg/runtimes/core-py`。

1. Create a dedicated feature branch from current `origin/main`；do not reuse the unrelated
   `feat/extension-setup-wizard-complete` branch。
2. Replace snapshot/diff/restore publication with an exact active-effect record：
   - retain the exact FastAPI routes published by this startup；
   - retain exact Peer inbound capability IDs published by this startup；
   - retain the public HTTP route claim；
   - retain contributed Source classes only long enough to perform the explicit catalog sync。
3. Make Source、Resolver and future Sink Python type registration process-monotonic：
   - startup may register types；
   - disable/failed startup does not attempt to restore an earlier registry；
   - an imported exact Extension version remains a restart boundary。
4. Withdraw only active runtime effects during stop：remove exact routes，unregister exact Peer inbound capability IDs，release
   public-route claims，then let `on_close()` release Extension-owned resources。
5. Reduce `DistributionModules` to ordinary entry-point loading plus Distribution-origin verification。Delete simulated
   `sys.modules` unload/restore behavior；do not replace it with another module cache abstraction。
6. Update Runtime contracts and admitted behavior-boundary coverage for the observable enable/disable/re-enable lifecycle。
   Do not add snapshot/map/sys.modules implementation tests。
7. Add one Runtime Changie fragment，run the ext-reg repository contract，publish the next `runtime-core-py` version through
   the existing independent package release workflow。

### Runtime invariants

- Disabling an Extension removes its reachable routes and advertised Peer capabilities。
- Resolver/Source/Sink classes already imported into the process remain registered but inert。
- A startup failure can leave inert type registrations；ordinary diagnostics report the startup failure，and restart is the
  reset boundary。
- One Extension teardown cannot remove another Extension's routes or Peer inbounds。

## Workstream B — Adopt the Runtime Contract in core-py

Owner：`core-py`。

1. Pin the exact newly released Runtime wheel and refresh `pdm.lock`。
2. Remove `snapshot_*` / `restore_*` helpers from SourceManager、ResolverManager and PeerManager。Keep
   `PeerManager.unregister_inbound(capability)` as the explicit active-effect withdrawal primitive。
3. Align the Core facade and Extension Host stop/failure paths with the released Runtime API；remove unload/rollback calls that
   no longer exist，without duplicating the Runtime's lifecycle implementation locally。
4. Update the local Extension Unit guide and any affected deployment/design prose from reversible type publication to
   monotonic type registration + reversible active effects。
5. Verify an existing real Extension can enable、disable and re-enable in one process，with its Resolver type still present
   while disabled and its route/inbound absent。

## Workstream C — Persisted Sink Domain

Owner：`core-py`。

### Database contract

Add one forward Alembic migration and matching SQLModel metadata：

```text
sink_types
  id            text primary key
  description   text not null
  config_schema jsonb not null default '{}'

sinks
  id       bigint identity primary key
  type     text not null -> sink_types.id
  nickname text null
  config   jsonb not null default '{}'
  enabled  uuid[] not null default '{}'
```

There is no Sink `state`，path，protocol，transport or runtime-status column。Runtime presence remains process-local；
`enabled` is deployment intent scoped by PeerRef，following the established Extension/Peer pattern。

### Python domain

1. Add `SinkBase[ConfigT]`：
   - exact Sink type ID and Pydantic config contract are registered on subclass definition；
   - one instance receives its persisted Sink model；
   - `on_start(app)` and `on_close()` own that instance's active resources。
2. Add `SinkManager`：
   - type registration and explicit catalog sync；
   - list/get/create/delete/config update；
   - enable/disable for the current Peer；
   - cold-start enabled instances，close running instances，and one process-local running map；
   - persist enable/disable intent first，then start/stop the local runtime；runtime failure stays observable and does not
     rewrite owner intent。
3. Do not add generic delivery、reconcile、watcher、restart、transport or rollback abstractions。
4. Add the minimal Peer-JWT-protected management routes needed by an operator/client：type list，Sink CRUD/config，enable and
   disable。The MCP endpoint itself is not placed under the Peer-JWT router。
5. Bootstrap order：register core Sink classes -> sync Sink type catalog -> start enabled Sinks after Extensions are started
   and before final Peer publication/readiness。Shutdown closes Sinks before Extension teardown so a running Sink cannot
   observe disappearing Extension-owned behavior mid-close。

### Instance lifecycle branches

- Config may be persisted while disabled。
- Enabling an already-running instance is idempotent。
- Disabling a non-running local instance clears only this Peer's durable intent。
- Config update validates through the Sink type contract；a running MCPSink receives the new validated config without route
  replacement when only its PAT changes。
- Deleting an enabled or locally running Sink is rejected as an ordinary state conflict；the caller disables it first。
- Cold-start failure preserves `enabled` intent and logs the exact Sink ID/type failure。

## Workstream D — MCPSink Protocol Runtime

1. Add the official MCP Python SDK v2 as a bounded dependency from the verified `2.1.1` line。Use its high-level
   `MCPServer`，not a custom JSON-RPC implementation；the lockfile remains the exact build authority。
2. Register one built-in exact type，`core.mcp.v1`，with config `{ "pat": string }`。
3. For one running instance，construct exactly one MCP server and Streamable-HTTP ASGI app：
   - mount parent `/sinks/{sink_id}` with the SDK child route `/mcp`，realizing exact path `/sinks/{sink_id}/mcp` without a
     trailing-slash redirect；
   - stateless HTTP and JSON responses；
   - parent lifespan enters the SDK session manager because mounted sub-app lifespan is not run by FastAPI；
   - a small pure-ASGI bearer-PAT wrapper protects only this Sink endpoint；do not use Peer JWT、OAuth server machinery or
     `BaseHTTPMiddleware`。
4. Mount/unmount the exact retained route on start/close。A re-enable constructs a fresh SDK runtime and session manager。
5. Publish exactly seven stable Tools，Resource templates/reads for Block content，and the accepted fixed Skills extension
   subset (`io.modelcontextprotocol/skills` with `skills/list` and `skills/get`)。
6. Package one static English `use-inkcre` Skill。Its content teaches the Block/Relation/Resolver/Storage info-base model and
   the meta-cognition that InKCre can supply evidence to productive work；it does not prescribe tool recipes or retrieval-mode
   syntax。

## Workstream E — MCP Application Adapters

Keep the Agent-facing surface fixed：

```text
inkcre_recall
inkcre_open_entities
inkcre_read_blocks
inkcre_expand_entities
inkcre_find_path
inkcre_resolver_methods
inkcre_invoke_resolver_methods
```

1. Build thin adapters over the existing LexicalRetrievalManager、SemanticRetrievalManager、Block/Relation managers and
   GraphNavigationRetrievalManager。Do not route these calls through internal HTTP APIs。
2. Apply the accepted ordered batch contract：one correlated result atom per admitted input；natural payload proves success；
   only failures contain one of `not_found | invalid_arguments | unavailable | failed`；one atom cannot cancel siblings。
3. `inkcre_recall` runs requested retrieval modes independently，deduplicates by entity reference，and preserves each mode's
   native evidence。It does not invent a cross-mode score or ranking。
4. `inkcre_open_entities` and graph tools return presentation-neutral Block/Relation facts with bounded context。
5. `inkcre_read_blocks` selects `raw | hydrated | solved` once per call：
   - raw is persisted `Block.content` and includes Storage metadata when present；
   - hydrated uses ordinary Storage hydration；
   - solved uses the exact Resolver contract；
   - bounded text/JSON may be embedded，while oversized or binary values use deterministic live Resource URIs；
   - one common recursive projector preserves typed solved facts and replaces nested bytes with Resource content rather than
     base64 JSON。
6. Resource reads lazily re-read current Block/Storage/Resolver authority。Do not persist Resource rows、sessions or caches。
   The initial inline text/JSON budget is the preflighted non-configurable 64 KiB UTF-8 constant；it is a context policy，not
   an MCP limit or Agent argument。
7. Resolver method discovery：
   - resolve exact Resolver classes from non-empty `blocks` first，otherwise from supplied `resolvers`；
   - group Blocks by Resolver ID；
   - consider public bound `get_*` / `read_*` methods only；
   - include a method only when its non-`self` input can be represented as Agent-supplied JSON Schema and it has no runtime
     dependency such as `sqlmodel.Session`；
   - derive input validation from a generated Pydantic model，with no decorator、allowlist or Extension adapter。
8. Invocation resolves each Block's ordinary Resolver instance，validates arguments through the derived Pydantic model，and
   calls the bound method。Project returned values through the same structured-content/Resource boundary as Block reads。

## Workstream F — Operator Companion and ChatGPT Path

1. Document the minimal Secure MCP Tunnel invocation that exposes one remotely reachable MCP URL while injecting the Sink
   PAT。Keep tunnel deployment/operator configuration outside business code。
2. Document ChatGPT Developer Mode connection and **Scan Tools** Skill snapshot import as a manual acceptance path，not a
   second product API or runtime Skill fetch contract。
3. Do not add legacy `ai-plugin.json` or a ChatGPT-specific business adapter unless preflight disproves current MCP support。

## Workstream G — Verification and Delivery

1. Run narrow static/type/migration checks while iterating，then `pdm run check` in core-py and the declared ext-reg contract。
2. Execute the accepted deterministic Journeys A–D and F with an independent MCP client against a real local endpoint and
   dedicated corpus。Keep the first realization as a manual/scripted acceptance asset；do not promote it to CI merely because
   it exists。
3. Deploy the core-py feature branch/PR to preview and repeat the transport/content subset against the deployed endpoint。
4. Execute Journey E manually through Secure MCP Tunnel + ChatGPT，record observed behavior without asserting one model/tool
   sequence。
5. Update task truth and only the durable owners implicated by the implementation。Extension lifecycle correction belongs in
   local Runtime/Core technical docs；shared product truth is updated through the Hub-first workflow if implementation exposes
   missing cross-unit semantics。

## Preflight Gates Before Impact Handshake

The following questions are evidence gates，not open product decisions：

1. Confirm the official SDK v2 mount/lifespan/auth wrapper behavior with a minimal disposable spike，including disable and
   fresh re-enable。
2. Confirm the SDK representation accepted by a real MCP client for bounded image/audio content and Resource links；freeze
   one conservative inline text/JSON budget，then keep the native-media-versus-Resource choice isolated for the real Host
   acceptance path。
3. Enumerate actual Resolver `get_*` / `read_*` signatures from core and installed Extensions，then prove the Pydantic schema
   filter includes useful methods and excludes runtime dependencies such as `get_existing(db_session)`。
4. Enumerate solved-content return shapes，including nested bytes，and prove one common projector can preserve them without
   Resolver-specific MCP code。
5. Select and record the real acceptance corpus and exact Extension Resolver method used in Journey D。
6. Confirm current MCP/ChatGPT Skills extension behavior and Secure MCP Tunnel invocation from primary sources/current tools。
7. Dry-run the ext-reg release -> core wheel pin dependency sequence and verify each PR can be reviewed independently。

If a gate disproves an accepted contract，return to design with the exact evidence。Otherwise produce the Impact Handshake and
wait for explicit “开始”。
