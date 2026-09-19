# Product Design: Information Evolution Organization

- **State**: Product phase complete under D-493；同一 implementation vertical 已依 D-562 完成生产交付。Knowledge Evolution、Crystals、Memory Links、Ontology、Entity Extraction、Memory
  Compaction、exploratory Agentic execution topology、Automatic Labeling and Memory Type Review closed；info-base
  representation lens、Insight Detection、Working Memory、Skill Suggestions、Rule Suggestions and Memory Freshness closed；
  Organization Extension pressure accepted；Community Detection、Flags / Memory Maintenance and transfer audit closed。
- **Decision authority**: [D-462–D-470](../../decisions/D461-D470.md)、
  [D-471–D-480](../../decisions/D471-D480.md)、[D-481–D-490](../../decisions/D481-D490.md)、
  [D-491–D-498](../../decisions/D491-D500.md)。本文件拥有 coherent Product design；
  decision shards 拥有 accepted task-state decisions。

阅读边界：本文保留 Product 研究与推导，部分表格说明的是 Nowledge 的状态规律或当时尚未确定的运行机制。
当前 InKCre 合同以最新 decision 和 [Organization TDD](../../../../docs/30-unit-tdd/organization.md) 为准。
例如下文的 default recall、confidence 描述不构成全图隐藏 predecessor 或计算置信度的实现要求；当前
`read_lineage` 是有范围的显式读取。不得将历史“尚未批准实现”误读为本 unit 仍处于研究阶段。

## Product-to-Delivery Handoff

D-493 remains the authority for what the anti-overlearning audit retained、downgraded or rejected。D-495 supersedes only its
stage conclusion that no implementation vertical follows：this study is the Product phase of the same implementation Unit，not
a report handed to another Unit。

Technical design therefore carries the surviving Organization results forward as one coherent feature set and one delivery
vertical。The different behaviors remain semantic components，not delivery slices。Negative audit results remain constraints：
the implementation must not recreate a Memory ontology、generic Organization
method、fixed relation vocabulary、Human review lifecycle or graph-cleanup objective merely to obtain a uniform architecture。
If Technical/Acceptance exposes a missing Product behavior or use effect，the same Unit reopens that exact Product edge rather
than terminating as research or silently filling it with infrastructure。

## Product Foundation

The accepted first-principles definition and end-to-end distinction-realization axis live in
[Organization from first principles](organization-first-principles.md) under D-498。They refine the foundation below without
turning `Organization behavior` into a runtime entity or common processing pipeline。

InKCre stores information from potentially different sources、actors、times and contexts。It does not assume one global
epistemic subject or one canonical “my current understanding”。Nowledge's Memory is therefore a constrained memory-like subset
or application lens over information InKCre may retain，not the info-base ontology。

Organization starts from information already in persisted Block / Relation authority and creates explicit graph meaning to
improve later use。Because time is continuous，it cannot know which concrete future use will occur。At Product-design time，
observed past uses、failures and regularities may justify a forecast that one reusable distinction is worth producing；that
forecast admits or rejects an Organization behavior，but is not part of the behavior's evolution execution。

Organization-authored meaning must remain distinguishable from source-authored evidence and Resolver-derived projection。
Automatic triggering does not remove the need to define candidate、scope、authority、cost、correctness and partial effects。

## Accepted Evolution Topology

```text
Information
  -> has one or more evolution properties
     -> may participate in one or more evolution models
        -> forms model-scoped relation / state transition
```

- **Property** explains why information can participate，such as identity continuity、being a scoped assertion or carrying
  comparable provenance。
- **Model** owns the relevant scope / authority and permitted state law；it is not a mutually exclusive information type。
- **Relation / state transition** is one model outcome，not an object classification。
- One information object may simultaneously participate in source revision、decision supersession、refinement and evidence
  models。

This property/model split is the current key lever。It prevents one broad EVOLVES family from applying incompatible state laws
to all information。

## Knowledge Evolution — Accepted Product Decomposition

| Model / property | Continuity and scope | Relation / state law | Exposed reusable distinction |
| --- | --- | --- | --- |
| Supersession lifecycle | referent、authority and applicability scope remain continuous | a successor dominates a predecessor within scope；predecessor leaves default recall but remains history | future uses can distinguish applicable current information from historical state |
| Accretive refinement lineage | later information is treated as a newer refinement of the same evolving subject | no dominance/archive law is documented；the relation contributes traversal and confidence；branching remains unknown | future uses can recover accumulated explanation、detail and refinement paths |
| Evidence stance | scoped assertions are comparable and provenance/source relation is meaningful | supporting or challenging assertions remain co-active；polarity/confidence may be represented | future uses can inspect corroboration、tension and uncertainty |

Nowledge's separate Memory Link feature owns general “read together for a useful reason” relations，while EVOLVES is documented
as newer-version history。This supports mapping `enriches` to accretive refinement lineage rather than general composition。
`replaces` maps to supersession lifecycle；`confirms/challenges` map to evidence stance。The progression label therefore groups
two lineage relations with different state laws，not one lifecycle state machine。

## Accepted Mechanism Learning，Not Yet InKCre Behavior

1. New persisted information or graph change can provide a bounded automatic trigger to reconsider organization。It does not
   define the affected set and does not require every result to include the new entity。
2. Semantic retrieval can propose candidates and bound cost。It is not relationship authority or a universal candidate rule；
   different models may need identity、provenance、time or graph evidence。
3. Pairwise analysis is appropriate only when the relation is genuinely binary and supplied context is sufficient。Cluster、
   composition、synthesis and other n-ary behavior are not pairwise classification by default。

No automatic runtime、relation vocabulary、schema or implementation owner is approved by these learnings。

## Product / Acceptance Boundary

Acceptance is derived only after a concrete Product behavior exists。Difficult、expensive or unavailable evidence may expose
uncertainty or block implementation approval，but cannot replace intended behavior with an easier one。An available benchmark
does not establish Product value or choose trigger、graph shape、scope or authority。

## Evolution Model Applicability

“Information has a property” does not require a permanent enum or intrinsic Block type。A property may be an applicability
predicate over information、scope、authority and related information：

- supersession requires a continuity key plus authority to say one scoped state dominates another；
- refinement requires continuity of an evolving subject plus an additive/non-dominating relation；
- evidence stance requires comparable scoped assertions plus meaningful provenance/source relation。

For one model to justify organization behavior，it must eventually own：

1. the applicability / continuity predicate；
2. scope and authority；
3. model-specific candidate evidence；
4. permitted relation or state-transition law；
5. persisted provenance / uncertainty / correction semantics；
6. the reusable distinction exposed by the model。

Product separately uses past use evidence to forecast whether that distinction is worth producing。The forecast is a model-
admission argument，not a model transition。These are Product questions，not an approved generic runtime pipeline。Different
models may be automatic、explicit、pairwise、n-ary or unsupported；one information object may satisfy several predicates。

## Knowledge Evolution Transfer / Rejection Candidate

| Nowledge mechanism element | InKCre learning return | Rejected transfer |
| --- | --- | --- |
| New Memory triggers EVOLVES | An information/graph change can be an incremental reconsideration trigger。 | Every new Block must run one universal evolution job；only relations touching the new Block may change。 |
| Semantic similarity proposes old Memories | Candidate generation is separate from model judgment and may bound work。 | Semantic similarity is the universal candidate authority；same wording proves same referent/scope。 |
| Two Memories are classified | Pairwise analysis is valid for a genuinely binary model with sufficient context。 | All organization or evolution is pairwise；standalone Memory assumptions apply to arbitrary Blocks。 |
| EVOLVES relation changes recall/graph/confidence | A model must own explicit relation/state semantics and the reusable projection they provide。 | One open relation taxonomy can silently carry lifecycle、confidence and evidence authority without model-specific laws。 |
| Progression and validation coexist | One information item may participate in overlapping evolution models with different state laws。 | Information is assigned one evolution type；Nowledge's four relations are a complete or global InKCre ontology。 |
| Personal memory has a current understanding | Current frontier is meaningful only inside a proven continuity、scope and authority。 | info-base has one base-wide current belief；new record time means newer truth。 |

The resulting analytical shape is：

```text
information / graph change
  -> evaluate zero or more model applicability predicates
     -> gather model-specific candidate evidence and sufficient context
        -> establish model-scoped relation / state transition，or honest no-op
           -> persist provenance / uncertainty required by that model
              -> expose the model-defined reusable distinction
```

This shape explains the Knowledge Evolution learning；it does not approve a common engine、mandatory cascade or implementation
surface。

Outside that execution shape，Product selection has a separate feedback loop：

```text
past use / failure evidence
  -> forecast whether a reusable distinction is likely to matter
     -> admit、reject or revise one Organization behavior/model
```

## Knowledge Evolution Closure Candidate

Knowledge Evolution has now returned a coherent Product learning result under the eight inquiry questions：its problem is
memory-like current/history/evidence ambiguity；its event-driven pairwise operation relies on normalized personal Memories；its
persisted edges and lifecycle affect recall、confidence and synthesis；its incorrect relations have asymmetric downstream cost；
and the InKCre transfer is the overlapping property/model decomposition plus model-specific incremental mechanics above。

No concrete InKCre behavior is approved yet。A future behavior must first show real Product pressure for one model—for example a
proven revision-continuity ambiguity、fragmented refinement lineage or scoped evidence ambiguity—rather than implementing
Knowledge Evolution by analogy。

Sir accepted this transfer/rejection boundary under D-470，with future-use forecasting corrected to the separate Product-
admission loop。Knowledge Evolution is closed for this study；exact Nowledge review/cardinality details remain non-blocking
product-specific residuals。Product inquiry proceeds to Crystals without opening Technical / Acceptance。

## Crystals — Accepted Synthesis Pattern And Propagation Direction

Crystals addresses a different loss from Knowledge Evolution：several source Memories can each remain valid and useful，but a
later use may repeatedly pay the cost of finding、reading and integrating the same set。Nowledge creates a provenance-linked
standalone synthesis，then tracks whether upstream evolution affects that synthesis。The first Product return is an Organization
method / pattern，not an evolution model or an exclusive Crystal object type。

### Provenance-preserving n-ary synthesis

#### The loss it addresses

The source set may jointly provide a reusable whole that no member provides alone。For example，one item gives a definition，one
gives an operating constraint，and one gives an exception。Pairwise links can say the items are related，but do not provide the
combined reference；every later use must reconstruct it。

`n-ary` is material：the derived meaning depends on the coverage and structure of a set，not on independently classifying every
pair and summing those classifications。There is no intrinsic minimum cardinality；two rich sources may be sufficient，while ten
near-duplicates may be useless。`Convergence` is therefore a poor model name because the sources need not agree。Recurrence may
help form candidates，but the proposed name is **provenance-preserving n-ary synthesis**。

#### Applicability and operation

The pattern is applicable only when all of the following can be established with enough confidence：

1. the items share a synthesis subject and compatible scope；
2. multiple items make distinct contributions to a useful combined view；
3. disagreement、uncertainty and actor/source roles can be preserved instead of flattened；
4. past evidence supports forecasting that an addressable combined view is worth producing and maintaining。

The operation then：

```text
candidate source set
  -> qualify subject / scope / distinct contribution
     -> synthesize a new organization-authored information object
        -> preserve disagreement、uncertainty、speaker and source attribution
           -> persist dependency/provenance edges and contribution roles
```

The sources remain unchanged and authoritative for what they contain。The synthesis is neither source truth nor a replacement；
it is derived information whose authority is limited to “the organization system produced this view from these sources under
this scope”。Source independence is required only if the synthesis claims corroboration；it is not required merely to combine
complementary material。

Expected Product value is amortized integration cost：later uses can address one combined view while retaining drill-down to
the sources and their differences。The honest result is no-op when one source already suffices、the set only duplicates content、
scopes cannot be reconciled、synthesis would conceal disagreement，or predicted reuse does not justify a maintained derivative。
D-472 records Sir's acceptance of this pattern，including preservation of disagreement、uncertainty and speaker attribution。

### Source change：dependency propagation，not a Crystal-specific lifecycle

The earlier `derived-information dependency lifecycle` candidate added a separate stateful abstraction before exhausting the
existing live-graph model。It also created a false symmetry with synthesis：synthesis is a reusable method that creates derived
information；source-change handling is a graph propagation concern plus ordinary version continuity。D-473 withdraws the
separate Crystal lifecycle direction。

Every synthesis must still retain its exact derivation basis。That dependency relation is more than attribution：a relevant
upstream change can conduct **reconsideration pressure** to downstream derived information。It does not copy the upstream
relation or state label to the derivative；the synthesis pattern interprets the current source subgraph again：

```text
source graph change
  -> traverse derivation dependencies to affected synthesis results
     -> reconstruct the applicable current source subgraph
        -> re-run provenance-preserving n-ary synthesis
           -> no-op，or append a new derived-information version + provenance
```

For example：

- `A1 replaced by A2` changes the applicable source frontier；a recomputed Crystal may use `A2 + B + C`。
- `B challenged by D` does not remove `B` automatically；a recomputed Crystal may preserve the new disagreement and its
  uncertainty。

This is the useful meaning of relation as a path for “force”：the typed dependency edge carries impact to a downstream operation，
while the operation's own semantics decide the result。Not every relation conducts every change，and propagation alone cannot
write the new synthesis content。

Append-only / keep-all-versions prevents silent overwrite。An ordinary edit preserves the old Block，creates a new Block and
records `old --edited--> new`；`edited` states version continuity without deciding dominance or refinement。A changed synthesis
therefore becomes `S2` with `S1 --edited--> S2`，and may additionally use the accepted supersession/refinement models when that
semantic judgment is true；a Crystal-only revision state machine is unnecessary。The current applicable projection can be
derived from graph history and recorded basis instead of persisting duplicate `current/stale/reviewed` mutable state。

`Stateless` here means the Organization operation need not retain a second mutable lifecycle state outside its inputs and graph
result。The info-base and append-only history remain state；a projection can be deterministic over that state。One invariant cannot
be eliminated：a use must not present an old derivative as based on the new source frontier。That can be satisfied by synchronous
recomputation or a basis-aware derived projection；the Product design does not yet select runtime timing。

This is necessarily best-effort at the info-base boundary。When an upstream edit is represented by a new Block、`edited` or
another observable graph change，`synthesis` routes reconsideration pressure to the affected synthesis。If bytes change
silently behind an unchanged external Storage pointer，the graph has no event from which Organization can infer the change；the
system admits that defect rather than promising a stable address、copying every source or adding a universal monitor/state
machine。

Nowledge's confirm/dismiss workflow remains product-specific evidence，not an InKCre Organization responsibility。Possible
future Human participation does not justify adding `accepted/dismissed` to the current synthesis or propagation design。Speaker
attribution remains required because it preserves source meaning；it does not imply Human review of the synthesis。

### Properties and authority that remain separate

Nowledge's “three independent sources” gate partly conflates four properties：

| Property | Product question | Not proved by source count |
| --- | --- | --- |
| Recurrence / topic overlap | Is there a candidate set worth considering？ | copied or repetitive items can inflate recurrence |
| Source independence | Does agreement add epistemic support？ | platform/thread diversity does not prove independence |
| Complementarity | Does each source add distinct content that a synthesis can combine？ | same-topic items may add nothing new |
| Salience / predicted usefulness | Is a combined reference likely worth its cost？ | repeated mention is only one forecast signal |

D-471 accepts that source count `>= 3` is a Nowledge candidate/quality heuristic，not an InKCre Product property。Recurrence、
independence、complementarity and salience may inform candidate formation or Product admission，but none defines a Crystal
lifecycle。

The authority split is likewise material：source information remains source/provenance evidence；the synthesis is
organization-authored derived information；search boost or penalty is an application projection。Speaker attribution is one
realization of the provenance rule：synthesis must preserve who asserted、recommended or decided what，rather than flattening
heterogeneous contributions into one voice。

One unresolved risk follows from this split：if Crystal membership raises a source Memory's “confidence” before Human review，
and confidence is interpreted as truth，the dependency becomes circular。If it means retrieval usefulness，it is salience instead。
InKCre therefore must not merge epistemic support with predicted usefulness merely because Nowledge exposes one confidence-like
signal。

Crystals learning therefore currently consists of one accepted synthesis pattern、dependency-directed change propagation and
reuse of common append-only/version-continuity semantics。The remaining Product inquiry is the candidate-set and contribution
logic，including whether Nowledge's weighted source contribution carries useful meaning beyond provenance ordering。No runtime、
threshold、review UI、ranking change or implementation surface is approved。

### Candidate-set formation：graph topology routes attention，not authority

Nowledge runs Crystal cluster evaluation after EVOLVES edges are created。Its important causal ordering is therefore not
“globally search for similar items and summarize them”，but：

```text
prior Organization relations
  -> expose a bounded affected neighborhood / candidate cluster
     -> independently qualify n-ary subject、scope and complementarity
        -> run provenance-preserving synthesis or no-op
```

This is another concrete meaning of a live info-base graph。An earlier Organization result does not merely decorate retrieval；
it routes attention and change pressure for later Organization。The relation is still not synthesis authority。A connected
component can drift across subject or scope through a chain of locally valid edges，and mixed `replaces/enriches/confirms/
challenges` edges do not all conduct the same operation in the same way。Candidate traversal must therefore be typed and bounded；
n-ary qualification remains a separate judgment over the selected set。

This pattern also gives the event trigger a causal position that was previously missing：a new information/edge changes one
local graph frontier，which identifies what should be reconsidered without claiming that the future use is known or that every
reachable item belongs in the synthesis。

### Contribution meaning：retain provenance before inventing scalar authority

Official API evidence establishes only that every `CRYSTALLIZED_FROM` edge has `contribution_weight` and source drill-down is
sorted descending。It does not define whether the number measures output coverage、causal dependence、epistemic support or
salience。

The defensible learning is smaller：the synthesis must expose which sources contributed and preserve enough context to explain
their contribution。A scalar may be a convenient UI ordering projection，but must not become source truth、synthesis admission
authority or propagation eligibility by field-name inference。A low-volume source may contain the critical exception whose
change forces re-synthesis；weight cannot safely suppress that path。

Under D-474，graph-guided n-ary candidate formation was accepted as a way to reuse typed prior Organization relations to bound
attention while keeping set qualification and synthesis authority separate。D-493 narrows its current status to a behavior-
specific candidate heuristic：useful，but not durable Product semantics、a common pipeline or an independent Organization method。
`contribution_weight` returns only an application-level ordering observation，not a new Product property。

The broader relation-as-force insight is registered as cross-mechanism pressure P-031 and decision D-475。This study will use a
common observation record when later Nowledge mechanisms provide new cases，but will not design a generic propagation framework
from Crystals alone。

## Crystals Closure

Crystals returns two Product learnings：provenance-preserving n-ary synthesis，and dependency-directed re-synthesis using common
append-only continuity instead of a feature-specific lifecycle。Graph-guided candidate formation remains a behavior heuristic
with separate qualification authority。Fixed cardinality、Human disposition、confidence feedback、scalar contribution authority
and ranking behavior remain Nowledge-specific or unsupported transfers。

This closes the Crystals Product inquiry under D-471–D-475。It approves no concrete InKCre synthesis runtime or implementation
vertical；the next Nowledge mechanism must again begin from its own Product loss and causal chain。

## Memory Links — Initial Product Inquiry

### Product loss and Nowledge mechanism

Similarity can retrieve two Memories that look alike，but does not persist that one changes how the other should be understood。
Nowledge Memory Links records the stronger claim that two specific Memories should be read together **for a named reason**。
Examples include a plan depending on an assumption、a note expressing a risk behind another plan，or an example making a rule
usable。

The persisted result is one stable Memory-to-Memory edge with an open normalized relation name and optional reason。Creation is
explicit：a Human，or an Agent acting with clear intent，selects the pair and decides what to save。Same-Space restriction acts as
a coarse accidental-link boundary。Later graph/Agent use can retrieve the neighbor and understand why it matters，rather than
receiving similarity alone。

### Concrete case：a rollout plan is misleading when recalled alone

Assume the info-base already contains two independently useful information objects from different work contexts：

```text
I1 — rollout plan
“At launch，80 workers will process imports concurrently。”

I2 — capacity observation
“The current database pool supports at most 50 concurrent import workers before timeouts rise sharply。”
```

Without Organization linking，both objects remain searchable，but their ordinary retrieval paths can diverge：a query about the
launch plan returns I1，while I2 ranks under database capacity or timeout language。A later use reads I1 alone，treats the rollout
as executable and misses the already persisted constraint。The Product loss is not an untidy graph；it is **isolated recall that
permits a materially wrong use of otherwise correct information**。

Automatic Organization may discover the pair from shared import/database entities、semantic evidence or a bounded graph
neighborhood。That only produces a candidate：the two items might discuss different environments、periods or worker types。If the
system cannot reconcile those scopes，the correct outcome is no-op rather than `same_topic`。

If the scopes do match，the system can establish a more exact graph assertion：

```text
I1 -- constrained_by --> I2

reason / relation meaning:
“The rollout requires 80 concurrent import workers；the recorded capacity boundary is 50 before timeout degradation。”
```

Here `constrained_by` plus the endpoints does not preserve which quantity creates the constraint。The rationale is therefore not
decorative UI text；it carries the organization-authored comparison that makes the link reusable。A later query or graph walk
starting from I1 can bring I2 into context and expose why the plan may be infeasible。The improvement is observable without
knowing the exact future query：likely future uses of the plan stop losing a known operating constraint。

This case also shows the admission boundary：

```text
shared topic/entity/numeric clues
  -> candidate pair only
     -> verify referent、scope、units and semantic role
        -> exact constrained_by assertion + sufficient rationale，or no-op
```

By contrast，a source-native relation such as `reply_to` or `attachment_of` may already be completely stated by its owning
contract、direction and endpoints；adding prose would not improve later use。The learning is therefore not “every Relation needs
a reason”，but “a persisted Relation must retain all meaning required for the intended reuse”。

### Reconciliation with existing InKCre Product truth

The useful semantic is not the manual UI action。It is the distinction between：

```text
candidate relevance
  “these items may be useful together”

persisted contextual commitment
  “these exact items should be read together for this scoped reason”
```

Nowledge obtains authority for the second statement from explicit Human/Agent intent。InKCre already permits explicit or
automated Organization linking，so Human confirmation is not a general prerequisite。Its accepted Product truth instead requires
the operation to state the intended use improvement、correctness and partial-effect boundary；the resulting directed Relation
becomes ordinary graph authority，and its payload meaning belongs to an owning contract rather than a universal relation registry。

The unresolved authority question is therefore narrower：what automatic evidence is sufficient to promote candidate relevance
into one exact graph assertion，and what basis、scope or uncertainty must the owning linking contract preserve。A generated
natural-language reason can explain a judgment but does not prove it。

### Descriptive relation versus operational relation

Open relation vocabulary has a real KISS benefit：it can express `depends_on`、`example_of`、`blocks` or a domain phrase without
pre-designing a complete ontology。This matches InKCre's existing rule that a contract-owned text/JSON payload does not imply one
universal relation-type registry。Lexical normalization identifies spellings；it does not establish shared state or propagation
semantics。The saved reason can make an instance useful when label plus endpoints are otherwise insufficient。

The same openness creates a boundary with P-031 relation-as-force。A free string such as `pricing_assumption_for` can explain why
two information objects should be read together，but downstream machinery cannot safely infer which changes it conducts、in what
direction、to which operation or with what termination law。Current candidate separation：

| Relation responsibility | Required commitment |
| --- | --- |
| Descriptive/contextual linking | exact endpoints、direction and payload sufficient under its owning contract；non-obvious reason when needed |
| Operational/evolution/force semantics | contract/model-owned scope、authority、conducted stimulus、downstream operation and state/no-op law |

This does not require two storage schemas or prohibit one relation from having both responsibilities。It rejects the assumption
that one open label automatically supplies machine-operational semantics。

### Current Product candidate

The strongest learning is **candidate evidence must not be mistaken for persisted relation meaning**：similarity、graph proximity
or an LLM suggestion may locate a pair，but an accepted linking operation must persist a contract-owned semantic assertion whose
direction/payload is sufficient for later use。

`Reason` is not universally mandatory and should not become generic UI metadata。When relation name plus endpoints already states
the useful meaning，extra prose may add noise；when the relation is domain-specific or context-dependent，the rationale is part of
the semantic payload because later use otherwise cannot recover why the neighbor changes interpretation。

“Should be read together” is best treated as an intended use effect of a specific relation，not a universal relation type or an
instruction that every application must eagerly fetch both endpoints。Resolvers and retrieval/application contracts retain
their own bounded context-selection semantics。

The material review candidate is therefore a **candidate-to-assertion boundary for contextual linking**：automatic Organization
may persist a link when its owning contract can distinguish candidate evidence from the exact asserted meaning and retain enough
payload to make the latter reusable。No universal vocabulary、mandatory reason field、review workflow or runtime propagation is
approved。

### Heterogeneous interpretation，not universal content structuring

The concrete case used `referent / scope / units / semantic role` to show what could make one relation judgment invalid。Those
are reasoning questions for that case，not a proposed Block/Relation schema。Arbitrary information cannot and should not be forced
into one normalized field set merely to make automatic linking look deterministic。

The Product-consistent mechanism direction is：

```text
heterogeneous Blocks / Relations
  -> exact Resolver interpretation under each owning contract
     -> bounded candidate context
        -> LLM / Agent compares meaning and drafts an exact relation or no-op
           -> Organization validates its output contract and persists ordinary graph authority
```

Resolver supplies faithful、domain-aware usable meaning without acquiring Organization authority。The LLM handles contextual
comparison that does not fit a universal schema，but its output is not self-authorizing truth。Organization still owns candidate
bounds、accepted output shape、correctness/no-op semantics and graph mutation。This is a Product mechanism boundary，not approval
of one prompt、provider、DTO or runtime topology。

### Memory Links closure

D-476 accepts contextual linking as a basic Organization family：candidate evidence remains distinct from persisted assertion；
relation payload retains only the meaning required for reuse；“read together” is a use effect rather than a universal type。
D-477 rejects universal content structuring and retains Resolver + LLM/Agent as the heterogeneous interpretation direction under
Organization authority。

Memory Links adds no new lifecycle、Human review gate or operational force semantics。The mechanism is closed for this study；
future concrete linking behavior must still provide its own Product pressure and exact relation contract before Technical /
Acceptance opens。

## Ontology — Initial Product Inquiry

### Product loss and Nowledge mechanism

Generic extracted types such as `concept`、`product`、`method` and `term` can erase distinctions that matter inside one domain。
Nowledge allows a domain vocabulary such as `cell line / assay / antibody / target / protocol / instrument` to influence entity
extraction，reduce one real-world thing being assigned inconsistent types，and enable graph query by kind。

The important boundary is that this is not a schema for all Memory or relation content。It is an optional lens over the extracted
entity layer：unconfigured behavior remains available；unclaimed words stay visible；unknown types do not fail extraction；and the
vocabulary may cover only part of the graph。

### Bottom-up vocabulary，not top-down normalization

Nowledge drafts vocabulary from the actual graph and reports proposed coverage。Type consolidation、promotion and retyping are
previewed against affected entities；retired types remain aliases。Its mechanism shape is therefore：

```text
existing heterogeneous graph
  -> observe recurring domain nouns and current type drift
     -> propose a partial vocabulary with coverage/effect evidence
        -> use accepted vocabulary as an interpretation/extraction lens
           -> leave unclaimed information valid and visible
```

This ordering matters。The graph provides evidence for vocabulary；the vocabulary does not decide what information is admissible。
The design is open-world and progressive rather than a closed ontology that every object must satisfy。

### Concrete case：generic types erase a query-useful domain distinction

Assume a research info-base contains independently collected statements such as：

```text
I1: “Cetuximab reduced EGFR phosphorylation in A549 cells under the viability assay。”
I2: “Cetuximab binds EGFR。”
I3: “A549 is a non-small-cell lung cancer cell line。”
```

A generic extractor may represent `Cetuximab = product`、`EGFR = concept`、`A549 = term` and `viability assay = method`。The
information remains present，but the generic words discard distinctions needed by a later question：

> Which cell lines were used in assays of antibodies targeting EGFR？

Pure semantic retrieval may still find some source text，but it cannot rely on the graph to distinguish an antibody from a
target、an assay from an arbitrary method，or a cell line from a general term。The observable loss is weak candidate precision
and graph query/navigation，not an aesthetically generic graph。

A domain vocabulary lens can guide Resolver/LLM interpretation toward：

```text
Cetuximab       -> antibody
EGFR            -> target
A549            -> cell_line
viability assay -> assay
```

Later Organization/query can use those role distinctions to form a smaller candidate subgraph before reading source evidence。
The original statements remain untouched，and a new term such as `patient-derived organoid` remains valid even if the current
vocabulary does not classify it。

### Three responsibilities Nowledge's Product story partly combines

| Responsibility | Question | What vocabulary can and cannot do |
| --- | --- | --- |
| Vocabulary alignment | Which domain distinction should interpretation use？ | Can replace generic words with useful domain language。 |
| Entity identity resolution | Do two mentions denote the same real-world thing？ | Type compatibility is evidence，not identity proof；aliases/context still matter。 |
| Query/application | How is information selected or navigated by kind？ | Can consume type assertions；the vocabulary does not itself execute or validate the query。 |

Nowledge says domain vocabulary reduces one real-world thing landing under two types。That is a plausible benefit，but it must
not be upgraded into “typing solves entity resolution”。Likewise，a coloured graph and coverage count expose vocabulary effects；
they do not establish Product value unless a query/Organization failure depends on the missing distinction。

### Initial InKCre boundary

InKCre persists Blocks and Relations as graph authority and has no accepted universal entity-node/type ontology。The transferable
question is therefore not “which entity types should InKCre add？” but：

> Can an optional、partial domain vocabulary improve Resolver/LLM Organization interpretation and later query without becoming
> a storage schema、Block classification or ingestion gate？

This directly applies the D-477 correction。Resolver/LLM can use vocabulary as context when interpreting heterogeneous
information；absence or non-coverage must remain an ordinary condition。No Entity Block、type registry、migration、Human review UI
or extraction behavior is approved。

### Positioning：optional interpretation context，not an Organization capability

The earlier “open-world vocabulary lens” candidate was premature because it described a desirable shape before establishing its
place in the Product。The dependency is：

```text
specific LLM-based Organization / entity-extraction operation
  + optional domain vocabulary context
  -> organization-authored entity/type assertions
     -> later linking / candidate formation / query may consume them
```

The vocabulary does not itself organize information、resolve entity identity or execute a query。It guides another operation's
interpretation。A closer InKCre name would be **domain vocabulary context/profile**，not a broad Ontology capability。

It is a side input to one concrete judgment，not a stage in the generic Organization sequence：

```text
                                      optional domain vocabulary
                                                 |
candidate information -> Resolver meaning -> LLM / Agent judgment -> no-op or graph assertion
                                                 ^
                                                 |
                                  operation-owned rules / context
```

Existing InKCre authority already leaves this seam available without naming an Ontology subsystem：the Organization/application
caller prepares the initial Message and owns domain Tools；the selected Agent definition owns reusable system prompt/model/tool
configuration；Resolver owns exact Block interpretation。A later concrete operation could place stable vocabulary in its selected
Agent guidance or dynamic scoped vocabulary in caller-prepared context，but choosing that delivery surface is Technical design。

Vocabulary must not be pushed into Resolver：a Resolver explains what one Block means under its persisted contract，while a
domain vocabulary may be selected by a cross-Block operation/use context。It must not be owned by AgentManager either，because
Agent runtime is graph/domain-blind and does not own Organization policy。

Its value is conditional：

- For a structured source whose Resolver/native contract already knows `pull_request`、`issue` or `release`，another vocabulary
  layer may add nothing。
- For unstructured legal documents，a LLM extraction operation might otherwise flatten `matter`、`filing`、`statute` and
  `deadline` into generic concepts；a legal vocabulary can improve that operation's output and later “deadlines in this matter”
  query。
- If no approved Organization/query behavior needs typed entity distinctions，the vocabulary has no standalone Product value。

Optional、partial、open-world、scoped and multi-lens remain useful constraints **if** such a concrete operation appears，but they
do not justify creating the operation or a vocabulary subsystem。Persistence of type assertions is likewise downstream of that
missing Product behavior。

### Ontology closure：no transfer

D-478 rejects introducing domain vocabulary into the current Organization design，including as a seemingly lightweight context
profile or supporting principle。Nowledge Ontology has understandable value inside its entity-extraction/type-query Product，but
InKCre currently has no approved consumer behavior、observable failure or Product owner that requires it。

No vocabulary capability、profile、lens、context contract、entity type system or persistence question remains open。If a future
concrete Organization behavior encounters a domain-language failure，that unit must recover the need from its own evidence rather
than inheriting this abandoned candidate。Ontology is closed with **no current transfer**。

## Entity / Relationship Extraction — Initial Product Inquiry

### Nowledge mechanism and apparent loss

Nowledge automatically runs entity extraction when new Memories arrive，alongside EVOLVES detection。It reads Memory content and
persists extracted entities and relationships into its knowledge graph。Later entity-mediated search、graph traversal and
community detection can use those explicit nodes/edges。

The apparent Product loss is that important meaning may exist only inside prose：two documents can both mention PostgreSQL，or
one sentence can state that a project depends on a technology，without those references becoming navigable graph facts。Search
can rediscover textual similarity per query，but cannot reliably traverse or reuse an implicit relation that was never
materialized。

### Initial InKCre positioning question

The Nowledge feature name must not preselect an Entity node/type model。From an Organization-action perspective，the mechanism may
be decomposable into already known families：

```text
heterogeneous information via Resolver
  -> recognize a possible referent                              # ephemeral candidate
     -> resolve it to existing identity-bearing information     # identity continuity
        -> connect source information to that unit               # linking / provenance
           -> connect reusable units by an asserted relationship # contextual linking
```

This would make “entity extraction” one specialized composition of breakdown and linking，not a new top-level capability。The
study must still establish a concrete use failure and why ordinary semantic/graph retrieval is insufficient before accepting
any transfer。Creating identity information when no reusable referent already exists is a separate materialization behavior，not
an automatic consequence of recognizing a noun。

No Entity Block、entity identity resolver、relationship vocabulary、automatic trigger or persistence behavior is approved。

### Concrete case：an implicit shared referent hides a cross-document risk

Assume the info-base contains：

```text
I1 — Atlas rollout plan
“Atlas production will stream changes through logical replication on pg-prod-3。”

I2 — incident note
“A subscriber outage left a replication slot on pg-prod-3 retaining 800 GB of WAL。”
```

A query about `Atlas rollout risk` can retrieve I1 while missing I2 because the incident never names Atlas。Semantic similarity
may sometimes bridge the wording，but it does not provide a stable、auditable path explaining why this incident belongs in Atlas
context。

If `Atlas` and `pg-prod-3` are resolved to reusable referent anchors，Organization can express：

```text
I1 ----mentions/grounds----> Atlas
Atlas ------uses-----------> pg-prod-3
I2 ----reports_about-------> pg-prod-3
```

A later graph/query operation starting from Atlas can now reach I2 through an exact path and inspect the original evidence。The
use improvement is cross-document risk discovery through a shared referent，not displaying more nouns in the graph。

The mechanism becomes harmful if `pg-prod-3` in one document names a production host while another uses the same string for a
retired test alias。A false merge makes unrelated information reachable as if it shared identity；a false split merely misses the
connection。Identity resolution is therefore the hinge，and unresolved mention is a valid result。

### Five responsibilities packaged as “entity extraction”

```text
Resolver meaning
     -> mention recognition                    # ephemeral candidate
     -> referent resolution                 # existing referent / absent / unresolved
        |-> referring-fragment anchoring    # selected text materializes only after resolution
        |-> anchor materialization          # separate Product behavior when absent
        `-> unresolved / no-op              # when identity is ambiguous
source-grounded meaning
  -> relation assertion                     # only when exact meaning is supported
```

These responsibilities have different authority and valid no-op behavior：

| Responsibility | Output | Valid no-op / boundary |
| --- | --- | --- |
| Mention recognition | candidate span/name/context | mention does not identify a referent worth resolving |
| Referent resolution | identity match or unresolved candidate | ambiguity remains unresolved；type/name similarity is insufficient |
| Referring-fragment anchoring | `source --has mention--> selected-text fragment --refers to--> existing identity-bearing information` | no sufficiently resolved existing referent |
| Anchor materialization | new identity-bearing information，if separately justified | not part of the current transfer candidate；never create a bare graph junction merely for completeness |
| Relation assertion | organization-authored semantic Relation with source basis | text does not support exact direction/meaning |

Nowledge's preview/apply split correctly keeps LLM extraction output non-authoritative until a write operation。Its aggregate
`extraction_confidence` does not resolve the harder per-entity identity and per-relation support questions，and cannot safely be
promoted as one admission threshold。

### Current Product candidate：existing-referent anchoring as a basic linking composition

The transferable candidate is not an Entity subsystem。It is a conservative **existing-referent anchoring pattern** inside the
existing linking family：

1. use Resolver meaning plus bounded graph candidates to recognize a mention and seek existing identity-bearing information；
2. preserve unresolved ambiguity rather than forcing merge or creation；
3. when a source-local expression resolves，materialize only that selected text as an occurrence-local ordinary Block and persist
   `source --has mention--> fragment --refers to--> referent`；persist any separate referent-to-referent Relation only when its own
   exact meaning/direction is supported；
4. expose the resulting path for later graph/query use。

This pattern gives the useful part of entity extraction a Product position without importing Nowledge's Entity node/type
ontology。An existing Block qualifies only when it already carries enough identity evidence to distinguish the referent from
plausible alternatives and can serve as the continuity point for facts across sources or time。Recurrence can strengthen this
case，but is evidence rather than a fixed count threshold。

Automatic **new-anchor materialization** remains outside this candidate。A label-only Entity whose sole purpose is to become a
graph junction is not yet shown to be information in InKCre's sense；calling it “independently reusable” would only rename that
unresolved problem。If no identity-bearing information exists，the current valid result is unresolved/no-op。A later concrete use
failure may justify materializing identity information through breakdown，but that needs its own Product case。

### Entity / Relationship Extraction closure

D-479 accepts existing-referent anchoring as a contextual-linking pattern。New Entity materialization is acknowledged as
potentially valuable but deferred：the current study has not found a credible extraction and identity-establishment pattern that
would justify automatic creation。No Entity node/type、automatic extraction trigger、identity schema or persistence behavior is
approved。D-509 later corrects the exact realization：the successfully resolved selected text becomes an ordinary occurrence-local
Block，preventing a direct Relation from overclaiming the composite source；this is referring-fragment materialization，not new-
referent/Entity materialization。

## Memory Compaction — Initial Product Inquiry

### Product loss must be more specific than “the graph is untidy”

Nowledge runs optional weekly Memory Compaction over similar or redundant Memories。Its candidate planner is read-only；a later
Agent judgment may propose merge、link、summary or review。Confirmed merge remains review-gated，and saved Memory text is not
silently deleted。

Similarity alone exposes at least three possible use losses：

1. **retrieval crowding** — near-identical results occupy a result window；
2. **false evidence multiplicity** — copies look like independent support for one claim；
3. **fragmented graph meaning** — evolution、context and provenance Relations attach to different copies，so no later traversal
   sees the complete local meaning。

Only the latter two necessarily pressure Organization。Retrieval crowding may be solved by an application-owned diversity or
representative projection without changing info-base authority。Compaction is therefore not justified merely by storage size、
node count or visual cleanliness。

### Concrete case：the same number does not establish duplicate information

Assume the info-base contains：

```text
I1 — API operations note, copied from runbook R1
“The public API request timeout is 30 seconds。”

I2 — imported copy of the same R1 paragraph
“Public API requests time out after thirty seconds。”

I3 — batch export guide
“The export worker timeout is 30 seconds。”

I4 — rollout decision dated 2026-08-20
“The public API request timeout is now 60 seconds。”
```

A similarity cluster can place all four together，but the correct meanings differ：

- I1/I2 may duplicate one source assertion；treating both as independent support inflates evidence。
- I3 shares wording/value but differs in referent and scope；merging corrupts both facts。
- I4 changes the API fact over time；it belongs in a supersession lifecycle rather than duplicate merge。

Even I1/I2 require provenance evidence。If two independent operational measurements both report 30 seconds，their proposition
may be equivalent while their evidence is not duplicate。Destructive coalescence would erase corroboration and source
attribution。

### “Compaction” packages relationship triage，not one merge law

```text
similarity / graph proximity
  -> bounded candidate
     -> Resolver-supported relationship judgment
        |-> same source-native identity / replay        # Collection reconciliation
        |-> duplicated assertion from one provenance    # possible duplicate relation/merge
        |-> equivalent claim from independent evidence  # preserve source multiplicity
        |-> partial overlap / complementary content     # linking or synthesis
        `-> temporal or epistemic change                # evolution
```

This recovers why Nowledge can choose merge、link or summary from one candidate cluster：the candidate signal does not determine
the semantic operation。It also preserves the existing InKCre rule that stable source identity may authorize reconciliation，
while fuzzy content similarity cannot overwrite uncertain graph state。

### Current inquiry edge

The promising transferable idea is **redundancy relationship triage**：use similarity only to bound candidates，then route each
case into its owning model rather than applying generic compaction。

Query-side representative selection fixes only result crowding。It cannot prevent two imported copies of one R1 assertion from
being counted as two independent sources by a later Crystal/evidence operation，nor can it expose their non-independence to
evolution、linking or graph traversal。That is a graph-level use failure：the info-base lacks an explicit fact about assertion
multiplicity。

The current non-destructive candidate is therefore a **provenance-aware duplicate-assertion relation**：

```text
same referent + scope + temporal applicability + semantic assertion
  + evidence that both Blocks reproduce one provenance occurrence
      -> persist duplicate-assertion relation
         -> evidence consumers count the component once
         -> query may collapse it to one representative
         -> traversal may reach each record's provenance/context without rewiring it
```

Independent sources expressing the same proposition do **not** receive this relation；they retain separate evidence and may
participate in the already accepted evidence-stance model。Partial overlap routes to linking/synthesis，and changed applicability
routes to evolution。

This is intentionally not a physical merge：all Blocks、source provenance and adjacent Relations remain in place。The relation
adds the missing multiplicity fact；a consumer may derive a representative without Organization persisting another mutable
representative state。It is also a new concrete P-031 observation：the relation may conduct “count once” semantics to an evidence
operation，but no generic force framework follows from that observation。

### Memory Compaction closure

D-480 accepts provenance-aware duplicate-assertion linking as the minimum useful InKCre return。The relation records that
multiple Blocks reproduce one provenance occurrence；it does not collapse independent evidence or physically merge records。
Exact relation contract、candidate trigger、judgment context and consumer projection remain unapproved。Memory Compaction is
closed for this study。

## Exploratory Agentic Execution Topology Across Parallel Organization Behaviors

### Why the topology has now earned a Product position

Entity identity、duplicate assertion、evolution scope、contextual relation and synthesis eligibility are open-world semantic
judgments。Resolver projections make heterogeneous information readable，but no finite field schema or deterministic ruleset can
generally decide those meanings。Without a general semantic reasoner，InKCre would have to abandon many useful Organization
behaviors or restrict them to narrow source-native cases。

The repeated Nowledge mechanisms and existing InKCre rumination support a reusable execution topology：cheap machinery may supply
initial evidence；an LLM-backed Agent follows one behavior's direction/SOP to understand、explore and act；ordinary graph
authority owns what becomes durable。

```text
one Organization behavior invocation
  -> optional deterministic / low-cost initial candidate seeds
     -> Agent receives that behavior's direction and methodology / SOP
        <-> iterative retrieval / graph navigation / Resolver tools as needed
           -> LLM/Agent semantic judgment and action
              |-> no-op / unresolved
              `-> behavior-consistent graph command
                    -> ordinary validation and Block/Relation persistence
```

This cross-mechanism pattern no longer precedes evidence in violation of D-463。It is induced after Knowledge Evolution、
Crystals、Memory Links、Entity Extraction and Memory Compaction independently converged on the same separation。

### What “LLM as the universal part” does and does not mean

The LLM/Agent is a broadly applicable **open-world semantic reasoner**。It may compare heterogeneous content、preserve scope and
uncertainty、explore beyond initial evidence、choose among behavior-valid outcomes and directly invoke allowed graph tools。It is
not the owner of source truth or persistence，and its generality does not create one universal Organization method。

| Responsibility | Owner / mechanism | Boundary |
| --- | --- | --- |
| Direction、methodology/SOP、trigger and result meaning | each Organization behavior | rumination、evolution、linking and synthesis remain parallel owners |
| Initial candidate seeds | behavior-chosen exact mechanisms、graph neighborhoods、lexical/semantic retrieval or simple clustering | improve starting relevance/cost；do not normally close Agent visibility |
| Heterogeneous meaning and further discovery | exact Resolvers plus read/retrieval/navigation Tools | preserve content contracts while enabling iterative exploration |
| Semantic judgment/action | behavior-directed LLM-backed Agent | may reason over multiple turns and invoke allowed mutation Tools |
| Durable authority | ordinary graph command validation/persistence | Blocks/Relations remain authority；source meaning is not rewritten by inference |

Initial candidate recall affects efficiency and the quality of the starting point，but does not necessarily cap discovery。An
exploratory behavior may let the Agent search、follow relations、resolve new Blocks and reconsider its hypothesis。A narrow
mapping/decision behavior may deliberately provide a closed input when exploration adds no value。That distinction belongs to
the behavior's methodology，not a global candidate protocol。

“Universal” therefore means semantic breadth，not omniscience or an unconstrained mega-agent。Resolver availability、tool access、
model-call/resource budgets、behavior methodology and graph validation still shape what can happen；no-op/unresolved remain
first-class outcomes。Simple deterministic Organization behavior also need not invoke an LLM merely to conform to this topology。

### Relationship to current rumination

Current `OrganizationManager.ruminate(block_id)` is one concrete instance：an explicit focal Block selects a bounded direct
neighborhood，Resolver text provides meaning，a configured Agent can draft and submit a graph，and an empty/unsupported result is
a no-op。Its current direct-neighborhood input is an implementation boundary of that behavior/version，not evidence that every
Agentic Organization behavior must remain inside initial candidates。

Rumination、evolution、linking and synthesis are parallel behaviors。There is no targeted-behavior-to-rumination fallback and no
single Organization method that first chooses among them。A behavior may reuse Agent runtime、Resolver/retrieval Tools and graph
submission capabilities while retaining its own complete path from invocation through graph mutation/no-op。

This is why Agent Tools、Agent runtime and AI Provider remain separate：the behavior supplies direction and methodology；Tools
supply capabilities；the runtime conducts turns；the Provider supplies model inference。Reuse at these layers does not collapse
Product behaviors。

D-481 accepts this exploratory Agentic execution topology and withdraws the earlier `candidate-bounded`、per-behavior `planner`
and `rumination fallback` framing。No universal Organization method/API、candidate protocol、Agent prompt、Tool expansion、trigger
or implementation mutation is approved。

## Automatic Labeling — Initial Product Inquiry

### Nowledge mechanism and apparent use

Nowledge automatically assigns 2–4 descriptive Labels to a new Memory，preferring existing Labels when they fit。Labels act as
categories/filters and receive a query-match boost。A separate consolidation mechanism finds canonical forks、near synonyms and
cross-language pairs，then can move assignments from one Label to another after preview/review。

This appears to solve vocabulary fragmentation and make a stable category reusable across queries。But the feature name hides
several different semantic roles：`postgresql` may be an entity/topic，`atlas` a project scope，`incident` an information type，
and `urgent` an Organization-authored priority assessment。Treating all four as the same kind of graph fact is deliberately coarse。

### Concrete case：recall cue versus durable membership fact

Assume an incident Block says：

```text
“A replication slot retained 800 GB of WAL on pg-prod-3 after the subscriber outage。”
```

Possible automatic Labels include：

- `postgresql` because it is a useful lexical/semantic recall cue；
- `atlas` because existing provenance/context establishes that the host belongs to Project Atlas；
- `incident` because the information records an operational event；
- `urgent` because the model predicts priority。

These outputs do not have one authority or one effect：

1. If `postgresql` merely boosts queries，it is a derived application projection。Persisting it as graph authority adds no
   demonstrated information meaning。
2. If `atlas` means “this incident belongs in the context of the existing Atlas information”，it is an ordinary
   source-grounded contextual Relation to an existing referent—already accepted by D-476/D-479。
3. If `incident` controls type-specific behavior，it needs a concrete type/use contract；a generic Label does not provide one。
4. If `urgent` changes priority，it is a new assessment requiring its own meaning and evidence，not category housekeeping。

The stable word is therefore not the Product value by itself。The question is what reusable distinction the assignment asserts
and which later use consumes it。

### Current positioning

```text
label-like output
  |-> lexical recall cue only
  |     `-> application/search projection
  |-> membership/context assertion to existing information
  |     `-> existing-referent contextual linking
  `-> newly materialized named category
        `-> new-anchor materialization，currently deferred
```

Automatic Labeling currently exposes no fourth meaning that requires an independent Organization behavior。Reusing existing
Labels is useful inside Nowledge's Label model，but importing that model would either create parallel string metadata authority
or reintroduce the new-Entity/new-category materialization problem without a reliable admission rule。Likewise，the `2–4` count
and lowercase-hyphen convention are heuristics rather than Product properties。

### Automatic Labeling closure

D-482 closes Automatic Labeling with no independent transfer。Coarse reusable set membership without a more specific semantic
role is not accepted as an InKCre information distinction：persist exact contextual/type/assessment meaning when it exists，and
leave recall cues to application support。No Label node/field、automatic labeling behavior、fixed count、naming convention or
consolidation operation is approved。

## Memory Type Review — Initial Product Inquiry

### Nowledge mechanism and its atomic-Memory assumption

Nowledge assigns every Memory one primary `fact / preference / decision / plan / procedure / learning / context / event` type。
The type helps Agents decide how to use the Memory and supports exact recall filtering。Automatic review revisits weakly typed
Memories in bounded batches，then changes metadata—not content or embeddings—when confidence is high enough。

This works inside a Product that first distils a conversation into standalone durable takeaways。InKCre stores broader
information：a Block may be one semantic unit，but it may also faithfully retain an email、document、message、attachment metadata
or another source-shaped record containing several independently useful statements。Classifying that container with one primary
type can hide an information-boundary problem rather than solve it。

### The type list mixes several independent dimensions

| Nowledge type | Dominant question it appears to answer | Why it can overlap |
| --- | --- | --- |
| `fact` | is this presented as an assertion/reference？ | a decision、event or procedure can contain factual assertions |
| `preference` | what does an actor favor？ | a preference can ground a decision or standing rule |
| `decision` | what choice was made？ | it can simultaneously create a plan and prescribe a procedure |
| `plan` | what future action/state is intended？ | a decision may authorize that same future action |
| `procedure` | how should an action be performed？ | it may be encoded inside a decision、rule or learning |
| `learning` | what realization was acquired？ | the learned content may itself be a fact or procedure |
| `context` | what frames another use？ | almost any information can have contextual force relative to another |
| `event` | what happened？ | an event can include a decision、observation and outcome |

These are use-role properties from different axes，not mutually exclusive object classes。This repeats the structural lesson
from evolution：properties make information eligible for different use/model behavior；they do not partition the info-base。

### Concrete use failure：one source passage carries several roles

```text
“Approved today：after every schema migration，run checksum verification；the rollout starts next Monday。”
```

The passage simultaneously contains：

- an event：approval happened today；
- a decision：checksum verification is required；
- a procedure fragment：run it after every schema migration；
- a plan：rollout begins next Monday。

Choosing `decision` hides the exact procedure from by-type use；choosing `procedure` hides the governance decision and future
plan。Returning four coarse types on the same container improves recall facets but still forces every later use to reopen the
passage and recover the independently useful units。

### Product return：persist an exact source-relative role，without privileging the source vocabulary

The earlier candidate used semantic roles only inside the Agent's breakdown judgment and proposed generic provenance links to
the resulting units。That leaves later use to infer each unit's role again and therefore fails to preserve the distinction that
made the Organization operation valuable。

When a behavior extracts independently reusable information，an exact source-relative role can be preserved in ordinary open
Relation content：

```text
Source Block S
  |--event------> E  “approval happened today”
  |--decision---> D  “checksum verification is required”
  |--procedure--> P  “run it after each schema migration”
  `--plan-------> L  “rollout begins next Monday”
```

Under the established directional reading，the target is the source's `<relation-content>`。The relation therefore does two jobs
without typing the target Block：it preserves provenance and states how the source presents or contributes that information。
One target may receive several role Relations，and one source may produce several independently reusable targets。

The example uses `event / decision / procedure / plan` because those meanings are present in the passage，not because Nowledge's
eight primary types define an InKCre starter vocabulary。D-493 removes that privilege：`fact` risks being read as base-wide truth，
`learning` assumes an epistemic subject，and `context` often fails to say how another item matters。Every behavior must choose the
exact open Relation meaning that preserves material actor、scope、time、authority and later-use distinction。Any Nowledge type word
may still be used when it is in fact the most accurate relation content。

### Revised Product candidate

```text
source/coherent information via Resolver
  -> behavior-directed Agent explores sufficient context
     -> identify independently reusable information and its source-relative roles
        |-> create or reuse information unit(s)
        |-> persist source -> unit Relation(s) using exact source-relative meaning
        `-> insufficient basis / no reusable distinction -> no-op
```

Breakdown is one possible graph action，not the entire return。If an appropriate target Block already exists，the behavior may
add the role Relation without creating another unit。Conversely，a derived Block should not be created merely to satisfy every
role word found in a source vocabulary。The source remains authoritative；the role Relation is Organization-authored graph meaning。

This applies the existing D-330 convention：Relation content names the information role (`text / transcript / subtitle`) rather
than the extraction implementation。The study clarifies that the same open rule can preserve source-relative semantic roles；it
does not add a preferred list alongside that rule。

### Memory Type Review closure

D-493 corrects D-483：the source-relative、non-exclusive Relation-role principle remains，while the eight Nowledge words return
to source evidence/examples and have no starter-guideline status。No registry、Block type field、mandatory breakdown、automatic
reviewer、confidence threshold or consumer behavior is approved。The review is closed；the broader representation fit is
developed separately in the
[info-base representation lens](representation-lens.md)，rather than expanding this mechanism file into another architecture
monolith。

## Post-Monolith Mechanism Shards

New mechanism inquiries are maintained as separate Product shards so one-at-a-time review remains directly addressable without
growing this historical design file：

- [Insight Detection](product/insight-detection.md)：closed under D-485/D-493；cross-context pattern induction remains a D-472
  synthesis candidate/qualification heuristic。
- [Working Memory / Daily Briefing](product/working-memory.md)：closed under D-486；near-term Application context assembly is a
  downstream use projection，not durable Organization output。
- [Skill Suggestions](product/skill-suggestions.md)：closed under D-487/D-493；procedure synthesis is a D-472 application，while
  downstream capability compilation、testing、activation and distribution remain separate。
- [Rule Suggestions](product/rule-suggestions.md)：closed under D-488；descriptive regularity cannot acquire normative force
  without an authorized source and owning downstream contract。
- [Memory Freshness / Decay](product/memory-freshness.md)：closed under D-489；use salience is a scoped projection prior，not
  semantic currentness or epistemic support。
- [Extension-influenced Organization](product/organization-extension-pressure.md)：D-490 cross-unit pressure；keeps Core/Product/
  Extension ownership independent and defers the seam until one concrete behavior proves it。
- [Community Detection / Graph Analysis](product/community-detection.md)：closed under D-491；structural results remain
  projections/candidate seeds and durable thematic meaning routes to synthesis。
- [Flags / Memory Maintenance](product/flags-memory-maintenance.md)：closed under D-492；routes its packaging to concrete owners
  and retains only the P-032 evidence-coverage pressure。
- [Nowledge transfer audit](audit/nowledge-transfer-audit.md)：active after the final mechanism closed；reviews accepted study
  returns for over-learning、copied Memory-product assumptions、duplicate local truth and abstractions without added power。

Decision shards remain accepted task-state authority；the linked Product shard owns each mechanism's coherent analysis。
