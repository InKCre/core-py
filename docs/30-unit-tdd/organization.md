# Organization

Shared Product language and cross-unit contracts remain owned by `docs/_shared/`. This document records only the implemented
core-py topology and exact local contracts.

## End-to-end topology

```text
automatic Job / explicit rumination
  -> exact BehaviorResolver
     -> behavior-owned initial context
     -> purpose-built Agent selected by core.organization.<behavior>
        -> definition-selected retrieval / Resolver / graph navigation
        -> no graph effect
        -> exact behavior mutation tool
           -> ordinary Block / Relation transaction
              -> later Resolver, retrieval, navigation, or application use
```

Organization improves an existing info-base for plausible later use. It neither predicts an exact future query nor reorganizes
for structural neatness. Automatic Jobs bound the number of initial seeds, not the size of every seed's context or subsequent
Agent exploration. Rumination's focal context includes all direct relations; exploratory behaviors use a relation-count limit
for their initial seed context.

## Behavior carriers

Core implements seven independent Resolver classes: rumination, scoped supersession, non-dominating refinement, evidence
stance, provenance-preserving synthesis, existing-referent anchoring, and provenance-aware duplicate assertion. There is no
generic Organization manager/base/dispatcher or persistent behavior table.

Each behavior Resolver provides:

- a stable, versioned Resolver ID and readable description;
- a lazy descriptor Block using that Resolver;
- `record_candidate()` for an exact `candidate for` edge;
- its own automatic availability and execution method;
- its own exact graph command where the behavior has a precise mutation.

Resolver registration remains the single extensibility mechanism. The candidate tool discovers registered classes by their
small structural capability; Core does not maintain a second behavior registry. An Extension can therefore provide another
exact behavior Resolver and its own execution/config/Job contracts without modifying a central Organization map.

## Behavior relations and commands

Relation content is owned next to its writer and reader, not in a global registry:

- `successor --supersedes--> predecessor` rejects a currently visible directed cycle;
- `detail --refines--> predecessor` rejects a currently visible directed cycle;
- `evidence --supports/challenges--> assertion` rejects the opposite stance for the exact pair;
- every material source `--synthesis--> derived text Block`; changed reapplication also writes
  `previous synthesis --edited--> new synthesis`;
- `source --has mention--> occurrence-local selected-text Block --refers to--> existing referent`;
- lower Block ID `--duplicates assertion-->` higher Block ID.

These commands validate graph mechanics, not open-world meaning. They do not delete, merge, overwrite, assign confidence, infer
transitive closure, or reserve generic Relation writes. Sequential exact replay converges through fetchsert. Synthesis replay is
keyed by exact text plus exact source basis; the ordinary Block identity rule is not changed.

## Reading and Agent boundary

Exploratory behavior definitions select the following owner-provided read tools:

- info-base owns `retrieve` and `get_entities`;
- the Resolver domain owns `resolver` discovery and invocation;
- Graph Navigation owns `get_entity_neighborhood`, `find_path`, and `get_connected_components`.

Organization owns only its behavior definitions, candidate selection, initial message, and behavior-specific mutation tools.
The generic read contracts and Agent-facing controllers remain with their semantic owners; Organization does not redefine
them merely because its Agents consume them. MCP Sink and Agent Query Sink may compose the same owner contracts without
becoming dependencies of Organization.

Mutation tools are behavior-specific, except the single dynamic `record_organization_candidate` tool. Agent definitions—not an
extra runtime allowlist—select the tools appropriate to each behavior. AgentManager and AIManager remain graph-blind execution
infrastructure; they do not own Organization semantics or writes.

The supplied rumination definition retains only `get_draft_graph_schema`, `draft_graph`, and `submit_graph`. Its task is to
reconsider the supplied focal Block, not to search the graph or mark candidates for other behaviors. Other behaviors may still
mark a rumination candidate. These choices belong to Agent definitions, not an additional runtime enforcement layer.

## Automatic Jobs and configuration

Seven exact Job handlers independently execute the seven behaviors with bounded `max_seeds`. They share Job lifecycle only;
there is no Evolution umbrella Job. Availability requires the corresponding deployment config and a locally executable Agent.
No schedule is created automatically.

The config keys are `core.organization.rumination`, `.supersession`, `.refinement`, `.evidence_stance`, `.synthesis`,
`.existing_referent_anchoring`, and `.duplicate_assertion`. Each value contains only its selected Agent ID; model, prompts, tools,
tool choice, and turn budget stay in the Agent definition.

Candidate selection combines behavior-owned strong signals, recent Blocks, explicit `candidate for` edges, and a small random
fallback. A completed Job may write nothing. Missing/unavailable runtime prevents claim; unhandled provider, database, or model
execution failure uses the existing failed/timed-out Job lifecycle.

Automatic execution logs a selected Block disappearing or one Agent Turn reaching its model-call limit as a recoverable seed
failure, then continues with the remaining seeds. Already committed graph effects remain. If all attempts complete without a
batch-level failure, the Job finishes even when individual seeds failed; this is not a semantic success verdict. Configuration,
provider, database, unexpected execution errors, and cancellation still escape. Explicit focal rumination continues to report
budget exhaustion to its caller. These diagnostics use the existing application logger and configured backend, not a new report.

## Graph use

`get_connected_components` 的通用查询合同归 Graph Navigation。Duplicate Assertion 只拥有它的消费规则：
一个完整的 `duplicates assertion` component 计作一个 provenance occurrence；truncated 结果不能证明临时分组
彼此独立。这里不重复定义遍历算法或返回模型。

`SupersessionBehaviorResolver.read_lineage()` follows `supersedes` relations in both directions from a focal Block and returns
the bounded graph, current frontier, cycle detection, and truncation. A relation points from successor to predecessor:
for C supersedes B and B supersedes A, the complete acyclic result has frontier C and retains A/B in its history. The frontier
contains Blocks with no incoming supersedes relation; a cyclic or truncated result has no current frontier. This read does
not validate semantic supersession or select a latest Block by timestamp.

这些读取直接 await GraphUnitOfWork 中的 repositories，不再通过 worker thread 执行同步 SQL。
公开组织行为命令各自拥有一个事务；合成的 Block、来源关系与 edited 关系，以及锚定的片段和关系，
都在同一事务中提交或回滚。内部协作只接收必需的 GraphUnitOfWork，不以可选 session 改变提交语义。
自动行为先在短作用域内读取 seed 与邻居，退出后才调用 Resolver 或 Agent；媒体解释的邻居按 ID 批量读取。
Other relations remain usable through ordinary navigation; no shadow Organization index is maintained.

## Best-effort limits

Organization can abstain, miss relevant information, or be wrong; semantic quality is evaluated through credentialed,
Human-reviewed information worlds rather than a claimed completeness score. External Storage pointer bytes can change without an
observable Block/Relation change, so synthesis reconsideration and all relation-based propagation remain best effort. The system
does not persist no-op/evaluated state, chain-of-thought, behavior reports, or a universal relation-force engine.

Media interpretation remains a separate existing Organization path and keeps its bounded report contract. Explicit focal
rumination keeps the existing Peer capability and HTTP request contract while its local implementation is now carried by
`RuminationBehaviorResolver`.
