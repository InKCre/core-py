# MCP Sink Preflight

> Evidence collected after the accepted product、technical、acceptance and execution baselines。This file records
> implementation-readiness evidence；it does not authorize source mutation。

## Result

The unit is ready for Impact Handshake。No accepted product or technical boundary was disproved。The preflight did refine
several implementation details：

- use the official MCP Python SDK `2.1.1` line and its `MCPServer` / Streamable-HTTP ASGI support；
- mount the child ASGI application at `/sinks/{sink_id}` while its SDK route remains `/mcp`，which realizes the exact public
  endpoint `/sinks/{sink_id}/mcp` without redirecting to a trailing slash；
- enter every running MCPSink's SDK session manager from the parent FastAPI lifespan；mounted sub-application lifespan is not
  entered automatically；
- wrap only the mounted MCP ASGI application with a small bearer-PAT ASGI callable；
- implement OpenAI's exact static Skills-import subset，not a general SEP-2640 implementation；
- use the RSS Extension and the official MCP Python SDK release Atom feed as the deterministic Extension-Resolver corpus；
- keep binary/oversized Resource delivery a live projection and let the real ChatGPT journey determine whether native
  image/audio content or a Resource link is the better Host realization。

## Gate Evidence

| Gate | Evidence | Resolution |
| --- | --- | --- |
| SDK mount/lifecycle | A disposable `mcp==2.1.1` ASGI spike exercised initialize、`tools/list`、tool call、Resource read、PAT rejection、route removal and fresh re-enable through the official client。The SDK documentation requires the parent lifespan to enter `session_manager.run()`。 | Pass。One fresh SDK server/session manager per enable cycle；no reusable session abstraction。 |
| Exact endpoint | Starlette mounting directly at `/sinks/{id}/mcp` either redirects to a trailing slash or misses when slash redirects are disabled。Mounting at `/sinks/{id}` with child route `/mcp` serves the accepted URL exactly。 | Pass。Retain/remove the parent `Mount` route as the Sink's active effect。 |
| Result content types | The official client accepted text、native image content and Resource links。MCP defines text、image、audio、embedded Resource and Resource link content blocks。OpenAI Plugin documentation guarantees model-readable `content` / `structuredContent` but does not document a universal tool-result byte ceiling or promise one exact Resource-link expansion behavior。 | Protocol pass；Host choice remains Journey C/E evidence。Start with a non-configurable **64 KiB UTF-8 inline budget per text/JSON content atom**；larger or generic binary values become Resource links。Do not make the threshold an Agent argument。 |
| Resolver reflection | Core plus installed Extension registration yielded 24 exact Resolver types。Public typed `get_*` / `read_*` methods produce Pydantic JSON Schema；`get_existing(db_session: sqlmodel.Session)` is rejected by schema derivation。Untyped overrides are omitted rather than patched for MCP。 | Pass。No Resolver decorator、allowlist or Extension adapter。 |
| Solved-content projection | Existing results include primitives、Pydantic/SQLModel models、frozen byte-content dataclasses、tuples and nested Mail solved models。They are finite typed values；bytes are the only value requiring content extraction。 | Pass。One recursive MCPSink projector handles Pydantic models、dataclasses、containers、scalars and bytes；unknown non-projectable values produce the ordinary per-atom `unavailable` result rather than stringification。 |
| Extension corpus | `extensions.rss.feed.v1` and `extensions.rss.feed_item.v1` provide real typed overridden `get_text` / `get_label` behavior。`https://github.com/modelcontextprotocol/python-sdk/releases.atom` is public、relevant and exercises the Extension's ordinary producer/resolver path。 | Pass。Journey D invokes an RSS Resolver override；it does not require a Resolver-specific method invented for acceptance。 |
| Skills import | OpenAI's current Plugin documentation explicitly supports a bounded static subset of draft SEP-2640 during **Scan Tools**：`capabilities.extensions["io.modelcontextprotocol/skills"]`、`skills/list`、`skills/get`、`resources/read` and SHA-256 resource digests。Imported Skills are snapshots in the Plugin draft，not runtime reads。 | Pass。Publish exactly one static `use-inkcre` Skill and no general Skills framework/archive/update API。 |
| Secure MCP Tunnel | Official Tunnel configuration supports an HTTP MCP target and static extra headers sourced from environment/file configuration。Those headers are attached only to the configured MCP origin。 | Pass。The operator companion injects `Authorization: Bearer <PAT>`；business code gains no Tunnel/OAuth branch。 |
| Runtime release chain | ext-reg independently releases `runtime-core-py-v<version>` wheels through Changie and `packages-release.yml`。core-py currently pins the exact `runtime-core-py-v0.1.1` wheel URL。 | Pass。Dedicated ext-reg feature branch/PR -> release-version PR -> published wheel -> separate core-py exact pin/lock update。 |

## SDK Realization Notes

- `MCPServer(...).streamable_http_app(streamable_http_path="/mcp", stateless_http=True, json_response=True)` is the smallest
  official realization。No custom JSON-RPC、SSE compatibility layer or FastMCP replacement is indicated。
- In an existing ASGI host，the supplied `host` value controls SDK transport-security defaults rather than binding a socket。
  The mounted application must not accidentally retain localhost-only Host validation in preview/production；ordinary PAT
  authentication remains the product boundary。
- The SDK's default 4 MiB limit applies to inbound Streamable-HTTP POST bodies，not server tool results。There is no evidence
  for making that transport limit configurable in this read-only MVP。
- The high-level Resource template contract has a declaration-time MIME type。Dynamic Block MIME remains available on
  Resource links/native content；a generic lazy `resources/read` fallback may use `application/octet-stream` without
  inventing a low-level MCP server solely for per-read MIME variation。

## Content Projection Branches

```text
requested raw | hydrated | solved value
  -> common typed projector
     -> <= 64 KiB text/JSON: embedded Resource + structured correlation
     -> bounded image/audio accepted by Host: native MCP content + URI correlation
     -> otherwise: Resource link + MIME/size hints

resources/read(inkcre://blocks/{id}/content/{mode})
  -> re-read current Block authority
  -> re-run the requested hydration/resolution layer
  -> return the complete current text/blob
```

The 64 KiB constant is a context-budget policy，not a protocol maximum。Journey C may lower it if the real Host exhibits a
concrete compatibility problem；raising/configuring it requires evidence that Resource deferral harms a real use case。

## Extension Runtime Impact

Inspected implementation confirms the horizontal correction is real rather than speculative：

- ext-reg `ExtensionPublicationSnapshot` captures/restores Source、Resolver and Peer registries；
- `DistributionModules` removes and restores matching `sys.modules` entries；
- core `SourceManager`、`ResolverManager` and `PeerManager` expose snapshot/restore helpers；
- local Extension/Source guidance currently describes reversible publication。

Implementation therefore removes reversible **type** publication while retaining exact active-effect withdrawal。The change
must not be approximated only inside core-py：ext-reg owns the runtime lifecycle and must release first。

## Branch and Review Readiness

- core-py is already on `feat/knowledge-lifecycle-task-packet-recovery` with only active task-packet edits plus the unrelated
  untracked `telegram-extension/` unit；the latter stays untouched。
- ext-reg is clean but is on unrelated `feat/extension-setup-wizard-complete`。Before any mutation，create a dedicated feature
  branch from current `origin/main`。
- Runtime and core changes remain separate commits/PRs。Do not commit task packet or implementation until Sir explicitly
  commands it。

## Residuals for Acceptance，Not Design Blockers

1. ChatGPT's exact choice to place native image/audio content into model context versus requiring Resource traversal is not
   fully specified。Journey C/E observes the actual Host and records the chosen interoperable projection。
2. Skill activation and Tool selection are probabilistic product evidence。Only Scan Tools import、manifest digest and MCP
   protocol behavior are deterministic acceptance claims。
3. The current Resolver set has no unique Extension-only public `get/read` method beyond ordinary base-method overrides。
   Dynamic Extension behavior is still proven by invoking the RSS override；acceptance must not reshape production APIs to
   create a more theatrical example。
