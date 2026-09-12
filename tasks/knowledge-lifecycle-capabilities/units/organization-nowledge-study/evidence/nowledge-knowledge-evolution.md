# Evidence: Nowledge Knowledge Evolution

- **Question served**: What Product loss、information assumptions、evolution properties and state effects does Knowledge
  Evolution actually own，and what can be learned without promoting personal Memory semantics into InKCre？
- **Consumer**: [Product design](../product-design.md)。
- **Evidence horizon**: Nowledge official documentation observed 2026-08-31。Recheck when official Product/API/CLI behavior
  changes or before any version-sensitive Technical claim。

## Official Evidence

- Nowledge defines a Memory as one durable takeaway that should stand alone without its source conversation。Each has one primary
  type such as fact、preference、decision、plan、procedure、learning、context or event，and may retain source-thread provenance、
  event time and record time。Sources：[Memories](https://mem.nowledge.co/docs/memories)、
  [CLI](https://mem.nowledge.co/docs/cli)。
- Saving a new Memory triggers Background Intelligence。After semantic candidate retrieval，the system may create `replaces`、
  `enriches`、`confirms` or `challenges`。Nowledge calls the first pair progression/version-chain relations and the second pair
  validation/evidence relations。Challenges are surfaced for Human judgment。Sources：
  [Knowledge evolution](https://mem.nowledge.co/docs/concepts/evolves)、
  [Background intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)。
- Relations can carry `confidence`、`reviewed`、`source`、`reason`、direction and properties。Source：
  [Memory relations API](https://mem.nowledge.co/docs/api/memories/memory_id/relations/get)。
- A replaced Memory becomes superseded and leaves default recall while remaining in history。EVOLVES links influence search
  confidence；new edges trigger cluster evaluation and may contribute to later Crystal formation。Sources：
  [Search architecture](https://mem.nowledge.co/docs/concepts/search-architecture)、
  [Background intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)。
- Nowledge separately defines an open-vocabulary `Memory Link` for two Memories that should be read together because one
  supplies context、support、dependency、an example or another useful relation。Its documentation contrasts that with EVOLVES：
  use EVOLVES when one Memory is a newer version that updates、replaces、enriches、confirms or challenges an older version。
  Source：[Memory Links](https://mem.nowledge.co/docs/concepts/memory-links)。
- Search confidence grows when a Memory is confirmed **or enriched** by other Memories。The documented lifecycle states still
  archive only superseded/replaced or retired Memories；no enrich-triggered archive is documented。Sources：
  [Search & Relevance](https://mem.nowledge.co/docs/search-relevance)、
  [API reference](https://mem.nowledge.co/docs/api)。
- The public `nowledge-co/nowledge-mem` repository contains the Product README and reference assets，not the implementation or
  EVOLVES design source；it cannot resolve undocumented enrichment cardinality or state mutation。Source：
  [public repository](https://github.com/nowledge-co/nowledge-mem)。

## Evidence Versus Inference

| Evidence / observation | Current inference | Missing evidence / confidence |
| --- | --- | --- |
| `replaces` suppresses predecessor from default recall while retaining history。 | Supersession lineage with a dominance/current-frontier law。 | High；exact automatic review boundary remains unknown。 |
| `confirms/challenges` keep both Memories active as evidence。 | Evidence stance，not version lifecycle。 | High；source independence and aligned scope proof are unknown。 |
| `enriches` is grouped with progression/newer-version EVOLVES；general “read together” relations have a separate Memory Link feature；only replacement documents supersession。 | `enriches` is best explained as non-dominating、accretive refinement lineage，not general composition and not supersession lifecycle。 | Strong Product inference；both-end activity and branching cardinality remain undocumented。 |
| Memory input is already standalone、typed and may carry provenance/time。 | Pairwise EVOLVES relies on upstream normalization and personal-memory context，not two arbitrary text bodies。 | Medium-high；exact model context is not public。 |
| Relation effects reach recall、confidence and Crystal inputs。 | Incorrect relation effects are asymmetric；review policy matters。 | Material residual，but secondary to property/model decomposition。 |

## Current Synthesis

Knowledge Evolution packages multiple overlapping evolution models behind one personal Memory / recall UX。Official separation
of generic Memory Links from newer-version EVOLVES supports identity/subject continuity for `enriches`。However，`enriches`
does not share the documented dominance/archive law of `replaces`；it contributes graph navigation and confidence instead。
The strongest current decomposition is therefore supersession lifecycle、accretive refinement lineage and evidence stance，
not one progression state machine。

The apparent `new entity -> semantic candidates -> pairwise relation` shape is therefore not independently established as a
general info-base Product model。New information can be a useful trigger；candidate retrieval is heuristic；pairwise judgment
depends on a binary relation and sufficient scope/context。

## Per-mechanism Return

1. **Problem**: overwrite loses history；flat personal Memories make current understanding、refinement and evidence hard to
   distinguish。
2. **Actor / trigger**: Background Intelligence runs after a new normalized Memory is saved。
3. **Existing authority**: standalone typed Memories with possible source/event/record context。
4. **Operation**: semantic candidate retrieval followed by pairwise EVOLVES relation judgment。
5. **Persisted result / provenance**: semantic relation carrying confidence、review/source/reason properties；`replaces` also
   changes lifecycle state。
6. **Reusable output**: current/history recall distinction、refinement traversal、evidence stance、confidence and downstream
   synthesis inputs。Past-use forecasting may justify this output at Product-design time but is not an evolution transition。
7. **Incorrect / uncertain result**: false supersession can hide valid memory；false refinement/evidence can distort confidence
   and synthesis；review/cardinality details are only partly documented。
8. **InKCre reconciliation**: retain overlapping evolution properties/models and model-specific incremental mechanics；reject
   global personal-currentness、the four-relation ontology、universal semantic candidates and universal pairwise analysis。

## Closure

D-469 accepts accretive refinement lineage as distinct from supersession lifecycle。D-470 accepts the transfer/rejection result
and separates Product future-use forecasting from evolution execution。Knowledge Evolution is closed for this Product study；
reopen only if new primary evidence changes the model boundary or a later InKCre Product candidate depends on an unresolved
Nowledge-specific detail。

## Residual / Return

- **Residual**: exact `enriches` activity/cardinality and the non-challenge relation review boundary remain undocumented。
- **Return**: D-470 closes the mechanism and returns property/model decomposition plus model-specific incremental learning to
  Product design。Proceed to Crystals；do not open Technical / Acceptance from external analogy alone。
