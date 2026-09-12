# Minimal Mechanisms And Consumer Contracts

- **State**: accepted minimal shared-mechanism foundation under D-500/D-520；exact models and read placements are closed。
- **Question**: which mechanisms are genuinely shared by the accepted exact models，and what must exist after mutation for the
  promised later-use affordance to be real？
- **Method**: place every proposed component on the D-498 axis，then remove it unless current code lacks a simpler capability and
  at least one accepted model would otherwise fail。

## Result In One View

```text
model-owned occasion/candidate function
  -> existing Resolver + lexical/semantic retrieval + graph navigation
     -> optional outer Agent adapter
        -> shared read-only exploration Tools
        -> model-specific graph-mutation Tools
           -> exact model proposal/command
           -> existing InfoBase managers in one caller-owned transaction
              -> exact semantic Relation content
              `-> ordinary synthesis Block + exact source-basis Relations
                 -> existing graph/retrieval use
                 + Resolver/Graph Navigation/application reads where raw traversal is insufficient
```

There is no common Organization runtime、behavior entity、candidate protocol、judge interface、event stream、evaluation ledger、
Relation Resolver or graph ontology in this result。

## Reuse Before Addition

| D-498 position | Existing owner reused directly | Missing remainder |
| --- | --- | --- |
| candidate seed | `BlockManager.get_recent/get_random`、lexical and semantic retrieval、exact Relation queries | model-specific candidate functions only |
| evidence assembly | `ResolverManager` text/label/solved projection and `GraphNavigationRetrievalManager` | thin read-only Agent Tool adapters when an Agent is selected |
| judge | `AgentManager` or `AIManager` as outer execution choices | model-specific prompt/SOP and proposal schema；no common judge protocol |
| validation/mutation | `BlockManager`、`RelationManager`、caller-owned `SessionLocal` transaction | exact model methods on concrete BehaviorResolvers；generic `submit_graph` is too permissive and additive for these contracts |
| automatic carrier | exact `JobHandler` + Cron occurrence mechanics | one Job path per independent execution family，not per inventory row |
| graph use | exact-content graph navigation、Relation semantic retrieval、Block lexical/semantic retrieval | one Block-anchored supersession Resolver projection plus one bounded connected-components Graph Navigation query only |
| extension delivery | extension startup precedes Job catalog sync and may register exact Resolver/Tool/Job implementations | no generic Organization contribution registry until a concrete extension cannot compose these seams |

The retrieval Managers remain their own application owners。Organization calls them to acquire evidence；it does not wrap them in
a second `OrganizationContext` facade or copy their result schemas。

## Durable Relation Semantics：Keep Content Semantic

Every currently accepted relation-producing model has one assertion whose meaning can be carried by endpoint identity、direction
and concise Relation content：

| Relation content | Direction | Assertion |
| --- | --- | --- |
| `supersedes` | newer -> predecessor | newer information displaces the predecessor under the model-qualified continuity/scope |
| `refines` | refinement -> predecessor | newer information adds non-dominating refinement under proven continuity |
| `supports` | evidence -> assertion | source-grounded evidence supports the target scoped assertion |
| `challenges` | evidence -> assertion | source-grounded evidence challenges the target scoped assertion |
| `has mention` | source -> referring fragment | source contains this addressable referring occurrence |
| `refers to` | referring fragment -> existing referent | this selected source expression denotes the existing identity-bearing information |
| `duplicates assertion` | lower Block ID -> higher Block ID | both endpoints reproduce one scoped assertion from one provenance occurrence |
| `synthesis` | source -> derived synthesis | the target is a synthesis formed partly from this source；all incoming `synthesis` edges are the exact derivation basis |

The feature set also reuses one ordinary version-continuity Relation rather than treating every edit as supersession：

| Relation content | Direction | Assertion |
| --- | --- | --- |
| `edited` | older -> newer | the newer Block is an edit-version of the preserved older Block；no dominance/refinement follows automatically |

These values are graph meaning，not serialized protocol identifiers。They remain directly readable through
`RelationManager.get_text()` and semantic retrieval while also supporting the repository's exact `from_ + to_ + content`
identity、`fetchsert()` and graph filtering。The model command owns the exact spelling and direction；generic Relation code does
not parse a namespace or dispatch to Organization。

Do not put namespace、implementation owner or version suffixes in `content`。If a future meaning is materially different，give
that Relation a different semantic phrase；if only the command/API changes，version the command contract outside the graph fact。
Likewise，do not introduce a common JSON envelope merely to make arbitrary relation prose machine-shaped。

This simplicity imposes an important correctness boundary：the whole endpoint information units must support the assertion。If
one Relation is true only for an unaddressable sentence、scope or unit hidden inside a larger Block，the model must abstain；it may
not hide a second fact model in opaque Relation JSON merely to force a write。A separately justified breakdown/synthesis operation
may first create addressable information，but this Unit does not invent a universal extraction step。

The open contextual-linking family therefore receives no generic content or write command。Only its accepted exact model，existing-
referent anchoring，gets a contract。A future link whose reason is not recoverable from endpoints/direction must define its own
semantic content and consumer at that time，as required by D-476。

### Relation meaning does not prove producer identity

The existing authenticated graph API can write arbitrary Relation content；the database records no per-Relation producer。The
semantic phrase identifies the asserted relationship，not a security principal or execution history。Automatic judges cannot
submit arbitrary relation prose because their model-specific Tools call validating commands，but an authorized generic graph
writer can make the same assertion。Adding provenance/actor state solely to distinguish which code path wrote an otherwise
identical graph fact is not currently justified。

## BehaviorResolver-owned exact mutations

| Semantic owner | BehaviorResolver mutation method | Required validation/effect |
| --- | --- | --- |
| evolution | `record_supersession(newer, predecessor)`、`record_refinement(refinement, predecessor)`、`record_evidence(evidence, assertion, stance)` | distinct existing endpoints；model-owned direction/content；relation fetchsert |
| synthesis | `create_synthesis(proposal, previous_synthesis_id?)` | proposal has non-empty text and at least two distinct existing sources；create/reuse a derived text Block identified by text + exact source basis；fetchsert every source->derived basis edge；when changed，fetchsert previous->new `edited`；never decide supersession/refinement inside this command |
| referent anchoring | `anchor_existing_referent(source, selected_text, referent)` | existing source/referent and non-empty selected text；create/reuse one occurrence-local text fragment and fetchsert the two model-owned Relations；no new referent creation or global same-text merge |
| duplicate assertion | `record_duplicate_assertion(left, right)` | distinct existing endpoints；canonicalize lower ID first；model-owned Relation fetchsert |

These methods validate graph shape and mechanical invariants，not the open-world semantic judgment already made by the owning
model。They live on the corresponding concrete BehaviorResolvers and remain callable without a running Agent、AI Provider、Job
or Thread。An Agent explores evidence and produces graph modifications by calling narrow model-specific mutation Tools backed
by these methods；it does not receive unrestricted
`GraphForm` mutation for these runs。Shared Agent Tools are read-only only because retrieval、Resolver reading and graph navigation
are the mechanics common across models，not because the Agent is analysis-only。

`RelationManager.fetchsert()` already gives sequential retry idempotence under the repository's relation identity。The current
Job/Cron path prevents the same Job occurrence and one Cron template from running concurrently。Do not add a global unique
constraint、advisory-lock protocol or evaluation ledger before a demonstrated overlapping-writer failure；concurrent manual or
multi-Cron execution remains a preflight risk to measure，not a reason to redesign all Relations now。

## What Source Basis Means And Why Synthesis Needs It

The **source basis** is the exact set of retained information units from which Organization derived one synthesis。For example：

```text
A: the deadline changed to 15 September
B: the migration requires a seven-day rehearsal
C: Alice owns the rehearsal

S: Alice must complete the rehearsal before the 15 September migration deadline
```

`S` is not a faithful statement copied from any one source。Its limited authority is “Organization derived this combined view
from A、B and C”。Those three sources are its basis。Without that basis，later use cannot inspect the derivation、retain speaker/
source attribution、see concealed disagreement、distinguish independent support or know that replacing A should trigger
reconsideration of S。

The basis is persisted only as ordinary graph meaning：

```text
A --synthesis--> S
B --synthesis--> S
C --synthesis--> S
```

The previous `basis_key` + synthesis Resolver proposal duplicated graph authority inside Block content and added a decoder merely
to repair that duplication。It is withdrawn。The synthesis remains an ordinary `core.text.v1` Block；its semantic identity is
**text + exact incoming source-basis set**，which the synthesis command queries before creating a new Block。The command must not
use plain `BlockManager.fetchsert()` alone because that would merge equal text derived from different bases。

Thus same text + same basis reuses the existing synthesis；same text + different basis remains distinct；changed text appends a
new synthesis。No `basis_key`、new Resolver、Crystal type/table or duplicate source list inside Block content is introduced。

## Automatic Runs Without An Organization Dispatcher

The minimum scheduled topology has seven independent behavior-owned Organization Jobs：

1. rumination：recent/changed、small random fallback and explicitly marked candidates enter the same rumination behavior；
2. supersession；
3. refinement；
4. evidence stance；
5. synthesis：new-set discovery and dependency-response reconsideration enter the same synthesis model；
6. existing-referent anchoring；
7. duplicate assertion。

Each Job parameter names its Agent definition and finite scan/exploration bounds；Cron supplies recurrence。The exact semantic
modules do not read those parameters or import Agent。Recent Blocks plus a small random fallback provide stateless seed coverage；
model-specific positive-edge checks suppress obvious replay，while no-op remains eligible for later reconsideration。An
observable `edited` edge from a source already connected by `synthesis` additionally seeds an affected synthesis run。This
does not promise exhaustive graph classification and does not persist `evaluated`、`unresolved` or cursor state。Bytes that change
silently behind an unchanged external Storage pointer provide no reliable trigger；the run remains explicitly best-effort。

An incoming `candidate for` edge targeting a behavior descriptor is one additional high-priority seed source for that behavior's
Job，not a separate candidate-only Job and not a command。The Rumination Job is therefore a complete automatic behavior path；
explicit focal rumination reuses the same behavior implementation without defining the Job's whole candidate law。

The synthesis reapplication candidate query remains model-local and deliberately over-recalling：take the endpoints of a newly
observable graph change，then reverse-follow their outgoing `synthesis` edges to affected syntheses。`edited` additionally
supplies the old/new frontier；other incident Relations merely cause reconsideration。No Relation content directly authorizes a
new synthesis，and no common force registry or event dispatcher is introduced。

There is no Evolution Job。Supersession、refinement and evidence stance own different candidate、availability、budget、failure and
diagnostic contracts；speculative scan amortization does not justify binding their lifecycles。If implementation reveals repeated
cheap reads，they share an ordinary private query function while the Jobs remain independent。A pair may still be considered by
all three models and receive multiple non-conflicting distinctions；there is no call that asks an Agent which Organization model
to apply。

The Agent has two Tool classes：

- shared read-only exploration Tools：lexical/semantic retrieval、exact Resolver-backed Block read、bounded neighborhood/path；
- model-specific mutation Tools：record evolution、create synthesis、anchor an existing referent or record duplicate assertion。

Initial seeds guide rather than cap this exploration。Mutation Tools stay model-specific。If a model later proves a bounded direct
AI call or deterministic judge sufficient，that adapter can replace its Agent path without changing commands or graph contracts。

## “Consumer” Means A Stateless Read Projection

No new persisted Consumer entity、worker or state machine is proposed。Here `consumer` means code that reads graph authority
according to one model's interpretation law and returns a use-facing projection。Consumer names a semantic responsibility，not
one common implementation owner：

```text
current graph facts -> pure/bounded model read -> result for the present caller
```

Placement follows the projection's natural receiver：

| Projection shape | Technical owner | Reason |
| --- | --- | --- |
| one focal Block + its current graph meaning -> one use-facing Block interpretation | ordinary public Resolver method | Resolver is already the Block-selected interpretation/use surface；the method consumes persisted facts but does not select candidates、judge meaning or mutate the graph |
| caller-supplied Blocks + exact Relation filters -> presentation-neutral topology | Graph Navigation query | this is a bounded read of persisted graph authority；it does not resolve content、judge meaning、rank or mutate |
| topology/retrieval results -> count、representative or ranking for the current request | application/use function | this is the actual request-specific use of the graph result，not graph navigation itself |
| candidate/evidence -> semantic judgment -> graph mutation | exact Organization operation | this is production of the distinction，not its later read |

This corrects the earlier blanket placement in model-owned Manager functions。The exact Organization model still defines the
meaning and traversal law。D-520 further corrects the receiver：interpreting persisted `supersedes` facts is non-trivial
Organization semantics，so the method belongs to `SupersessionBehaviorResolver` and accepts a focal Block ID；it does not become
an information Resolver base method merely because any Block kind may participate。

| Model | Existing later-use path | New computed contract，if any |
| --- | --- | --- |
| supersession | exact Relation is navigable/searchable | bounded `SupersessionBehaviorResolver.read_lineage(focal_block_id, bounds)` traverses only `supersedes` from the focal Block，returning current frontier + retained history graph |
| refinement | exact-content graph traversal exposes refinement lineage | none；no dominance projection is allowed |
| evidence stance | graph navigation and Relation semantic retrieval expose support/challenge with both endpoints | none；no base-wide truth/confidence score is manufactured |
| synthesis | ordinary text Resolver makes the derived Block retrievable；incoming `synthesis` Relations report the exact recorded sources without substitution | none |
| referent anchoring | exact source->referring-fragment->referent path supports graph/path navigation and semantic relation retrieval | none |
| duplicate assertion | Relation preserves every Block and context | bounded `GraphNavigationRetrievalManager.get_connected_components(block_ids, contents=("duplicates assertion",))` expands exact-content connectivity beyond the seed set，returning the seed partition、spanning proof、missing seeds and block/relation truncation；any evidence-sensitive caller applies the count-once law |

These return immutable Pydantic values，not database rows。`SupersessionBehaviorResolver.read_lineage()` follows newer -> predecessor
edges in both directions to recover one bounded lineage，then marks nodes with no incoming supersession edge as current。It is a
behavior-owned typed read over a caller-supplied focal Block；its implementation remains read-only and bounded。
`get_connected_components()` belongs to existing Graph Navigation：it starts from
caller-supplied Blocks，expands only exact Relation contents，treats Relation direction as irrelevant only for connectivity，and
returns singleton as well as multi-Block seed components while preserving persisted Relation direction in the discovered proof
graph。Under D-510 it may traverse non-seed Blocks needed to prove connectivity and reports truncation；those Blocks do not
become caller evidence merely because navigation discovered them。
The duplicate model supplies `duplicates assertion` as the exact filter and the consumer law “one component is one provenance
occurrence”；Graph Navigation itself does not know what a duplicate means。No current concrete consumer is required for that
Organization behavior to exist；synthesis is only one integration case that must not multiply independent corroboration when it
encounters this distinction。Request-specific evidence counting may later reuse the same projection in an Application。

This adds one exact bounded topology query to the existing Graph Navigation manager，not a pattern language、community analysis
or Organization-specific query module。The supersession method uses the existing Resolver-method transport when needed；a
separate transport for connected components waits for a concrete cross-boundary caller。No second persisted projection or
acceptance-only shadow index is created。

When ordinary edits follow append-only `edited` continuity，the synthesis basis prevents one temporal lie：an old synthesis keeps
the exact old source Blocks，while dependency response may append a new synthesis with its own basis and `edited` continuity。
Supersession/refinement express their additional exact semantics without `stale/current` state on the derived Block。This claim
does not extend to undetectable external bytes changing behind an unchanged Storage pointer。

## Extension Consequence

No new Organization extension registry is needed for the demonstrated seam。The current bootstrap starts enabled Extensions
before `JobManager.sync_job_types()`；an Extension can register an exact Resolver、Agent Tool and Job Handler during its normal
startup/import path，reuse the Core read capabilities，and call public exact model commands or contribute a new exact model beside
them。Disable semantics remain the Extension runtime's responsibility；persisted Resolver decoding survives according to the
existing extension contract。

This supports future Nowledge-like first-party packaging without teaching Core an umbrella Organization method。Add a dedicated
contribution interface only when a concrete Extension must alter an existing Core model's candidate、evidence or judgment law and
ordinary module composition cannot express that safely。

## Material Decisions

1. Keep Relation `content` as concise semantic meaning，without namespace、version suffix or common payload envelope；abstain when
   endpoint granularity cannot carry the complete assertion。
2. Preserve synthesis source basis with ordinary `synthesis` Relations；reuse `core.text.v1` and identify replay by text +
   exact basis graph，without `basis_key` or a new Resolver。
3. Reuse existing retrieval/navigation/persistence/Job mechanisms；Agents both explore and produce graph changes，using shared
   read Tools plus model-specific mutation Tools across seven independent behavior-owned Job paths。Six exact mutations live on
   their concrete BehaviorResolvers；one candidate Tool dynamically dispatches to the target Resolver's `record_candidate()`。
4. Add only two stateless reads now：a Block-anchored supersession lineage/frontier Resolver method and a bounded connected-
   components Graph Navigation query that expands exact Relation contents from caller-supplied seeds and returns seed partition、
   spanning proof、missing seeds and block/relation truncation。An evidence-sensitive caller applies the count-once law only to a
   complete result。Other
   affordances are already available through ordinary retrieval、Resolver and graph navigation。
5. Accept sequential replay idempotence now and measure concurrent overlapping writers during preflight before adding global
   locking/uniqueness machinery。
