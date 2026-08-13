# Rumination And Graph Forms

> [Technical design index](index.md)

## T-017 Rumination Approach And Interpretation Relation（approved through D-145）

`rumination` is the concrete organization approach in which one focal Block is reconsidered in its graph context and a
more useful ordinary graph is materialized。An implementation may compose parsing、LLM、resolver materialization and linking
mechanics。Output relations should express discovered information value；a mandatory `part:<order>` lineage is rejected。
A composition/order relation remains legitimate only when document structure itself is useful，not as proof that an
algorithm split text。

`breakdown` is retired from the technical vocabulary。It may remain historical/product shorthand for the observable case
where information aggregated in one Block becomes a richer graph，but it does not name a runtime abstraction、command、
class、registry、DTO or job。

The operation may also materialize embedded information：for example，an authored URL can become an independently resolved
Block connected by a supported semantic relation。Extractive/source-faithful output remains the default evidence rule；
generated summaries or paraphrases require a distinguishable future graph grammar。

The focal Block is the true organization input。Its direct incoming/outgoing Relations form the initial graph-position
context；they do not turn the operation into a relation-list transformation。The concrete rumination implementation declares
the understanding capability required by its reasoning core，and the Block resolver supplies that capability from hydrated
actual content。The MVP text-LLM implementation therefore requests resolver `get_text()` even when the hydrated value happens
to be a string；runtime representation is not semantic permission to bypass the resolver。A future multimodal implementation
may require image、audio or structured understanding through the same pattern。At the product level，“Block content” means
the actual content after any storage pointer has been resolved；at the storage contract level，the persisted field remains a
pointer until hydration；at the application boundary，the resolver owns understanding。

If the resolver cannot supply the understanding capability required by this implementation，the implementation cannot
understand the Block；this does not mean rumination is inapplicable。The organization-facing contract exposes shallow
best-effort completion semantics：one consideration is completed with currently available capabilities，without promising
graph mutation。Cannot-understand and no-useful-output therefore complete silently rather than becoming public typed
outcomes。An execution that cannot complete may surface one high-level rumination failure，without leaking resolver、storage、
AI-provider or persistence exception taxonomies。

MVP performs one attempt。Do not add internal retry、compensating rollback、degradation or fallback policy。A rich internal
outcome model is allowed only if concrete control flow needs it；module depth is not a reason to prebuild unused machinery。
This follows the shared design pattern that a deep module may own rich internal distinctions while exposing the shallowest
completion semantics that preserve its abstraction-level promise。

The MVP text-LLM context is one bounded snapshot。It contains focal resolver `get_text()` output plus every direct
Relation's direction and exact content。The other endpoint is projected as an opaque Block reference、resolver name and
resolver `get_label()` output；its complete text/content is not recursively loaded。The projection preserves the dynamic-
property semantics `to is from's <relation-content>` while keeping the focal Block as the sole substantive input。

The approved MVP uses an Agent loop for native structured Resolver schema discovery、GraphForm drafting and eventual
`submit_graph` calls。It still has no graph-reading or navigation Tools and therefore cannot recursively explore neighbors；
the bounded D-145 snapshot remains the complete info-base read-side context。This introduces reusable Tool orchestration
without changing focal-Block authority or importing a future exploration policy。

MVP retains the input Block and all existing relations unchanged，adding only useful ordinary graph facts。It does not
delete、replace or generically rewire the target。A future explicit owner-approved replacement contract may reopen that
boundary；this unit does not spend design complexity on a low-benefit/high-risk destructive path。

Additive output need not expose a concrete world-property relation directly from the source。When evidence supports one，
use it（for example `highlight`、`need_adjustment` or `reference`）。Otherwise the source may point to one representative
entry Block of a valuable derived subgraph through an interpretation anchor。For a Markdown document，the title Block can
be that entry while quote/section relations form the internal graph。The anchor preserves source-versus-interpretation
authority and navigation without a mandatory direct edge to every output。The active exact relation content is
`interpretation`。

## T-018 Agent、Resolver Draft And GraphForm Boundary（approved through D-179）

The desired authority direction is sound：organization adds connected Blocks/Relations through `GraphForm` and
`InfoBaseManager`，so an LLM should not produce a second graph proposal model merely for code to translate it back into the
same command。Modern typed tool calls can validate JSON arguments directly and avoid text parsing。

### Current boundary ledger

This table is the current-state reasoning authority for the graph-command path。D-175–D-177 remain correction history；do
not compose superseded responsibilities from those snapshots into another topology。

| Boundary | Receives / produces | Owns | Explicitly does not own |
| --- | --- | --- | --- |
| Agent Tool runtime | untrusted ToolCall JSON → bound Pydantic Tool arguments | deserialization and one runtime validation pass，including the selected Resolver's code-owned input model；Pydantic failure → per-call ToolResult | Resolver semantics、graph normalization、persistence |
| `draft_graph` Tool handler | already validated Tool arguments → GraphForm | exact Resolver lookup，passing ordinary nested `input` to that Resolver，and adapting StarsGraphForm through the shared normalizer | repeated validation、Resolver-specific construction policy、persistence |
| `Resolver.create_graph(input)` | resolver-native ordinary input → StarsGraphForm | resolver-specific Block content、supporting graph and Relation grammar | Agent/runtime state、details of where/how its caller validated input、signed-ID allocation、persistence |
| `InfoBaseManager.normalize_graph(stars, id_start)` | StarsGraphForm → GraphForm | recursive traversal and deterministic command-local signed-ID allocation | Resolver selection、Resolver semantics、Tool validation、persistence |
| `submit_graph` Tool handler | already validated GraphForm → persisted-ID mapping | narrow Agent effect adapter into `InfoBaseManager.submit_graph()` | repeated structural validation、positive-ID existence probes、graph semantics |
| `InfoBaseManager.submit_graph(graph)` | ordinary GraphForm command → persisted Blocks/Relations | graph insertion coordination and negative→positive Block-ID mapping | Agent validation、Resolver construction、pre-querying positive endpoint existence |
| GraphForm / PostgreSQL | constructed Form / database write | Pydantic model owns intrinsic no-I/O structural invariants；PostgreSQL FK owns persisted endpoint existence and referential integrity | duplicate handler/Manager validation layers |

“Validated” therefore describes how the Agent runtime obtained the Tool handler arguments；it is not a domain value、a
wrapper type or part of Resolver/InfoBase method names。Internal callers may construct the concrete resolver-native input
or GraphForm through ordinary typed/domain paths without entering AgentManager。

Producer grammar is closed。`BlockForm` / `RelationForm` omit database-generated identity、timestamps and other database-
managed state。Flat GraphForm adds the approved command-local signed Block-ID namespace only where one batch must declare
new Blocks and connect Relations to new/existing Blocks：negative means create，positive means persisted reference，zero is
invalid。StarsGraphForm continues to compose the same base Forms recursively for Resolver/extension authoring。The exact
Python container projection is implementation-plan work，not another design question unless preflight reveals a material
contract change。

The current `SubGraphForm` implementation is failure evidence rather than a compatibility surface：

- `SubGraphForm.block` is a persisted `BlockModel`，whose generated schema exposes `id`、timestamps、storage、resolver and
  content；
- each arc embeds a persisted `RelationModel`，exposing relation ID/timestamp and endpoint columns；
- recursive tree shape cannot cleanly express an existing Block by ID alone，shared references or arbitrary connected
  graph edges；
- the model is therefore forced to understand persistence placeholders even though rumination owns those facts。

Do not solve that mismatch by adding an LLM-only graph domain。Producer-facing `BlockForm` / `RelationForm` remove
table-owned fields。Retain the recursively authored representation as `StarsGraphForm` for extension/source Resolver
construction，while flat `GraphForm` expresses arbitrary connected Blocks/Relations through signed references and is the
only Agent-visible graph command。

Resolver construction is semantically rooted：a Resolver interprets one resolver-native value as one subject Block and may
add supporting Blocks/Relations；nested Resolver calls make the complete result more than one mathematical star。
The Agent Tool `draft_graph` accepts negative `id_start=-1` by default，invokes Resolver-owned StarsGraphForm construction，
normalizes it to GraphForm，guarantees that exact ID belongs to the subject/star Block and allocates remaining draft-local
IDs below it。This preserves rooted Resolver authoring without asking the LLM to translate representations。

`GraphForm` is self-contained and uses one non-zero signed-ID namespace。Positive IDs refer to existing persisted Blocks；
negative IDs identify new Blocks only within the current form；zero is invalid。Rumination includes real focal/direct-
neighbor IDs in its initial user message，and the LLM assigns unique negative IDs to proposed Blocks。After insertion，
InfoBaseManager maps negative IDs to database-generated positive IDs。The exact field remains `id`：Form semantics already
exclude database-managed values unless explicitly stated，and the negative value is a legitimate command-local identity。

Pydantic `GraphForm` validation owns structural invariants that require no I/O：new declarations use negative IDs，endpoints
are non-zero，new IDs are unique and every negative endpoint resolves inside the form。InfoBaseManager directly executes
the graph command without pre-querying positive IDs；PostgreSQL foreign keys remain the sole existence/integrity authority
for persisted Relation endpoints。The `submit_graph` Agent Tool handler does not repeat either layer。

Draft-capable Resolvers own a compact description、one Pydantic draft-input model and rooted StarsGraphForm construction。
Do not expose persisted `block.content` schemas or pretend relation content is one globally closed enum。The rumination
Agent instead uses three bounded Tools：

```text
get_draft_graph_schema(resolvers: exact Resolver IDs[])
  -> selected descriptions + Resolver-owned draft-input JSON Schemas

draft_graph(resolver: exact Resolver ID, input: JSON, id_start: negative int = -1)
  -> GraphForm whose star Block ID is id_start

submit_graph(graph: GraphForm)
  -> {blocks: [{local_id: negative int, id: persisted positive int}]}
```

The run's initial context lists only currently available draft-capable Resolver IDs and compact descriptions。AgentManager
binds `get_draft_graph_schema` / `draft_graph` argument enums from that same ResolverManager snapshot，so the detailed schemas
are fetched only after the model selects likely Resolvers。Agent runtime uses the selected Resolver's Pydantic model to
validate generic `draft_graph.input` before handler invocation；do not add handwritten parallel validation。Schema
discovery and draft construction perform no
info-base/storage mutation，but this is an effect-boundary promise rather than mathematical purity：Resolver-owned external
reads or computation remain possible。`submit_graph` is the sole graph-write Tool and receives only GraphForm。

Existing extension/source Resolvers keep ownership of native/canonical input → one subject Block plus supporting graph and
migrate their current recursive `SubGraphForm` call sites to `StarsGraphForm` using BlockForm/RelationForm。One reusable
InfoBaseManager normalizer owns StarsGraphForm traversal and signed-ID allocation，then produces GraphForm for Agent results
and graph-write coordination。Do not duplicate that conversion inside individual extensions、ResolverManager or Agent Tool
handlers。

The internal semantic method remains concrete `Resolver.create_graph(input) -> StarsGraphForm`。Extension/source
and other Managers may call it directly；it owns resolver-specific Block content and Relation grammar。The separately
registered Agent Tool `draft_graph(...)` receives arguments already validated by Agent runtime against its bound Tool
contract and the selected Resolver's Pydantic input model。Its handler obtains the exact Resolver through ResolverManager，
passes ordinary nested `input` to that same `create_graph()` method and asks InfoBaseManager to normalize the result with
caller-supplied `id_start` before returning GraphForm。It is a thin model-facing wrapper because it adds no graph-
construction or validation policy。InfoBaseManager owns normalization and `submit_graph(GraphForm)` persistence only；it
does not select Resolvers or expose `create_graph()`。

The approved reusable topology is：

```text
Rumination / another organization approach
  owns prepared UserMessage + selected persisted Agent + graph-aware Tool handler/mutation policy
  -> AgentManager.run(agent_id, initial_message) -> active Thread
       owns bounded model/tool turn orchestration，but no graph semantics
       -> AIManager.chat(model, messages, tools, tool_choice)
            owns model -> provider -> dialect routing and wire translation
```

This does not make AIManager graph-aware。A separate AgentManager is justified because system-prompt/tool composition and
typed tool dispatch have reuse across organization approaches and a stable caller-supplied-tool boundary；it does not own
provider/model registry or graph semantics。

### Rumination selection（approved through D-180）

Rumination remains one function on the enclosing organization domain，`OrganizationManager.ruminate(...)`；the current
behavior does not justify a `RuminationManager` class or a registry of organization approaches。

The reusable AgentDefinition is an ordinary shared-database fact and may be provisioned or edited directly through that
database authority。An HTTP Agent CRUD surface may be added as a convenience projection，but is not part of the
coordination topology and is not required by this contract。The withdrawn seed/default proposal stays withdrawn。

The deployment selects its rumination Agent through the existing deployment-scoped `configs` relation：

```text
key    = core.organization.rumination
schema = core.organization.rumination.config.v1
value  = {"agent": <int>}
```

The organization domain owns the Pydantic value model under that exact schema contract。ConfigContract supplies generic
model-driven validation/normalization；DeploymentConfigManager resolves the registered schema contract and owns the shared
row lifecycle。Neither generic module invents the organization schema。`agent` is an `int` reference，not a strengthened
positive-integer contract。

`OrganizationManager.ruminate()` is the reference-use owner：it reads the deployment config，resolves the AgentDefinition
when invoked，constructs the approved focal/direct-relation `initial_message` and calls the exact stable entry
`AgentManager.run(agent_id, initial_message)`。Missing config and missing referenced Agent remain distinct explicit、
repairable configuration failures。Agent deletion receives no reverse restriction；a dangling config is allowed until use。
The invocation does not accept a per-call Agent override in the MVP。

### Organization-facing completion（approved through D-181）

`OrganizationManager.ruminate(block_id)` is an async completion-oriented function。After preparing context and resolving
the configured Agent，it calls `AgentManager.run(agent_id, initial_message)`，awaits that Thread's active Turn Task and does
not return the Thread to its caller。This preserves AgentManager's approved Thread-returning contract while keeping Agent
execution state behind the shallower organization surface。

A naturally `completed` Turn maps to `None` regardless of whether any graph was submitted。A focal Block that the selected
implementation cannot understand also completes as `None` without starting an Agent run。When the Turn reaches
`max_model_calls` before natural completion，OrganizationManager exposes one organization-level failure；already completed
Tool side effects remain and no retry、rollback or compensation is added。Cancelling the caller's rumination coroutine
propagates cancellation to the awaited Turn Task and likewise preserves completed effects。No organization job、run entity、
abort endpoint or Thread projection is introduced。

### Repeated execution（approved through D-182）

Every invocation is an independent additive attempt built from the latest focal understanding and bounded direct-relation
snapshot。No run record、`last_ruminated_at`、content fingerprint、idempotency key or per-Block lock is introduced。A
submitted negative GraphForm ID always requests a new Block；only explicit positive IDs reuse existing Blocks。Repeated or
concurrent attempts may therefore create semantically or structurally duplicate Blocks/Relations，including after an
uncertain caller retry。MVP accepts that low-harm side effect；future merge/linking/reconciliation may address demonstrated
use degradation without turning rumination into an implicit deduplicator。

The current direct-relation snapshot may show that an `interpretation` or another derived edge probably came from an earlier
rumination，but it is not a freshness authority。It does not carry a run/dependency identity or prove whether focal content、
Resolver behavior、Agent definition、neighbor facts or the deeper derived graph have changed。OrganizationManager must not
skip execution or declare the prior result current merely because such a direct edge exists。The Agent may still choose a
no-op from its limited context，but that is best-effort semantic judgment rather than an update guarantee。A future unit may
add explicit reevaluation/freshness semantics when real use demonstrates the need。

### Trigger policy（approved through D-184）

MVP rumination runs only after an explicit request naming one focal Block and enters through
`OrganizationManager.ruminate(block_id)`。There is no collection-completion hook、new-Block event trigger、periodic scan、
batch candidate selection or organization job。Collection success remains independent of organization capability、AI
availability and cost。

Automatic organization requires evidence and a separate policy for candidate eligibility、reevaluation/freshness、AI
budget/concurrency and Peer-safe claiming/execution。The current direct-relation snapshot cannot supply those decisions，so
the unit does not disguise a low-information repeated scan as scheduling。A future trigger design may reuse the same
ruminate function without changing its explicit single-Block contract。

MVP rumination provides Resolver-owned schema discovery/rooted GraphForm drafting plus one organization-owned
`submit_graph(GraphForm)` mutation Tool。It keeps the D-145 prepared focal text/direct-relation snapshot as ordinary model
input and provides no
graph-reading/navigation Tool。The early handwritten
`BlockManager.query_by_reasoning()` string-command pseudo-agent is deleted，not migrated。Agent definition、Thread and Tool
execution semantics are closed in T-019；rumination Agent provisioning/selection is closed by D-180，organization-facing
completion by D-181 and repeated execution by D-182。The generic Agent/Thread/Tool lifecycle
is owned by the separate
[Agent runtime contract](agent-runtime.md)。
