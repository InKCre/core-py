# Info-Base Representation Lens

- **Status**: accepted Product-study lens under D-484；not yet promoted durable Product or Technical truth。
- **Purpose**: explain why InKCre can carry open-ended kinds of information，then use that explanation to judge individual
  Nowledge transfers without copying its Memory ontology、fields or application projections。
- **Evidence base**: current shared Product TDD says Blocks and Relations are persisted information authority；a Resolver
  interprets hydrated content plus the direct Relations required by its exact contract into derived use-facing meaning；Storage
  owns pointer/bytes mechanics only。Repository-local authority design says retrieval projections and Agent execution do not
  acquire graph、Resolver or Organization authority。

## Precise Claim

“Info-base can represent everything” means that its small semantic kernel can be extended to retain and relate **arbitrary
information** without first admitting every future domain into one universal schema。It does not mean that the system already
understands every object in reality，can verify every assertion as true，or can answer every query merely because bytes were
stored。

The kernel has four complementary responsibilities：

| Element | Representation responsibility | What it does not imply |
| --- | --- | --- |
| Block | gives one information unit persisted identity、addressability and a content/resolver boundary | one universal entity class or atomic factual claim |
| Resolver | turns heterogeneous hydrated content plus contract-required local graph context into use-facing meaning | another persisted authority or universal interpretation algorithm |
| Relation | states directed、contextual meaning between two addressable information units | a closed predicate registry or truth merely because an edge exists |
| Graph | composes local meanings and Relations into larger structures、paths and reusable distinctions | one canonical worldview、taxonomy or automatic organization method |

Storage is necessary infrastructure but not a fifth semantic authority：it turns an opaque pointer into actual bytes。An
**internal Organization Agent** may explore and propose meaning while executing one behavior，but validation and persistence
still return to ordinary Block / Relation graph authority。This is distinct from a **downstream Agent consumer** such as the
connected Agent served by Nowledge；InKCre's neutral information model does not privilege that consumer over Humans or
Applications。

## Meaning Is Composed，Not Located In One Field

A useful conceptual model is：

```text
local meaning(B)
  = Resolver[B.resolver](hydrate(B.content), contract-required local Relations)

contextual meaning(R: A -> B)
  = local meaning(A)
    + direction
    + exact R.content under its owning contract
    + local meaning(B)

larger usable meaning
  = bounded composition of local meanings and contextual meanings along relevant graph paths
```

This is not an implementation algorithm。A Resolver explicitly chooses which direct Relations its versioned contract requires；
consumers choose bounded paths and projections。That contract boundary prevents “the whole graph explains every node” from
becoming circular、unbounded interpretation。

Resolver and Relation are therefore dual rather than interchangeable：

- Resolver answers **what usable meaning this information exposes in a stated context**。
- Relation answers **how this information is situated relative to other information**。

Block identity makes both statements referable and reusable。The open-ended representational capacity comes from combining
intrinsic/local interpretation with extrinsic/contextual composition，not from making Relation content or Block content fit one
universal structured schema。

### Existing implementation pressures

This composition is already observable rather than merely aspirational：

- `EmailResolver` combines canonical email content with role-bearing Relations to body、MIME-part、participant、mailbox、flag、
  parent and reference Blocks to produce `SolvedEmail`。Neither the root JSON nor any one edge is the whole usable email。
- `FeedItemResolver` combines source-native item content with outgoing `feed`、`enclosure` and `full_text` Relations，and gives
  some edges explicit cardinality/integrity laws。This demonstrates why operational graph meaning belongs to an owning contract，
  not to free-text resemblance alone。
- `RelationManager.get_text()` projects one Relation as endpoint label + exact Relation content + endpoint label。A Relation's
  semantic retrieval input is therefore intentionally endpoint-dependent；its content string alone is incomplete meaning。
- Resolver selection is exact and versioned，while solved content remains a runtime projection。This permits semantic evolution
  without pretending that one decoded view is a second durable object store。

These examples also correct an overstatement：a Resolver is not simply a decoder of `block.content`。It can be the contract owner
for how one addressable root and selected local graph facts become a coherent use-facing value。

## How The Kernel Extends Without A Universal Ontology

New representational needs can enter at different seams：

1. A new source-shaped or semantic information kind can add an exact Resolver contract while remaining an ordinary Block。
2. A new contextual distinction can use precise open Relation content and an owning behavior/consumer contract while remaining
   an ordinary Relation。
3. A recurring multi-information structure can be expressed as a graph pattern before there is evidence for a new core type。
4. Application search、ranking、facets or views can project those authorities without becoming a second persisted ontology。

This gives InKCre an **open-world extension model**：unknown future meaning requires new interpretation or relation contracts，
but does not require redesigning one closed base taxonomy。The cost is deliberate：open text/JSON Relation content is not
automatically interoperable。Operational effects require an explicit producer/consumer contract rather than guessing from a
similar word。

## Relation Carries More Than Association

Relation can preserve several kinds of contextual meaning，often simultaneously：

- **provenance / attribution** — where information came from or whose assertion it is；
- **semantic role** — the source presents the target as text、decision、plan、procedure、event or another exact role；
- **logic / evidence stance** — information supports、challenges、refines or supersedes another scoped assertion；
- **composition** — several source units contribute to one provenance-preserving synthesis；
- **use consequence** — a model-scoped Relation can change default recall、frontier selection、confidence or reconsideration。

The last item is the emerging “Relation as a force path” insight。An edge can conduct an effect to a later projection or derived
artifact，not only say that two nodes are associated。A force is never implied by generic connectedness：its kind、direction、
scope、consumer and termination/no-op law must come from the owning model。Current cases justify keeping this as a research
pressure，not building a generic propagation framework yet。

## Representation Is Not Use Readiness

Several failures remain possible even when information is representable：

| Claim | Additional requirement |
| --- | --- |
| the bytes can be retained | suitable Storage and exact Block/Resolver identity |
| the information can be interpreted | available Resolver contract and sufficient local context |
| the assertion can be trusted | source、actor、scope、time、provenance and relevant evidence—not the `fact` word alone |
| the information can be found | retrieval projection、candidate generation or graph navigation |
| two producers/consumers agree on an edge | shared owning Relation-content contract |
| organization improves future use | one behavior-specific SOP、semantic outcome、graph effect and honest no-op law |

This distinction is important for Organization。An internal LLM-backed Organization Agent can perform open-world semantic
exploration across heterogeneous Resolver outputs and graph context，but it does not make candidate coverage、truth、authority or
future usefulness automatic。Its result is one behavior-owned graph proposal，not “understanding” that silently changes the
info-base，and not a context bundle for a privileged downstream Agent。

## Nowledge Transfer Questions

For each remaining Nowledge mechanism，ask in order：

1. **Independent information** — does the mechanism create or preserve something independently referable and reusable？If yes，
   an ordinary Block may be appropriate；if not，do not materialize a node for visual symmetry。
2. **Local interpretation** — is the distinction about how heterogeneous content becomes usable？If yes，it may belong to an
   exact Resolver contract rather than Organization。
3. **Contextual meaning** — is the distinction source-relative、between information units or model-scoped？If yes，prefer precise
   Relation content and graph topology over an intrinsic Block type/field。
4. **Application projection** — is it only a search facet、score、label or display convenience derivable from authority？If yes，
   keep it in the application layer。
5. **Organization behavior** — must the system make an open-world semantic judgment and persist a reusable graph distinction？If
   yes，define that specific behavior's direction/SOP、authority、graph effect and no-op law；do not invoke one generic method。
6. **Information preservation** — would replacement、merge or cleanup discard provenance、disagreement or prior versions？First
   test whether Relation、evolution law、append-only versions or synthesis can preserve them。
7. **Operational force** — will an edge affect recall、currentness、confidence、propagation or another consumer？Name the exact
   owning contract；otherwise treat it as descriptive graph meaning only。

### Default transfer discipline

Nowledge features often package source information、Organization judgment、application projection and downstream Agent behavior
into one user-facing mechanism。The default study operation is therefore decomposition rather than feature cloning：

```text
source feature packaging
  -> separate information / interpretation / relation / organization / downstream-use responsibilities
     -> map each transferable meaning into an accepted InKCre model
        -> propose a new method only for an irreducible reusable distinction left over
```

“Irreducible” means that forcing the distinction into an accepted model would materially lose its semantic outcome、authority、
scope、graph effect or honest no-op law。Novel terminology、a separate UI object、schedule or source-product lifecycle is not by
itself evidence of a new Organization method。Conversely，this discipline must not erase a real residual merely to minimize the
method count。

## Immediate Re-Reading Of Accepted Mechanisms

- Memory Type Review types fit Relation-content guidelines because they describe how a source presents a target；they are not a
  complete intrinsic classification of the target。
- Knowledge Evolution fits overlapping Relation models because currentness、refinement and evidence stance are contextual laws，
  not one Memory object's global state。
- Crystals fit derived information Blocks plus provenance-preserving n-ary Relations；dependency response can travel through
  those Relations without inventing a symmetric Crystal lifecycle object model。
- Entity Extraction should not force new Entity nodes until identity-bearing reusable information can be established；linking an
  existing referent is the safer current return。
- Automatic Labeling disappears as one mechanism because its lexical、membership、type and assessment meanings route to
  different authorities。

This lens does not approve a new schema、Relation registry、Resolver API、generic force engine or Organization runtime。Its current
job is analytical：make each Nowledge transfer justify where its meaning lives and what later use can legitimately consume。
