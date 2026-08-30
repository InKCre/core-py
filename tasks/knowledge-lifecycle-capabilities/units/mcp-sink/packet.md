# MCP Sink

- **State**: Active — Execute。Product/technical/acceptance、preflight、Impact Handshake and implementation approval are
  complete；current evidence and remaining delivery gates are tracked in [implementation evidence](implementation-evidence.md)。
- **Objective**: make InKCre available to external Agents through MCP as the first sink vertical，including a thin ChatGPT
  integration and an Agent Skill delivery surface over MCP。
- **Product boundary**: MCP serves **Agent retrieval of InKCre**。The downstream Agent owns whether retrieved information is
  used for writing、design、coding、chat or another task。
- **Non-goals**: generic sink framework、IME/browser/Figma/ChatGPT-specific sink、answer generation、Chat InKCre、hybrid
  retrieval composition。
- **Current premise**: info-base query primitives now exist：feature/lexical retrieval、semantic retrieval and graph-navigation
  retrieval。MCP should expose useful access to those primitives and solved content without becoming their owner。
- **Accepted MVP boundary**: read-only retrieval/context sink。No write、collect、organization、source action、email action or
  answer-generation tool enters this unit。
- **Cross-cutting correction**: simplify Extension publication before building Sink registration：registered Python
  capability types are process-monotonic；disable reverses active runtime effects rather than Source/Resolver/Storage/Sink
  registries or `sys.modules`。
- **Cross-repository owner**: Extension lifecycle primitives are owned and released by `../ext-reg/runtimes/core-py`；core-py
  consumes its released wheel and owns Host integration。The correction must change the Runtime source first，release it，then
  update core-py's pinned runtime dependency/facade without creating a local fork of the same lifecycle。
- **New scope input under investigation**: this unit must also support ChatGPT Plugin integration and deliver InKCre's
  philosophy / usage as an Agent Skill through MCP。Do not yet equate these requests with legacy `ai-plugin.json`，MCP
  Prompts，or an Extension-owned Agent adapter until current platform/protocol evidence establishes the right projection。
- **Current execution surface**: exact accepted journeys live in [acceptance](acceptance.md)；the cross-repository delivery
  sequence lives in [implementation plan](implementation-plan.md)；current implementation truth and blockers live in
  [implementation evidence](implementation-evidence.md)。

## Product Contract

MCP sink makes InKCre available as an evidence/context environment to external Agents。The caller Agent owns the final task；
InKCre owns retrieving、opening and graph-navigating info-base evidence。

```text
External Agent
  → recall/search InKCre
  → open selected block/relation evidence
  → expand graph context
  → optionally find a path between two blocks
  → use returned evidence in caller-owned work
```

The MCP server should not mirror internal REST/database APIs。Its surface is an Agent-environment interface shaped for
iterative tool use：few deep tools、explicit references、structured evidence、shallow error semantics and no hidden server-side
browse session。

## Accepted Tool Surface Direction

MVP tool direction separates discovery、inspection、content reading and graph navigation：

- `inkcre_recall(query, modes, limit?)`: discovery over explicit retrieval modes。`modes` may contain multiple values such as
  `lexical` and `semantic`。
- `inkcre_open_entities(entities)`: inspect graph entity references without forcing the Agent to pick Block-vs-Relation tools。
- `inkcre_read_blocks(blocks, content?)`: read Block content through a small stable set of InKCre content-layer intents。
- `inkcre_expand_entities(entities, context_limit?)`: bounded graph context expansion around Blocks or Relations。
- `inkcre_find_path(from_block, to_block, max_hops?, direction?)`: bounded graph path retrieval。

`inkcre_recall` multi-mode semantics are **parallel recall + entity de-duplication + per-mode evidence**。It is not hybrid
ranking：MVP does not normalize lexical and semantic scores into one cross-mode relevance score。Each result keeps mode-local
rank/snippet/score evidence so the Agent can decide the next action。

`inkcre_open_entities` is one Agent action even though implementation may dispatch internally by graph entity kind。This keeps
the MCP surface aligned with the Agent's current state：it already has an entity reference and wants to inspect it。

`inkcre_read_blocks` currently uses fixed content-layer intents：`solved`、`hydrated` and `raw`。These common reads do not
replace the separately required product behavior that MCP exposes relevant Resolver capabilities。The exact exposure shape
is reopened below；do not infer from the accepted `read_blocks` shape that specific Resolver behavior is deferred or optional。

MCP `resource_link` / `resources/read` is only transport realization for large、多模态 or non-inlineable payloads。It must not
be used as the product answer to whether Resolver read capabilities are exposed。

## Resolver-Capability Design

The five accepted core tools remain unchanged。The additional product behavior—“MCP exposes Resolver read capability”—has
been reconciled with the Block / Relation / Storage / Resolver model and accepted in D-381–D-383。

Confirmed pressure only：

```text
Block -> exact resolver ID
Resolver -> base behavior + exact-resolver-specific behavior
Extension runtime -> can change the registered exact Resolver set
MCP Server -> must make relevant Resolver read behavior available to an Agent
```

The accepted realization derives read-intent method contracts from ordinary public Resolver methods，adapts them through
the two bounded Tools，and keeps the top-level MCP Tool catalog stable as the Resolver registry changes。

## Recovered Info-Base Model

The current evidence supports this model：

```text
persisted Block.content ---------------------+
  inline text                                |
  or Storage-owned opaque pointer            v
                                    hydrated content
Storage(pointer) -> actual bytes             |
                                             + direct Relations
                                             v
Block.resolver -> exact Resolver contract -> solved/use-facing meaning + Block behavior
```

- `Block` is one persisted information unit；`Relation` is a directed semantic fact between Blocks。The graph，not a
  parallel source-native object store，is info-base authority。
- `Storage` owns pointer grammar and byte mechanics only。Hydration makes the Block's actual inline text or stored bytes
  available；it does not interpret them。A transfer URL is a Storage-owned transport hint，not semantic content。
- `Resolver` is the exact/versioned behavior contract selected by `block.resolver`。It interprets hydrated content together
  with the local Relations required by that contract。It is not merely a parser/decoder and must not be bypassed merely
  because hydrated content happens to be text or JSON。
- Resolver behavior has a shared base and an open exact-Resolver-specific portion。Base behavior currently includes solved
  content，text/label projection and relation/content mechanics；concrete Resolvers may add domain behavior such as RSS
  enclosure content materialization。These remain ordinary use/sink-neutral Resolver methods。Resolver must not declare
  Agent-facing or MCP-facing capability metadata。
- A Resolver may read local graph context or lazily add graph facts while completing an ordinary read capability。“Read
  calls never write” is therefore not a Resolver invariant。The MCP MVP's read-only boundary excludes Agent-intended mutation
  commands；it does not disable Resolver-owned lazy materialization required to complete `get/read` semantics。
- Resolver availability and executable behavior are peer-local runtime facts。core-py and client-web implement the same
  exact Resolver identities but can expose different behavior（for example remote materialization versus presentation）。
  Peer equality does not imply identical Resolver capabilities。
- Extensions make the exact Resolver set open at runtime。Current durable prose says installed decoders survive disable，
  while the inspected runtime publication currently restores/removes Resolver registrations on disable。This is a real
  implementation/documentation discrepancy to resolve outside the MCP interface assumption；the MCP design must not silently
  choose one side as fact。

## Recovered MCP Model

- MCP Tools are server-global named actions with descriptions and JSON Schemas；the Agent/Host invokes them through
  `tools/call`。The server may change its tool catalog and announce `notifications/tools/list_changed`。The official Python
  SDK supports runtime add/remove plus list-change notification。
- Dynamic catalog publication and progressive model exposure are different responsibilities。The MCP Server owns what its
  catalog contains；the Host decides which discovered tool definitions enter a model turn。`tools/list` pagination is not a
  guarantee of progressive Agent loading。As of the 2026-08 MCP roadmap，protocol-level progressive discovery is planned，
  not yet a stable primitive。
- MCP Resources/resource links solve URI-addressed and large/binary content transfer。They do not name Agent actions and do
  not answer how Resolver behavior is discovered or invoked。
- Therefore “MCP exposes Resolver capability” means the MCP sink adapts relevant use-neutral Resolver behavior into actions
  an Agent can discover and invoke for Blocks governed by an exact Resolver，including behavior contributed by Extensions。
  It does not mean Resolver knows about Agents/MCP，MCP mirrors every class method，or one generic read operation can infer
  which specific action the Agent intended。

## Dependency Correction

The rejected direction was：

```text
Resolver -> declares Agent-facing capability -> MCP
```

This would make the interpretation boundary depend on one downstream use/sink and would let MCP vocabulary alter Resolver
contracts。The accepted architectural constraint is：

```text
Block -> exact Resolver -> use-neutral typed behavior
                              ^
                              |
MCP sink -> Agent-facing adapter/tool projection
```

- Agent-facing names，descriptions，input/output schemas，batching，content-block projection and MCP annotations belong to
  the MCP sink boundary。
- Resolver owns only its ordinary typed behavior and domain semantics。It must remain callable by organization，retrieval，
  UI，MCP or another future use without importing or describing any of them。
- Dynamic Extension support cannot be solved by adding MCP metadata to Resolver classes **or by requiring each Extension to
  contribute a second MCP adapter**。Extension is only one delivery/lifecycle source of Resolver implementations；it is not
  part of the Agent→Resolver use path。

The corrected runtime topology is：

```text
Extension/runtime ----registers----> ResolverManager <----observes/uses---- MCP sink
                                           |
Block.resolver ----selects exact class----> Resolver instance
```

- Existing Extensions continue to register ordinary Resolver classes exactly once。They acquire no MCP files，hooks，
  schemas or Agent-facing descriptions。
- ResolverManager's current exact registry is the peer-local executable truth shared by every use owner。MCP consumes that
  same truth instead of creating an Extension-parallel capability registry。
- MCP owns projection from a Resolver's ordinary public typed method to MCP tool identity/schema/result content。Any
  mechanical discovery or filtering rule belongs entirely to MCP and ResolverManager's already-public Python contract；it
  must not require Resolver/Extension to mention Agents or MCP。
- The solved design question is how MCP exposes and progressively presents use-neutral Resolver methods from the current
  registry，not how Extensions publish Agent-facing capabilities。

This topology is accepted as D-381：

```text
Agent
  -> discover Resolver behavior applicable to Block
  -> invoke selected behavior
  -> MCP adapts arguments/result
  -> Resolver executes ordinary domain behavior
```

The earlier singular phrase “one method” was not frozen。D-382–D-383 resolve discovery and invocation as two stable Tools
with scoped catalog results and batched independent method-call atoms rather than one top-level Tool per method。

The next candidate design must preserve this effect distinction：

- use-neutral `get/read` behavior may internally hydrate，traverse local graph or materialize a missing derivation under its
  existing Resolver contract；
- explicit `create/update/delete/materialize/recompute` commands remain outside the read-only MCP MVP even if implemented as
  public Resolver methods；
- MCP must classify Agent-visible intent rather than inspect database side effects or require Extensions to annotate them。

## Method Projection Pressures

Automatic method projection is not metadata-free。If MCP classifies ordinary Resolver methods by name，ResolverBase must
establish a use-neutral public naming contract such as `get_*` / `read_*` for retrieval intent and
`create_*` / `update_*` / `delete_*` / `materialize_*` / `recompute_*` for explicit mutation intent。This naming belongs to
the Resolver API，not MCP，but MCP may consume it。The prefixes express coarse intent only；they do not replace typed
arguments，docstrings，return contracts or the accepted fact that a `get/read` method may lazily materialize internally。

Directly projecting every applicable method as an always-visible native Tool risks catalog/schema explosion as exact
Resolvers and their specific methods grow。This is now an in-scope product/interface problem，not a deferred Host concern。
Before freezing direct per-method Tools，compare current MCP progressive-discovery work and deployed Host/provider tool-search
mechanisms against an InKCre-owned minimal fallback。The solution must preserve typed atomic methods and avoid making every
Extension publish MCP metadata。

Current evidence rules out treating Host-side deferred loading as the portable contract：the 2026-08 MCP roadmap still
describes protocol-level progressive discovery as future work，while `tools/list` remains the standard server catalog。
Provider-specific tool search may optimize some Hosts，but the MCP sink cannot assume that every Agent runtime supplies it。

The accepted portable design is therefore a **scoped method catalog + scoped invocation envelope**，not one native MCP Tool
per Resolver method：

```text
Agent --inspect methods for these Blocks--> MCP --ResolverManager registry--> compact method contracts
Agent --invoke selected method call(s)----> MCP --typed validation---------> Resolver instance(s)
```

- Discovery is Block-scoped：resolve each Block's exact Resolver and return only its applicable public read-intent methods，
  rather than the deployment-wide Resolver catalog。
- The catalog returns exact method identity，ordinary description and input schema on demand；it does not create a second
  registration authority。
- Invocation accepts semantic method-call atoms。An envelope may batch independent calls without redefining them as one
  coarse domain action；the runtime may execute independent calls concurrently and returns results correlated to calls。
- This keeps the MCP Tool count bounded while preserving runtime Extension dynamism and Resolver-owned typed behavior。
- The cost is that method-specific input schema is discovered at runtime instead of appearing as a top-level native Tool
  schema。The design must therefore reuse framework/Pydantic validation and must not grow a custom validator or universal
  capability dispatcher。

This is accepted as D-382。The surface uses `inkcre_resolver_methods` for Block-scoped discovery and
`inkcre_invoke_resolver_methods` for a batch envelope of independently identified method-call atoms。It does not fold dynamic
method schemas into the five stable tools or add a third catalog/registry abstraction。

D-383 extends discovery without expanding the Tool count：`inkcre_resolver_methods` accepts `blocks` or exact `resolvers`。
When both are supplied，non-empty `blocks` wins。Block targets are grouped by their exact Resolver and represented once with
`blocks: int[]`；Resolver-direct results omit `blocks`。This lets an Agent reuse Resolver IDs learned from
`inkcre_open_entities` while preserving the Block as invocation-time Resolver authority。

## Preserved Design Constraints

- Keep `inkcre_recall`、`inkcre_open_entities`、`inkcre_read_blocks`、`inkcre_expand_entities` and
  `inkcre_find_path` unchanged while solving the additional Resolver-capability surface。
- Agent actions should be atomic and composable；depth is measured by caller understanding，not by minimizing method count or
  hiding semantically different operations behind one discriminator。
- Agent tools should normalize redundant compatible inputs through deterministic precedence/defaulting when intent remains
  unambiguous and the semantic cost is negligible。Do not turn avoidable shape conflicts into caller-facing work；do not use
  this principle to hide genuinely indeterminate or unexecutable requests。
- Reuse the established progressive-schema pattern where it fits：compact exact identities/descriptions first，detailed
  runtime-dependent schemas on demand。Do not build a universal reflection service。
- Runtime/framework validates raw Tool input once and hands ordinary typed input to the Resolver/domain handler。
- Registry-owning Managers own exact identity，metadata，duplicate and lifecycle rules；decorator registration is the
  established Python preference，not a reason to invent one global Registry。This does not authorize ResolverManager or a
  Resolver class to own MCP/Agent-facing registration。

## Technical Topology Direction

The accepted server topology is core-py-owned Streamable HTTP mounted directly into the process ASGI application。The
official MCP Python SDK owns protocol parsing，discovery/call framing and transport content；ordinary InKCre Managers remain
the business owners beneath the adapter。

The accepted domain topology is `SinkManager + SinkBase -> MCPSink` (D-384)。`SinkManager` owns peer-local Sink registration
and lifecycle；`SinkBase` is the extension point；`MCPSink` owns the SDK server instance，the seven accepted Tool adapters，
Resolver-method projection/invocation and MCP result adaptation。Runtime bootstrap depends on `SinkManager` rather than the
concrete MCP protocol implementation。

A future Extension may deliver/register another `SinkBase` implementation。It does not mutate `MCPSink` or contribute a
parallel MCP adapter merely because it is an Extension。As corrected by D-388，Extension/Core startup registers only an exact
Sink type/code capability；registration neither creates nor starts a Sink instance。

The Sink lifecycle follows the established type/instance separation：`sink_types` is the reconciled capability catalog，while
`sinks` owns persisted instance config and enablement intent。`SinkManager` constructs and runs only selected persisted
instances whose exact type is registered。A registered type is inert by default。There is no public Sink `unregister()`
command，registration-triggered start，or Sink-owned snapshot/diff/restore model；existing Extension publication compensation
is not the Sink business lifecycle。Each `sinks` row carries Peer-scoped `enabled: PeerRef[]` with an empty default；only a
selected Peer with the exact registered type runs that instance。There is still deliberately no false generic `deliver()`
method or transport abstraction。

D-391 fixes the runtime responsibility split。`SinkManager` is the explicit application service for type catalog，instance
CRUD，config，Peer enable/disable，cold start/shutdown and the local running map。It does not continuously reconcile database
rows。A `SinkBase` object binds one persisted row，provides typed config access/update and implements `on_start(app)` /
`on_close()`。Multiple rows of one type therefore create multiple objects rather than binding runtime state to the subclass。
Config update delegates to the running instance without a generic restart policy；a concrete Sink owns any special live-update
behavior。Async context management remains an internal implementation tool for MCPSink rather than the shared Base contract。
Enable/disable persists requested Peer intent before applying the corresponding local runtime action；failure remains
observable and does not trigger a generic compensation transaction that rewrites intent。

### Accepted endpoint lifecycle (D-392)

The inspected official MCP Python SDK imposes one concrete lifecycle constraint：`streamable_http_app()` creates a mounted
ASGI application，but a mounted sub-application's lifespan is not run by FastAPI/Starlette。Its `session_manager.run()` must
therefore be entered by the owning runtime，and that session-manager instance is single-use after exit。This supports rather
than weakens the accepted Sink instance model：one local enable constructs one fresh MCPSink object plus one fresh MCP server
and session manager；disable closes and discards that runtime object；re-enable constructs a new one。

The accepted minimal endpoint lifecycle is：

```text
SinkManager.enable(sink_id, this_peer)
  -> construct MCPSink(bound persisted row)
  -> MCPSink.on_start(app)
       create SDK MCP server + Streamable HTTP ASGI app
       enter this server's session_manager.run()
       publish one retained Starlette Mount
  -> remember the running object

SinkManager.disable(sink_id, this_peer)
  -> MCPSink.on_close()
       remove that exact Mount by object identity
       exit the session-manager context
  -> discard the running object
```

- Public path：`/sinks/{sink_id}/mcp`。The persisted Sink identity makes paths collision-free for multiple
  MCPSink instances without adding a transport-specific `path` column or config field。The same Sink enabled on different
  Peers has the same relative path under each Peer's own advertised/base HTTP address。
- Endpoint publication is concrete MCPSink behavior，not generic SinkManager knowledge and not a Peer inbound/capability。
- Startup enters the session manager before publishing the Mount；shutdown removes the Mount before closing the manager。
  The same retained-route identity technique already used for hot Extension route withdrawal is sufficient；no route
  registry，snapshot/diff/restore or dispatcher is proposed。
- The transport is stateless Streamable HTTP with JSON responses。The accepted Tools require no client callback
  channel，and stateless requests avoid introducing an MCP session-affinity lifecycle into the Sink instance。
- The accepted bearer PAT remains MCPSink configuration and gates this mounted ASGI boundary。It does not enter Core's Peer
  JWT middleware or affect Core readiness。Exact SDK-vs-Starlette middleware realization remains an implementation-plan
  choice after the endpoint shape is accepted。

The discovery of existing Source/Resolver snapshot/restore changes this unit's horizontal implementation scope (D-389)。The
current Extension Runtime attempts to make Python type publication reversible by snapshotting global registries and deleting
Extension packages from `sys.modules`。That mechanism is rejected：one process keeps one exact loaded Extension version，type
registrations are monotonic，and a version change requires restart。Hot disable remains for active effects only—routes、Peer
inbounds and resources owned by `on_close()`。The implementation must remove registry rollback and simulated module unload
instead of extending them to Sink；a failed import may leave an inert type until restart。

MCP Host/Client is an external Sink consumer rather than an InKCre Peer (D-386)，so MCPSink does not reuse Peer JWT。Its
deployment-scoped long-lived bearer PAT remains the accepted credential shape，but D-388 supersedes D-386's proposed
deployment-config persistence location：the concrete MCPSink instance config belongs to its `sinks` row and is validated by
the registered Sink type schema。Ordinary Authorization middleware gates the mounted MCP app；a disabled/unavailable Sink
instance does not make the Core runtime unready。A future centralized key/token service may add multiple devices，rotation or
expiry without changing Tools，but none of that subsystem enters this MVP。

## ChatGPT Plugin and Agent Skill scope evidence

Current OpenAI platform terminology resolves the new request without a second business service：a Plugin is a distributable
composition of Skills，an MCP server and optional UI。ChatGPT developer mode can create a personal Plugin directly from one
remote MCP URL。The old `ai-plugin.json` / OpenAPI adapter model is therefore not the relevant target。For this unit，the
ChatGPT runtime path can remain the same `/sinks/{sink_id}/mcp` endpoint and the same seven Tools；no ChatGPT-specific
business endpoints or duplicated Tool handlers are indicated。Optional MCP Apps UI is not required by the accepted
read-only retrieval use case and remains out of scope unless later acceptance shows that structured evidence cannot be used
effectively without it。

OpenAI also currently supports importing an Agent Skill from the MCP server while scanning a Plugin。The supported shape is
a bounded static subset of draft SEP-2640 rather than stable MCP core：

```text
MCP initialize
  -> capabilities.extensions["io.modelcontextprotocol/skills"] = {}

Plugin Scan Tools
  -> skills/list
  -> skills/get(skill://.../SKILL.md)
  -> resources/read(each declared resource)
  -> verify SHA-256 manifests
  -> snapshot the Skill into the Plugin draft
```

ChatGPT and Codex do not fetch the imported Skill live during ordinary use。A changed Skill requires another server scan and
Plugin version/review。The Skill is therefore a versioned Agent-facing projection；the MCP server remains the live-data/action
owner。The accepted product direction is one goal-facing `use-inkcre` Skill，not one Skill per Tool and not a Tool manual。It
gives the Agent the InKCre mental model and metacognitive trigger needed to notice when collected information could improve
the quality or efficiency of the Agent's current productive/creative work—including when the Human did **not** explicitly ask
to search a knowledge base or “find something”。It must not enumerate a preferred recall/open/read/expand/find-path recipe or
teach recall-mode mechanics；the Tool schemas own operational discoverability and the Agent remains free to compose atomic
actions for its actual context。Block，Relation，Resolver and the collect→organize→use model belong only where they build that
metacognition，not as a miniature architecture manual。

The official Python SDK currently provides generic MCP Extension/custom-method APIs but no stable Skills package。The
minimal implementation candidate is therefore one isolated MCPSink-owned adapter using the SDK's ordinary Extension，typed
custom-method and Resource surfaces。It should implement only the exact static OpenAI-supported subset，not the unsettled
dynamic/archive portions of SEP-2640。Resolver，Extension and the Sink domain remain Skills-neutral。

The compatibility conflict was that accepted MCPSink authentication is a caller-supplied long-lived bearer
PAT，while current ChatGPT Plugin connections explicitly cannot present custom API keys。ChatGPT supports anonymous access，
MCP OAuth，or private connectivity through Secure MCP Tunnel；it cannot consume the accepted PAT contract directly。The
target is now confirmed as a publicly hosted but permanently single-user/personal InKCre deployment，not a SaaS service。
OAuth and Secure MCP Tunnel must therefore be compared against that real topology instead of assuming OAuth from public URL
alone or deferring the decision as hypothetical。

Current official Tunnel behavior provides a simpler candidate than changing MCPSink authentication。`tunnel-client` can
forward to an HTTP MCP server and attach static MCP request headers sourced from environment/file configuration。Therefore
it can present the existing `Authorization: Bearer <MCPSink PAT>` on the private downstream hop while ChatGPT selects the
OpenAI-hosted Tunnel by Platform/ChatGPT account context；ChatGPT itself never needs to store or present the custom PAT。

```text
ChatGPT developer-mode Plugin
  -> OpenAI-hosted Secure MCP Tunnel endpoint
  -> customer-run tunnel-client
       + static Authorization: Bearer <MCPSink PAT>
  -> /sinks/{sink_id}/mcp
  -> unchanged MCPSink authentication + Tools + Skill projection
```

This accepted topology keeps OAuth out of the InKCre product and avoids an identity/consent/account subsystem that has no product
meaning in a permanently single-user deployment。It also keeps Tunnel ownership outside business code；`tunnel-client` is an
operator-run companion and ChatGPT-specific connection path，not a Sink transport abstraction or another Sink type。Its real
cost is operational；the companion must remain running for ChatGPT calls，and Tunnel supports private/developer-mode use but
not public Plugin distribution。That limitation matches the current personal ChatGPT target (D-394)。The PAT remains
required for direct MCP requests；it is not nullable and no anonymous MCPSink mode is introduced。

## Accepted seven-Tool domain mapping

The next implementation-facing mapping keeps retrieval/graph/content semantics with their existing owners while MCPSink owns
only Agent-facing composition and MCP result adaptation：

| MCP Tool | Existing domain authority | MCPSink-owned remainder |
| --- | --- | --- |
| `inkcre_recall` | `LexicalRetrievalManager.retrieve()` and `SemanticRetrievalManager.retrieve()` for the explicitly requested modes | run independent modes concurrently，normalize results to entity refs，deduplicate and preserve mode-local evidence |
| `inkcre_open_entities` | `BlockManager.get_many()` and `RelationManager.get_by_id()` | parse `block:<id>` / `relation:<id>`，preserve request order，and project bounded Block/Relation previews |
| `inkcre_read_blocks` | `BlockManager.get_many()`，`BlockModel.get_hydrated_content()` and `ResolverManager.get(block).get_solved_content()` | apply one request-level `raw|hydrated|solved` mode and adapt large/multimodal values to MCP content/resources |
| `inkcre_expand_entities` | `GraphNavigationRetrievalManager.get_block_neighborhood()` / `get_relation_neighborhood()` | batch independent entities，adapt bounded `GraphModel` neighborhoods and isolate per-entity misses/failures |
| `inkcre_find_path` | `GraphNavigationRetrievalManager.find_path()` | adapt the domain's found/not-found/limit-reached outcome without inventing a second traversal policy |
| `inkcre_resolver_methods` | `ResolverManager` exact registry + Block-selected Resolver class | derive the compact read-intent method catalog，group Blocks by Resolver and expose typed schemas/descriptions on demand |
| `inkcre_invoke_resolver_methods` | `ResolverManager.get(block)` + ordinary typed Resolver method behavior | validate the batch envelope，call independent atoms concurrently，preserve input order and adapt results/failures |

This accepted mapping (D-395) does **not** add an `MCPSinkRetrievalManager`，a generic tool dispatcher or MCP-specific methods to existing domain
Managers。Preview/resource serialization is a downstream presentation concern and remains inside MCPSink；query，graph，
hydration and Resolver semantics remain use/sink-neutral。

### Accepted Resolver-method eligibility correction

Code inspection shows that a `get_*` prefix alone is insufficient：the current Resolver contract includes
`get_existing(db_session: sqlmodel.Session)` for producer-side reconciliation。It is ordinary internal domain behavior but
cannot be invoked from an Agent JSON argument and must not appear in the MCP catalog。

The candidate projection rule remains convention-based and metadata-free：

1. consider only public bound instance methods whose names start with `get_` or `read_`；
2. require an inspectable typed signature with no variadic arguments；
3. ask Pydantic to derive JSON Schema for all caller-supplied parameters；if the ordinary signature cannot be represented as
   Agent JSON（for example an application-owned database Session），omit the method from discovery；
4. invoke only identities returned by the same projection，validate arguments once through the derived Pydantic model，and
   adapt the runtime result through the common MCPSink content projector；
5. do not add Resolver decorators，allowlists，MCP metadata，dependency injection or a second capability registry。

The coarse prefix remains a Resolver API intent convention；JSON-schema representability establishes whether that ordinary
use-neutral behavior can cross the Agent boundary。Omission means “not Agent-callable through this transport”，not that the
Resolver method is invalid or private to its Extension。This rule is accepted as D-399。

## Accepted `use-inkcre` Skill contract

The Skill has two distinct owners，so its delivery copy does not become a second Product authority：

- Hub Product / Product-TDD remains authoritative for the InKCre mental model，terminology and collect→organize→use / sink
  philosophy。Missing or corrected shared truth is promoted there through the ordinary Hub-first workflow。
- core-py MCPSink owns the exact Agent-facing `SKILL.md` projection and its MCP Skills delivery mechanics，because wording，
  trigger quality and static Skill packaging are part of this Sink's interface。The projection may summarize Hub truth but
  cannot redefine it。

MVP needs one static English `SKILL.md` and no auxiliary reference bundle or generated-doc pipeline。Its content has three
short responsibilities：

1. **Metacognitive trigger** — consider InKCre when the current productive/creative task may benefit from information the
   Human previously collected，such as past decisions，preferences，examples，sources，fragments，relationships or surrounding
   context，even when the Human did not explicitly request retrieval。Do not query reflexively when stored information is
   unlikely to improve the work。
2. **Mental model** — understand only the info-base concepts exposed by this MCP surface：Block is one persisted information
   unit；Relation is a directed semantic fact between Blocks；Resolver gives a Block its exact use-facing meaning and
   behavior；Storage owns pointer/byte mechanics rather than interpretation。Do not teach Source，collection，organization，
   sink lifecycle or the full product topology that this read-only surface cannot operate。
3. **Use posture** — treat retrieved Blocks/Relations as contextual evidence rather than a generated answer，preserve useful
   provenance/relationships，and choose atomic MCP actions according to the current task。Do not prescribe a fixed Tool
   sequence or explain recall-mode mechanics。

This accepted contract (D-396) intentionally keeps exact Tool documentation in MCP schemas/descriptions and keeps the Skill
small enough to shape Agent judgment rather than occupy context with an InKCre architecture tutorial。

## Accepted Block-content delivery contract

`inkcre_read_blocks` has three independent dimensions that must not collapse into one discriminator：

1. `raw|hydrated|solved` is the requested InKCre content layer and applies to the whole batch；
2. text、JSON-compatible facts or bytes are the returned value's representation；
3. embedded content versus a Resource link is only the MCP delivery choice。

MCP Resource defers context inclusion；it does not reduce the eventual payload，because `resources/read` still returns the
complete text/blob。The accepted policy therefore keeps one Tool behavior and lets MCPSink choose delivery automatically：

- bounded text / JSON-compatible content is returned as a URI-bearing embedded Resource；bounded image/audio may use MCP's
  native content blocks when the actual Host path proves they reach the model correctly；
- oversized content and content without a useful native MCP model-content representation（such as video、PDF or generic
  files）is returned as a Resource link carrying MIME/size hints when known；
- every projection has a deterministic URI such as `inkcre://blocks/{block_id}/content/{mode}` and is resolved lazily from
  current info-base authority；there is no persisted resource row，download-session model or separate content cache；
- the structured batch result correlates each Block with its Resolver、Storage reference and content URI，while the ordinary
  MCP `content` array carries the corresponding embedded Resource or Resource link。No extra `found` / `inline` status is
  added；payload presence and the standard MCP content-block type already express those facts；
- `raw` remains literal persisted `Block.content`，even when it is a Storage pointer；`hydrated` uses actual inline/stored
  content；`solved` uses the Resolver result。Resource delivery must not silently substitute one layer for another；
- nested bytes in a solved typed result require one common MCPSink result projector。The implementation preflight must inspect
  actual Resolver result shapes and prove the smallest lossless projection instead of adding Resolver-specific MCP adapters。

The inline budget is an implementation/compatibility constant，not an Agent argument or deployment product setting，unless
Host acceptance demonstrates a real need for configurability。Image/audio-specific direct content blocks are not yet frozen：
the acceptance spike must compare them with URI-preserving Resources in the actual ChatGPT/SDK path before choosing the
smaller interoperable realization。

This contract is accepted as D-397。The URI identifies a live read projection，not an immutable snapshot or persisted
Resource entity。

## Accepted Acceptance topology

Acceptance should prove one external Agent-facing vertical rather than mirror handler branches。The candidate evidence has
three complementary layers：

1. **Protocol/domain black box** — run the mounted Streamable-HTTP endpoint through an independent MCP client with a real
   PAT and a small real info-base corpus。One journey must recall evidence，open mixed entities，read small text plus
   multimodal/oversized content，follow the returned Resource，expand a neighborhood，find a path and discover/invoke a
   Resolver-specific read method。This proves the seven Tools compose over real domain owners rather than mocked handlers。
2. **ChatGPT product journey** — connect the same endpoint through Secure MCP Tunnel in Developer Mode，import the
   `use-inkcre` Skill，and perform a real productive task for which previously collected information is useful。Observe
   whether the Agent notices InKCre without a literal “search my knowledge base” instruction，retrieves relevant evidence
   and uses it as context rather than presenting Tool output as an answer。
3. **Runtime lifecycle journey** — persist and enable one MCPSink instance for the current Peer，observe endpoint/tool/Skill
   availability，disable it and observe route withdrawal，then re-enable a fresh SDK runtime。An Extension-delivered Resolver
   method remains registered process-locally across Extension disable while active Extension effects close normally。This
   covers the horizontal monotonic-publication correction without inventing registry-unit tests。

The direct MCP journey is the deterministic contract evidence。The ChatGPT journey is manual product evidence because model
tool selection and Skill triggering are probabilistic；it must not be promoted into a brittle automated assertion。Exact
fixtures/scripts remain implementation-plan work after the Human accepts the acceptance boundary。

This topology is accepted as D-398。

### Accepted acceptance corpus ownership

The deterministic MCP journey should use a dedicated preview/local corpus rather than mutable personal production state。
The corpus remains real info-base data and is created through ordinary producer/Manager paths，not test-only Resolver methods
or branches：

- one small text/structured Block for embedded `raw|hydrated|solved` reads；
- one storage-backed image/audio Block for multimodal delivery and lazy Resource reading；
- one deliberately oversized text or file Block for the Resource-link boundary；
- a small directed graph with at least one alternate branch for neighborhood and path behavior；
- one Block governed by an Extension-delivered Resolver，preferably from an existing real Source/producer，for method
  discovery/invocation and process-monotonic registration evidence；
- lexical and semantic records produced by their ordinary maintenance paths rather than inserted as fake retrieval rows。

The corpus content should be useful real public material，but its exact subject does not shape production code。The manual
ChatGPT product journey may separately use Sir's actual production info-base，because relevance to current work is the
behavior under observation there。This ownership is accepted as D-400。

### Accepted batch outcome contract

The multi-target Tools must preserve independent progress without making the Agent infer silent omission：

- malformed top-level Tool input remains framework/Pydantic validation failure；
- after a batch is admitted，each target/call produces one ordered result atom；one miss or invocation failure does not abort
  sibling atoms；
- a successful atom contains its natural payload (`block`，`relation`，content/resource，graph or invocation result) and no
  redundant `status: found`；
- a failed atom retains the input correlation key and an `error` object with a small actionable code plus observable message；
- the overall MCP `isError` remains false when the batch itself completed with isolated atom failures。It is true only when a
  shared failure prevented the Tool operation from producing the admitted batch result at all。

Candidate public error codes are intentionally shallow：`not_found`，`invalid_arguments`，`unavailable` and `failed`。Domain
outcomes such as graph path not found remain their existing natural result rather than being reclassified as execution errors。
This contract is accepted as D-401 and promoted into the task-wide experimental API design taste。

## Interface Research Baseline

- MCP 2026-07-28 distinguishes server tools、resources and prompts；tools are the primary fit for model-controlled retrieval
  actions，while resources can provide stable URI-addressed context。The current spec also favors stateless request/response
  operation，so any cursor/reference must be explicit tool data。
- MCP `tools/list` may change over time and supports pagination/caching，but the tool set must not vary per connection or as
  a side effect of ordinary requests。MVP therefore keeps a stable small tool set；future resolver-specific tool exposure
  needs a deliberate registration/loading contract rather than hidden per-block dynamic tools。
- ReAct-style agents benefit from interleaving reasoning with environment actions；therefore the sink should support
  iterative search → open → expand rather than one opaque answer-producing tool。
- Toolformer / function-calling evidence favors simple APIs with precise schemas and descriptions；large ambiguous API
  surfaces increase selection and argument errors。
- MRKL/Gorilla/ToolLLM/API-Bank-style evidence frames InKCre as an external knowledge module/tool environment，not the
  downstream Agent itself。Tool descriptions and result contracts are part of the interface, not incidental documentation。

## Delivery Gate

```text
Product contract
  → Technical contract ↔ Acceptance draft ↔ Implementation-plan probe
  → evidence preflight / branch simulation
  → Impact Handshake
  → explicit “开始”
  → Execute
  → Verify / Promote
```

No implementation is authorized by this packet。

The implementation-facing preflight is now recorded in [`preflight.md`](preflight.md)。It found no product/technical
contract contradiction and fixes the SDK、mount、Skills-import、Resource-budget、acceptance-corpus and ext-reg release details
needed for Impact Handshake。
