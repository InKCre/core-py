# Organization From First Principles

- **State**: accepted task-level Product/Technical foundation under D-498；not yet promoted durable truth。
- **Purpose**: derive what Organization is before choosing Resolver、Agent、Tool、Job or a new runtime abstraction。
- **Terminology warning**: `Organization behavior` has been overloaded to mean semantic law、operation、runner and code owner。
  This shard separates those roles。

## Premises Already Owned By Product Truth

1. The info-base's reusable information authority is its persisted Block/Relation graph。
2. Collection、Organization and Application/use are actions，not states of one information object or mandatory lifecycle stages。
3. Collection faithfully admits source information；Application obtains a result；Organization begins from information already
   retained and seeks to improve later use。
4. Resolver derives faithful/local use-facing meaning under one exact Block contract；retrieval indexes and embeddings are
   rebuildable Application support rather than information authority。
5. The exact future request is unknowable。Organization may forecast useful classes of future use from history、semantics and
   existing graph evidence，but cannot prove that a particular future query will occur。
6. Information is open-world and may participate in several overlapping semantic models；there is no exclusive Organization
   taxonomy or one universal state machine。

## Deduction

### D1 — Organization's subject is existing information

If an action's primary purpose is to faithfully admit source information that is not yet retained，it is Collection。Organization
may create a derived Block or Relation，but its evidence/subject is an already-retained information subgraph。

### D2 — Organization must create a reusable difference

If an invocation only returns a result to its current caller，it is Application。If it only changes a cache、embedding or search
record，it is Application support。Organization must change what later callers can learn or distinguish from reusable info-base
authority；otherwise no improvement survives the invocation。

The durable difference may add、revise、merge or remove graph authority according to an exact operation。This Unit currently
prefers additive/append-only results，but that is a feature-set design choice rather than the definition of Organization。

### D3 — The difference must express new organization-authored meaning

Hydrating bytes、decoding a format or materializing faithful OCR/transcript may improve usability，but the result is already
entailed by one source/Resolver contract。That is Resolver realization。Organization begins where the system asserts a new
distinction not mechanically dictated by one source decoder：for example scoped supersession、non-independent provenance、a
contextual dependency or a multi-source synthesis。

This distinction is about authority，not whether AI is used。A Resolver may use AI for faithful transcription；a deterministic
operation may still author Organization meaning。

### D4 — Organization is model-relative

“Make the graph better” has no correctness law。An action becomes Organization only under an exact semantic model that states
what distinction it can make and how that distinction may change a class of later use。

Define one conceptual **Organization model** `M` as：

```text
M = (
  semantic question,
  admissible judgments including unresolved/no-op,
  evidence and authority law,
  graph expression,
  later-use interpretation / state law
)
```

Examples：

- a supersession model asks whether one assertion displaces another within a scope，records that relation and lets a currentness
  consumer distinguish current from history；
- a duplicate-assertion model asks whether two Blocks repeat one provenance occurrence，records non-independence and lets an
  evidence consumer avoid counting the occurrence twice；
- a synthesis model asks whether a set supports independently reusable derived information，records the result plus basis and
  lets later use retrieve the synthesis without losing sources、disagreement or uncertainty。

The model is a semantic contract，not a required persisted row、Python base class、registry or ML model。

### D5 — Candidate formation and judgment mechanism are not the model

One application of `M` may be written as：

```text
existing graph G
  -> candidate heuristic selects a possible subject subgraph S
  -> Resolvers/retrieval expose relevant meaning/evidence
  -> a judge applies M to (G, S)
  -> unresolved / no-op
     OR an M-valid proposal
        -> exact command changes graph authority by delta
```

Candidate heuristics affect cost/recall。A deterministic rule、bounded AI call、exploratory Agent or future Human workflow may be
the judge。None of them defines `M`，and none should own its persisted grammar or later-use law。

### D6 — Later use is part of the model's meaning，not a predicted request

Organization cannot know which concrete query will occur。It must still know what reusable affordance its distinction provides：
currentness selection、evidence multiplicity、context expansion、dependency reconsideration or retrieval of a synthesis。This is
a claim about a **class of possible uses** and its interpretation contract，not foreknowledge of a future Human request。

Without such an interpretation，a graph mutation may remain useful descriptive information，but there is no basis for calling it
an Organization improvement rather than arbitrary enrichment。

### D7 — Organization is plural and non-exclusive

One information unit may simultaneously participate in evolution、evidence、context、duplicate and synthesis models。Therefore：

```text
Information
  -> exhibits zero or more model-relevant properties
     -> may participate in zero or more Organization models
        -> each model application independently yields no-op or graph distinction
```

There is no necessary umbrella operation that chooses “which model applies”，and no global lifecycle state follows from being
organized。

## The Unifying Axis — Distinction Realization

The deductions become one end-to-end causal/time axis when the moving subject is **a reusable distinction** rather than the
information itself：

```text
past use evidence / known use pressure / graph semantics
  -> forecast one useful affordance class
     -> exact Organization model M defines the required distinction
        -> an invocation occasion observes existing graph G
           -> candidate heuristic proposes subject subgraph S
              -> Resolver / retrieval / exploration assemble evidence E
                 -> a judge applies M(E, S)
                    |-> unresolved / no-op
                    `-> model-valid proposal P
                           -> exact validation + command
                              -> persisted graph distinction ΔG
                                 ... unknown time and concrete request ...
                                    -> later consumer interprets ΔG under M
                                       -> forecast affordance is available in actual use
```

Organization proper performs the middle transformation from an opportunity in existing authority to persisted distinction。
The complete Product value chain starts earlier with the reason that the model exists and ends later when a use can exploit the
distinction。This does not make Organization responsible for the later request or Application execution。

The logical forms of the distinction along the axis are：

```text
useful distinction hypothesis
  -> candidate distinction instance
     -> evidence-qualified distinction judgment
        -> authoritative graph distinction
           -> use-visible distinction
```

These are causal descriptions，not persisted statuses、a review lifecycle or a generic workflow engine。Only the graph distinction
is necessarily durable。An invocation may recompute the earlier reasoning from current authority and honestly no-op。

Past use can close a limited feedback loop：observed usefulness may change which models/candidates are prioritized in future。
It does not make exposure、clicks or repeated model output semantic evidence for the distinction itself。

### Supersession example across the whole axis

```text
known pressure: later use should not confuse obsolete and current assertions
  -> model: scoped supersession with current/history interpretation
     -> occasion: a later assertion A2 is present
        -> candidate: A2 and earlier A1 may address the same scoped subject
           -> evidence: Resolvers expose both meanings、scope、time and authority
              -> judgment: A2 supersedes A1 in scope S，or unresolved/no-op
                 -> command: persist the scoped supersession distinction
                    ... later ...
                       -> a currentness use presents A2 by default and keeps A1 reachable as history
```

The same axis is instantiated independently by synthesis、contextual linking and duplicate assertion。Their models、evidence、
judgments、graph expressions and later affordances differ；the axis does not create one dispatcher that chooses among them。

### How the deductions attach to the axis

| Earlier deduction | Position on the axis |
| --- | --- |
| subject is existing information | occasion and candidate operate on `G` |
| Organization creates a reusable difference | validated `ΔG` survives the invocation |
| Resolver realization is not Organization judgment | Resolver assembles entitled/local meaning；the model judge adds the new distinction |
| Organization is model-relative | `M` governs judgment、graph expression and later interpretation end to end |
| candidates/judges/runners do not define the model | they are replaceable mechanisms in the middle of the axis |
| later use is a class，not a known request | `ΔG` crosses an unknown time gap before a concrete consumer appears |
| Organization is plural/non-exclusive | each model runs its own axis over overlapping information |

## Candidate Definition

> **Organization is the application of an explicit semantic model to already-retained information，producing or revising a
> reusable organization-authored distinction in info-base authority so that a class of later uses gains a defined affordance。**

The action may be automatic or explicit、deterministic or AI-assisted。Its identity comes from the semantic model and graph/use
effect，not from its runner。

## Role Vocabulary Derived From The Definition

| Term | Responsibility | Runtime entity required？ |
| --- | --- | --- |
| Organization model | owns semantic question、judgments、authority、graph expression and later-use law | no；conceptual/durable contract |
| Organization operation | applies one model to one existing graph subject at one time | ordinary function/Manager command is sufficient |
| Candidate heuristic | cheaply proposes subjects/evidence worth evaluating | no common protocol implied |
| Judge | decides one model application from evidence | no common implementation；may be rule、AI、Agent or Human path |
| Proposal/command | typed model-valid requested graph change | ordinary exact schema/function |
| Execution adapter | invokes an operation via Job、route、Agent Tool or another runtime | exact adapter only |
| Consumer | gives the persisted distinction its later-use consequence | exact model/application contract |

This vocabulary replaces ambiguous uses of `Organization behavior`。Where retained for natural Product prose，it should mean the
whole exact model/operation capability，not an implementation object。

## Dependency Consequence

```text
candidate / deterministic judge / AI adapter / Agent+Tool adapter / Job / route
                                   |
                                   v
                exact Organization model implementation
                proposal + command + graph/use law
                                   |
                                   v
                    Resolver / retrieval / InfoBase
```

Outer execution mechanisms depend on the model implementation。The model implementation may consume Resolver/retrieval/InfoBase
contracts but does not depend on Agent、Tool、Thread、Job or route mechanics。Resolver remains local interpretation；it does not
become the cross-Block Organization model merely to provide a registry carrier。

## Classification Tests

| Action | Classification | Reason |
| --- | --- | --- |
| Persist an email and its source-authored body/participant relations | Collection | faithful admission of source meaning |
| Decode a PDF or materialize a faithful transcript/OCR child | Resolver realization | exact local/source-entitled meaning，not a new organization-authored distinction |
| Rebuild lexical records or embeddings | Application support | derived query acceleration，not info-base authority |
| Answer or rank one current query without retaining new meaning | Application | result serves the present invocation |
| Record scoped `A supersedes B` with a current/history interpretation | Organization | new reusable model-relative distinction over existing information |
| Create synthesis `X` from A/B/C with contribution、disagreement and attribution | Organization | reusable derived meaning plus provenance-preserving basis |
| Add links because the graph looks sparse or untidy | not justified Organization | no exact semantic question or use affordance |
| Use an Agent to summarize one Block transiently for the caller | Application | Agent mechanism does not make the output Organization |

## Consequences For This Unit

1. Do not add a generic `OrganizationBehavior` entity merely to carry runtime configuration or polymorphism。
2. Apply the model test before assigning components：some retained results are exact models，while others may be model families/
   methods、reapplication laws、candidate specializations or cross-model invariants。Only exact models own complete operations、
   commands and consumers。
3. Audit every proposed graph mutation for its model-relative distinction and later-use affordance；do not let acceptance ease、
   Agent capability or structural neatness define the Product。
4. Route faithful/local transformations back to Resolver；use exact derived-Block Resolvers only where the output has an
   independently useful content interpretation contract。
5. Select deterministic、direct-AI or Agent judgment separately for each operation after its semantic model is fixed。
6. Treat Relation-content encoding、Relation Resolver and Extension contribution as downstream Technical choices，not the
   definition or carrier of Organization itself。

## Accepted Result

D-498 accepts the six deductions、candidate definition、role vocabulary and distinction-realization causal/time axis。Technical
design now derives exact feature models and dependencies from this foundation；it must not let a runner、Agent/Tool mechanism、
acceptance convenience or structure-first abstraction redefine Organization。
