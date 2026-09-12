# Organization Model Realization Map

- **State**: accepted Technical foundation under D-499；exact model contracts are closed by D-503/D-506–D-511/D-520。
- **Purpose**: apply the accepted distinction-realization axis to the complete Nowledge-derived Product set before choosing
  modules、Agents、Tools、Jobs or shared infrastructure。
- **Boundary**: this map classifies Product responsibilities；it does not create delivery slices、runtime entities or a common
  Organization interface。

## Why The Product List Is Not A Component List

D-493 names the surviving Product returns，but those returns came from studying product mechanisms and therefore do not all
occupy one abstraction level。D-498 supplies the missing test：an independent conceptual Organization model must define a
semantic question、admissible judgments、evidence/authority law、graph expression and later-use interpretation law。

Applying that test yields five different roles：

| Role | Meaning | Technical consequence |
| --- | --- | --- |
| Exact model | owns all five parts of the D-498 contract for one reusable distinction | deserves one inward semantic operation/owner |
| Model family or method | constrains several possible exact models but leaves some exact relation/subject/use meaning open | may guide implementations；does not justify a dispatcher or base class |
| Invocation/reapplication law | determines when an existing model should reconsider current graph authority | belongs around that model's operation，not beside it as another behavior |
| Candidate specialization | finds or qualifies possible inputs for an existing model | remains replaceable evidence acquisition；cannot persist authority by itself |
| Cross-model invariant | rejects an invalid source of authority or effect across models | enforced at exact model/consumer boundaries，not implemented as its own job |

This removes accidental symmetry from the feature list without deleting any accepted Product requirement。

## Current Classification

| Accepted Product return | D-498 role | Reason |
| --- | --- | --- |
| Scoped supersession | exact evolution model | asks whether one scoped assertion/state displaces another within proven continuity；produces a dominance relation interpreted as current/history |
| Non-dominating refinement | exact evolution model | asks whether later information continues and adds to an evolving subject without displacement；produces traversable lineage without a currentness law |
| Evidence stance | exact evolution model | asks how one scoped information item bears on another；keeps both authoritative while changing corroboration/tension interpretation |
| Provenance-preserving n-ary synthesis | exact Organization model/method | defines set-level qualification、derivation、provenance、output and later drill-down without requiring one closed subject taxonomy |
| Dependency response | reapplication law for an exact synthesis model | an upstream graph change conducts reconsideration pressure；the only possible durable result is still no-op or a new result under the synthesis model plus ordinary continuity |
| Contextual linking | model family | defines candidate-to-assertion discipline and durable contextual meaning，while the exact relation question、direction、payload and consumer remain contract-specific |
| Existing-referent anchoring | exact model inside the contextual-linking family | asks whether implicit source meaning denotes existing identity-bearing information and，when supported，creates a reusable source-grounded identity path |
| Provenance-aware duplicate assertion | exact model | asks whether two scoped assertions reproduce one provenance occurrence；records non-independence so evidence consumers count the component once without merge |
| Normative-authority separation | cross-model invariant | recurrence or model confidence may support descriptive synthesis but cannot create operational force；authority must come from an entitled source/consumer |

One classification deliberately retains a family boundary rather than pretending the Product study supplied a closed ontology：

- contextual linking is open-world by design，so a generic “context link” operation cannot authorize arbitrary Relation content。

Evidence stance can admit `supports`、`challenges` and no-op as outcomes of one exact comparative question while retaining scope
and provenance。N-ary synthesis is also complete at the model level：its subject may be inferred or supplied per invocation，while
its qualification、authority、graph result and later-use law remain stable。A procedure SOP is therefore an application/candidate
mode under this model，not a required new model or generic `Crystal` type。

## Exact Model Contracts

### Scoped supersession

```text
affordance forecast: likely uses need current state without losing history
occasion/candidates: possible continuity plus possible dominance within scope
semantic question: does newer information displace older information under the same continuity、scope and authority？
judgments: supersedes / unresolved / no-op
evidence law: record time or contradiction alone is insufficient；continuity、scope and entitled dominance are required
graph distinction: directed scoped supersession relation between retained information
consumer law: derive a current frontier and retained history only inside this model/scope
```

### Non-dominating refinement

```text
affordance forecast: likely uses need the accumulated refinement path rather than one flat item
occasion/candidates: possible continuity plus additive detail/explanation
semantic question: does later information refine the same evolving subject without invalidating its predecessor？
judgments: refines / unresolved / no-op
evidence law: thematic similarity alone is insufficient；subject continuity and a material additive contribution are required
graph distinction: directed refinement lineage
consumer law: traverse connected refinements while retaining co-active branches；do not infer current/history dominance
```

### Evidence stance

```text
affordance forecast: likely uses need corroboration or tension without flattening disagreement
occasion/candidates: assertions comparable under a shared referent、scope and temporal applicability
semantic question: does one item support or challenge another scoped assertion，and on what source basis？
judgments: supports / challenges / unresolved / no-op
evidence law: semantic agreement alone does not prove source independence；stance does not replace either endpoint
graph distinction: directed source-grounded support/challenge relation
consumer law: expose evidence provenance、corroboration/tension and uncertainty without manufacturing a single truth state
```

### Provenance-preserving n-ary synthesis

```text
affordance forecast: likely repeated uses would otherwise rediscover、read and integrate the same source set
occasion/candidates: a heuristic or application proposes a set；the model qualifies shared subject、compatible scope and distinct contribution
semantic question: what independently reusable derived information is warranted by this collective basis？
judgments: a provenance-preserving synthesis proposal / unresolved / no-op
evidence law: retain exact source basis、contribution、disagreement、uncertainty and speaker attribution；sources remain authority
graph distinction: append-only derived Block plus derivation/contribution Relations to the complete basis
consumer law: address the combined view while permitting drill-down and basis-aware applicability
```

Dependency response extends only the occasion line：a relevant change reachable through derivation dependencies makes the
synthesis model eligible for reconsideration over the affected basis。It neither supplies a new judgment nor writes a `stale`
state。Ordinary version continuity is `old --edited--> new`；a changed synthesis similarly appends
`S1 --edited--> S2`。Supersession/refinement may coexist only when their separate semantic questions are also satisfied。
Unobservable bytes changing behind an unchanged Storage pointer provide no complete trigger and remain best-effort。

### Exact contextual-link instance

```text
affordance forecast: likely uses would materially misread or underuse one item without a particular neighboring meaning
occasion/candidates: similarity、topology、mention resolution or another bounded heuristic proposes endpoints
semantic question: does this exact directed relation hold，with enough payload to recover why the neighbor matters？
judgments: one contract-valid relation proposal / unresolved / no-op
evidence law: candidate evidence is not assertion authority；Resolver meaning and relevant graph/source context must support it
graph distinction: ordinary directed Relation with exact model-owned semantic content
consumer law: exact retrieval/resolution logic may traverse or expose the context；there is no universal eager “read together” law
```

### Existing-referent anchoring

```text
affordance forecast: likely uses need one stable auditable path from an exact source-grounded referring part to information about the referent
occasion/candidates: a selected referring fragment plus candidate existing identity-bearing information
semantic question: does this selected source expression denote this existing referent strongly enough to anchor them？
judgments: source-to-fragment-to-referent anchor / unresolved / no-op
evidence law: name/type similarity is insufficient；identity evidence、source context and competing referents must be considered
graph distinction: source --has mention--> referring fragment --refers to--> existing information
consumer law: graph/query traversal may reuse the referent path across sources and time without treating the anchor as a merge
```

This exact model composes the contextual-linking family's candidate-to-assertion discipline with referent resolution。Identity
ambiguity or absence yields unresolved/no-op；success materializes only an occurrence-local referring fragment and does not justify
a generic Entity、new identity materialization or anchoring framework。

### Provenance-aware duplicate assertion

```text
affordance forecast: likely evidence uses must not count copies of one occurrence as independent corroboration
occasion/candidates: high semantic overlap plus provenance proximity
semantic question: do both Blocks reproduce the same scoped、temporally applicable assertion from one provenance occurrence？
judgments: duplicate assertion / unresolved / no-op or routing to another owning model
evidence law: equivalent claims from independent sources are not duplicates；similarity alone is insufficient
graph distinction: non-destructive duplicate-assertion Relation；all Blocks and adjacent Relations remain
consumer law: evidence consumers count one duplicate-connected provenance occurrence once；query may derive a representative
```

## One End-To-End Topology，Several Independent Runs

```text
past-use evidence / known use pressure
  -> forecast one useful affordance class
     -> choose an exact model and model-owned occasion
        -> candidate seed
           -> Resolver + retrieval + optional exploration assemble evidence
              -> replaceable judge applies the exact model
                 |-> unresolved / no-op
                 `-> model-valid proposal
                    -> exact command validation
                       -> persisted graph distinction
                          ... future request remains unknown ...
                             -> exact consumer interprets that distinction
                                -> promised affordance becomes available
```

Each exact model independently traverses this same causal/time axis。Shared implementation is justified only for a repeated
mechanical need along the axis—such as reading resolved context or committing an idempotent relation—not because several models
are called Organization。

## Consequences For The Existing Technical Draft

1. `dependency response` does not receive an independent semantic module/Agent/Job merely to mirror the Product inventory；it is
   an invocation path into the synthesis model。
2. `normative-authority separation` receives no runner；exact synthesis and downstream operational consumers must preserve it。
3. `existing-referent anchoring` is an exact contextual-linking model that may reuse candidate/qualification routines；it owns a
   source-grounded anchoring contract but no generic Entity subsystem。
4. a single generic contextual-link command is too weak to validate open-world meaning；exact link contracts may reuse a small
   relation assertion primitive。
5. n-ary synthesis owns generic set-level qualification、authority and graph/use meaning；subject-specific heuristics/SOPs may
   propose sets or shape output but do not become new models by default。
6. Agent、direct AI and deterministic code remain replaceable judges/adapters。No exact model may depend inward on Agent/Tool
   orchestration。

## Accepted Result

D-499 accepts this classification as the basis for Technical design。The next step derives the minimum common mechanisms from
repeated rows of these exact contracts and maps each missing consumer contract；it does not create a behavior registry or choose
an Agent topology first。
