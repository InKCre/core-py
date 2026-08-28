# MCP Sink

- **State**: Active — Product/tool boundary accepted；technical topology is the current discussion surface。
- **Objective**: make InKCre available to external Agents through MCP as the first sink vertical。
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
- **Next discussion surface**: finish the persisted Sink instance/runtime contract and exact seven-tool→domain mapping，then
  freeze acceptance and implementation planning。

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

The remaining work is technical realization：derive read-intent method contracts from ordinary public Resolver methods，
adapt them through the two bounded Tools，and keep the MCP catalog stable as the Resolver registry changes。

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
- The remaining design question is therefore how MCP exposes and progressively presents use-neutral Resolver methods from
  the current registry，not how Extensions publish Agent-facing capabilities。

This topology is accepted as D-381：

```text
Agent
  -> discover Resolver behavior applicable to Block
  -> invoke selected behavior
  -> MCP adapts arguments/result
  -> Resolver executes ordinary domain behavior
```

The singular phrase “one method” is not frozen。Discovery scope，direct-vs-progressive presentation，per-method tool
identity，per-Block batching and multi-call composition remain open and must be separated rather than collapsed into one
generic dispatcher by default。

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
selected Peer with the exact registered type runs that instance。The exact `SinkBase` instance runtime contract remains to be
derived from this model。There is still deliberately no false generic `deliver()` method or transport abstraction。

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
