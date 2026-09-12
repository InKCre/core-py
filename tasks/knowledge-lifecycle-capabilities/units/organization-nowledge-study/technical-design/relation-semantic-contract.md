# Relation Semantic Contract — Causal Design

- **State**: retained causal analysis under D-498/D-499；its encoding examples are superseded by the active clean semantic-content
  proposal in [minimal mechanisms and consumers](minimal-mechanisms-and-consumers.md)，which awaits material review。
- **Question**: why should exact Organization Relation semantics be owned by each behavior rather than promoted into the generic
  graph model，and what must still survive in persisted Relation content？
- **Current recommendation**: exact models own Relation wording、direction and use law，while `content` remains concise graph
  meaning rather than a namespaced/versioned protocol token。Do not add a graph-level Relation Resolver or common envelope；if the
  complete assertion cannot be carried by endpoints、direction and semantic content，abstain。

## The Causal Chain

The design starts from the accepted Product topology rather than from a preferred schema：

```text
InKCre is a neutral information base
  + Organization contains several semantically different behaviors
  + future Extensions must be able to add behavior without redefining the graph kernel
    -> graph primitives cannot own one universal Organization vocabulary or state law

Some Organization judgments are open-world and strongly semantic
  -> their chosen judge may need LLM reasoning、retrieval and exploration

Durable graph mutation must nevertheless be exact and replayable
  -> unrestricted model/algorithm output cannot be the persistence protocol
  -> each behavior exposes a narrow typed command independent of the judge

The effect must survive after that invocation ends
  -> its judge/transport cannot be the sole owner of meaning
  -> the behavior owns a versioned write/read contract persisted in Relation content

Later use needs an operational effect
  -> the same behavior-specific consumer decodes the contract and applies its own state/use law
  -> the generic graph remains a carrier；connectivity alone has no force
```

Therefore the core is not exactly “compress semantics into an Agent Tool”。It is：

```text
behavior-owned semantic contract
  ├─ write projection: typed behavior command -> validation -> canonical Relation content
  └─ read projection: exact consumer -> decode -> behavior-specific force
```

An Agent Tool may adapt that command for a model，but is not the command's identity or required transport。The behavior module—not
an Agent、Tool or ephemeral call—owns semantics across both write and read sides。

## Why This Boundary Exists

The accepted Organization features do not merely add decorative edges：

- evolution decides currentness、refinement and evidence stance；
- synthesis records which sources jointly support a derived artifact；
- duplicate assertion affects whether provenance occurrences count as one assertion；
- contextual linking changes which otherwise-hidden information is reachable。

These behaviors share graph primitives but not one state machine。If their laws were raised into the generic graph level，the graph
would need to know why `replaces` dominates、why `supports` does not replace、why several `synthesis` edges form one synthesis judgment
and why a context edge only changes reachability。That would turn a neutral information graph into a closed Organization ontology
and make extension depend on modifying core graph semantics。

Conversely，raw prose emitted by a judge is insufficient。A string such as `replaces` may be source-authored text、an Organization
judgment or an unrelated domain word。The behavior command therefore accepts semantic arguments rather than arbitrary serialized
Relation content；its Manager validates endpoints and invariants，chooses the canonical versioned representation and persists it。
No judge—Agent、direct model call or deterministic heuristic—invents the storage grammar。

## Responsibility Topology

```text
Organization behavior
  owns applicability、candidate law、SOP、semantic judgment policy、content contract and state law
            |
            v
behavior-specific judge
  deterministic function、bounded AI call、exploratory Agent or later exact caller
            |
            v
typed proposal / behavior command
  judge-independent；does not expose raw persistence grammar
            |
            v
behavior Manager
  validates invariants and writes model-owned semantic Relation content
            |
            v
generic Relation(from_, to_, content)
  durably carries endpoints and opaque/open content
            |
            v
exact behavior/use consumer
  recognizes its contract、decodes it and applies currentness/evidence/dependency/multiplicity law
```

Generic Relation traversal and text projection may still expose the raw content to a Human or Agent。They do not infer operational
force from similar words or arbitrary JSON。

## Clean Semantic Content

An earlier sketch placed namespaced/versioned discriminators and payloads inside `content`。That is withdrawn：implementation
identity becomes visible relation noise and weakens the graph's direct semantic readability。The active design keeps concise
semantic phrases such as `supersedes` or `synthesis` in `content`，with no shared envelope。

The essential invariants are：

1. every caller submits a typed semantic command，not a generic “write this Relation content” command；
2. the exact model owns Relation wording and direction；
3. consumers exact-match that semantic relation rather than guessing from similar prose；
4. replay identity includes the exact content already used by `RelationManager.fetchsert()`；
5. command/API compatibility is versioned outside graph meaning；a materially different relation receives different semantic
   content rather than a numeric suffix。

## Why A Relation Resolver Is Not Yet Required

Adding `Relation.resolver` would make interpreter identity a first-class graph field and could support generic dispatch、indexing
and richer `RelationManager.get_text()` projection。It would also add a database migration、a new registry/contribution seam and
changes to Relation identity、filtering and every producer/consumer boundary。

The current Organization feature set requires exact behavior consumers，but it does not yet require the generic graph layer to
decode every heterogeneous Relation。Each behavior already needs its own state law and parser；moving the discriminator into a
column does not remove those responsibilities。Therefore the simpler content contract is the present recommendation。

Reconsider a Relation Resolver only when at least one concrete need appears：

- generic retrieval must dispatch to relation-specific label/text projection rather than expose canonical content；
- a demonstrated query requires indexed selection by interpreter family that content matching cannot reasonably support；
- Extensions need a stable generic Relation-interpreter contribution point independent of their Organization behavior consumer；
- several non-Organization producers independently recreate the same dispatch mechanism and the duplication has observable cost。

This threshold separates an open extension point from speculative symmetry with `Block.resolver`。

## Rejected Extremes

| Alternative | Why not |
| --- | --- |
| Tool-only + raw prose | meaning is not reliably recoverable after execution；later force relies on string guessing |
| Universal semantic Relation columns / ontology | forces unrelated relations into shared dimensions and moves behavior laws into the graph kernel |
| Reify every operational relation as a Block | adds topology and traversal cost before addressable higher-order relation identity is required |
| Add Relation Resolver only because Block has one | symmetry is not a Product or Technical requirement |

The chosen middle permits semantic openness where a judge needs it，keeps mutation precision in exact behavior commands/Managers，
durable meaning in semantic Relation content and operational force in the consumer that actually owns the behavior。Agent/Tool
is one possible realization，not part of this durable contract。
