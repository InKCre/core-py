# MCP Sink Implementation Evidence

## Current Realization

- ext-reg `feat/mcp-sink-runtime` removes registry snapshot/restore and simulated module unload；type registration is
  process-monotonic，while exact routes、newly-owned Peer inbounds and public claims are withdrawn。
- core-py removes Source/Resolver/Peer snapshot APIs，adds persisted `sink_types` / `sinks`，`SinkManager + SinkBase`，
  `core.mcp.v1` and the Peer-JWT management surface。
- MCPSink uses official MCP SDK `2.1.1`，one instance PAT，stateless Streamable HTTP，seven exact Tools，live Block/Resolver
  Resources and the bounded OpenAI Skills extension。
- Runtime/Unit/deployment docs now record the local lifecycle and projection contract；shared Hub truth has not been edited
  from the Spoke。

## Evidence So Far

- core narrow Ruff/Pyrefly checks pass after Resource URI and byte-size corrections。
- migration revision `143c4f4adc85` is recorded；`pdm run check:migrations` passes。
- independent official MCP client over in-process ASGI proves：invalid PAT `401`，initialize succeeds，exact seven tools are
  listed，one Skill is discovered/read，and close removes the exact mount。
- ext-reg Runtime formatting、Ruff、Pyright、reproducible wheel build and whitespace checks pass。Runtime source PR `#27`
  and Version PR `#28` merged independently；release `runtime-core-py-v0.1.2` was published from exact main revision
  `be9629a` with wheel and sdist assets。
- ext-reg's full `pnpm check` passes，including generated contracts、Python/TypeScript types、all package builds and Worker
  dry-run；the local Node 26 versus declared Node 22 warning is non-failing。
- A process-local lifecycle journey using the released Runtime seam performs two start/stop cycles：the exact route and newly
  owned Peer inbound appear/disappear each time，while the Resolver registration remains after both stops。
- OpenAPI has been regenerated from the current application route authority。
- The released Runtime is installed from the exact `runtime-core-py-v0.1.2` URL in the Core lock；the local editable
  Runtime is no longer present。
- The worktree-scoped remote-Docker runtime converges at migration `143c4f4adc85` and reports `/readyz = 200`。The migration
  introduced `sink_types` / `sinks`，and the database contract now includes both tables in its protocol-table authority。
- Journey A runs against the real mounted endpoint with persisted Sink `1`：disabled is `404`，invalid PAT is `401`，enable
  survives a Core cold start，the official MCP client initializes and lists the exact seven Tools plus one `use-inkcre`
  Skill，disable withdraws the route，and re-enable creates a fresh working SDK runtime。
- Journey B uses a four-Block/four-Relation directed corpus created through the ordinary Graph command。Real lexical and
  DashScope `text-embedding-v4` records are maintained through the ordinary managers。One multi-mode call preserves
  lexical rank and semantic score independently while de-duplicating `block:2`；mixed open isolates one missing Block，
  Block/Relation expansion returns bounded valid neighborhoods，and path retrieval returns a valid two-hop route from Block
  `1` to Block `4` without asserting which equal shortest path wins。
- Journey C uses bounded text，an 85,026-character text Block and an 83-byte PNG in PostgreSQL binary storage。`raw` keeps the
  storage pointer，`hydrated` exposes authoritative bytes，and `solved` preserves image facts。The 64 KiB boundary emits
  Resource links；`resources/read` returns all 85,026 text characters and the PNG bytes，with `image/png` and size carried by
  the solved-content Resource link。
- Journey D groups repeated Blocks `1/2/1` into one `core.text.v1` method catalog，ignores the simultaneously supplied
  Resolver list by accepted precedence，and exposes the typed public `get_*` methods。A valid `get_text` call and unavailable
  `get_missing` call complete in one batch with ordered index correlation and isolated outcomes。

## Open Gates / Observed Blockers

- Core's full gate passes foundation、migration、format、lint and type checking；its existing PostgreSQL migration suite cannot
  start because this machine only has Homebrew `libpq`'s client `initdb` and no sibling `postgres` server binary。Ten
  non-PostgreSQL admitted tests pass；40 skip and the 10 database cases fail at shared fixture setup rather than application
  execution。
- Journey F has deterministic released-Runtime evidence，but the Core implementation still needs its final repository gate、
  reviewable commit and preview deployment。
- Journey E remains manual：Secure MCP Tunnel + ChatGPT Developer Mode must use the reviewed preview endpoint and record the
  observed productive-task behavior。No automated assertion will be promoted from that journey。
