# Organization

Shared Product language and cross-unit contracts remain owned by `docs/_shared/`. This document records only the implemented
core-py topology and exact local contracts.

## End-to-end topology

```text
automatic Job / explicit rumination
  -> exact BehaviorResolver
     -> bounded deterministic seed evidence
     -> purpose-built Agent selected by core.organization.<behavior>
        -> retrieve / resolver / graph_retrieval
        -> no graph effect
        -> exact behavior mutation tool
           -> ordinary Block / Relation transaction
              -> later Resolver, retrieval, navigation, or application use
```

Organization improves an existing info-base for plausible later use. It neither predicts an exact future query nor reorganizes
for structural neatness. Initial seeds bound starting cost but do not bound Agent exploration.

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

Agents receive three owner-coherent read tools:

- `retrieve(query, mode)` combines lexical/semantic entry without hiding their separate results;
- `resolver` describes or invokes typed public `get_*`/`read_*` methods through `ResolverManager`;
- `graph_retrieval` describes or invokes bounded graph queries through `GraphNavigationRetrievalManager`.

The corresponding owners create Pydantic method contracts and validate invocation. Agent adapters serialize values and reject
binary projection; they do not replace Resolver or Graph Navigation APIs. MCP Sink consumes the same Resolver-owned reflection
contract but Organization does not depend on MCP.

Mutation tools are behavior-specific, except the single dynamic `record_organization_candidate` tool. Agent definitions—not an
extra runtime allowlist—select the tools appropriate to each behavior. AgentManager and AIManager remain graph-blind execution
infrastructure; they do not own Organization semantics or writes.

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

## Graph use

`GraphNavigationRetrievalManager.get_connected_components()` partitions caller seeds by bounded undirected connectivity over
exact requested Relation contents. It returns discovered member Blocks, spanning proof Relations, missing seeds, and a truncation
flag. A truncated result cannot prove that separate provisional components are independent. Its first use law is counting one
`duplicates assertion` component as one provenance occurrence.

`SupersessionBehaviorResolver.read_lineage()` exposes a bounded lineage graph, current frontier, cycle detection, and truncation.
Other relations remain usable through ordinary navigation; no shadow Organization index is maintained.

## Best-effort limits

Organization can abstain, miss relevant information, or be wrong; semantic quality is evaluated through credentialed,
Human-reviewed information worlds rather than a claimed completeness score. External Storage pointer bytes can change without an
observable Block/Relation change, so synthesis reconsideration and all relation-based propagation remain best effort. The system
does not persist no-op/evaluated state, chain-of-thought, behavior reports, or a universal relation-force engine.

Media interpretation remains a separate existing Organization path and keeps its bounded report contract. Explicit focal
rumination keeps the existing Peer capability and HTTP request contract while its local implementation is now carried by
`RuminationBehaviorResolver`.
