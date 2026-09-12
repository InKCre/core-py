# Evidence: Nowledge Memory Freshness / Decay

- **Question served**: Does time/use create Organization meaning，or only a retrieval projection；and does Nowledge confidence
  represent epistemic evidence？
- **Consumer**: [Memory Freshness Product shard](../product/memory-freshness.md)。
- **Evidence horizon**: Nowledge official documentation observed 2026-09-04。Recheck before version-sensitive Product or
  Technical claims。

## Official Evidence

- Nowledge gives each Memory independent decay and confidence scores。Decay represents freshness and combines recency with
  frequency；confidence represents how well-supported a Memory is and never decreases。Both influence ranking alongside semantic
  relevance。Source：[Memory decay](https://mem.nowledge.co/docs/concepts/memory-decay)。
- Decay uses exponential time since last interaction plus logarithmic access frequency，with recency weighted more heavily。
  An importance-dependent floor prevents the score falling below a minimum。Source：
  [Memory decay](https://mem.nowledge.co/docs/concepts/memory-decay)。
- Confidence inputs include access frequency、search appearances、explicit clicks、reading time、EVOLVES confirm/enrich edges
  and Crystal-source membership；each signal is capped。Source：
  [Memory decay](https://mem.nowledge.co/docs/concepts/memory-decay)。
- Semantic relevance remains dominant；decay and confidence adjust order when relevance is close。Crystals and latest EVOLVES
  versions receive additional adjustments。Source：
  [Search architecture](https://mem.nowledge.co/docs/concepts/search-architecture)。
- Since v0.6.6，appearing in search results updates last-accessed time/count as a light access。Nowledge documents about a 30-day
  half-life and says confidence contributes about five percent of final score。Source：
  [Search & Relevance](https://mem.nowledge.co/docs/search-relevance)。
- A daily background task recomputes cached decay/confidence scores and does not itself archive、delete、merge or rewrite
  Memories。Preferences、decisions、plans、procedures、learnings、rules、identities and context are not mechanically archived by
  freshness alone。Source：[Memory decay](https://mem.nowledge.co/docs/concepts/memory-decay)。
- Temporal queries can bypass ordinary decay pressure；event time and record time are separate，and temporal matching remains a
  relevance signal rather than a substitute for semantic relevance。Sources：
  [Search Through Time](https://mem.nowledge.co/docs/use-cases/bi-temporal)、
  [Search architecture](https://mem.nowledge.co/docs/concepts/search-architecture)。

## Existing InKCre Evidence

- Shared authority truth keeps Blocks/Relations authoritative and retrieval indexes/embeddings derived。Profile-scoped record
  timestamps mean database-row compatibility，not universal storage-byte freshness。Source：
  `docs/_shared/20-product-tdd/system-state-and-authority.md`。
- Shared semantic retrieval truth makes maintenance explicit and separate from retrieval；freshness checks compare projection、
  dimension and entity-row timestamps，while application retrieval owns ranking。Source：
  `docs/_shared/20-product-tdd/semantic-retrieval-and-peer-capabilities.md`。
- Local authority truth likewise assigns projection、derived-record lifecycle and ranking to the application/use capability。
  Source：`docs/30-unit-tdd/business-pipeline-and-authority.md`。

## Evidence Versus Inference

| Evidence / observation | Current inference | Missing evidence / confidence |
| --- | --- | --- |
| Decay is a secondary ranking signal and refresh mutates no Memory content。 | It is retrieval/application projection maintenance，not graph Organization。 | High。 |
| Recency and frequency reflect interaction history。 | They can forecast reuse within a relevant consumer/profile scope but do not express semantic currentness。 | High conceptual confidence；Nowledge's exact multi-user scope is not documented here。 |
| Search appearances reinforce freshness and confidence。 | Ranking output can become input to later ranking，creating exposure/self-reinforcement pressure。 | High causal confidence；magnitude in practice is unknown。 |
| Access/click/read time feed “confidence”。 | The score mixes use/exposure evidence with epistemic support and should not transfer as one information authority。 | High。 |
| EVOLVES and Crystal signals feed confidence。 | Distinct lineage、evidence and synthesis meanings are collapsed into a scalar application prior。 | High decomposition confidence；exact edge weighting is undocumented。 |
| Temporal queries bypass decay and latest EVOLVES versions get separate treatment。 | Query temporal relevance、use salience and semantic currentness are already distinct even inside Nowledge's implementation。 | High。 |
| Important Memories retain a floor。 | Importance is a ranking-policy input/projection，not proof of truth or applicability。 | High。 |

## Product Disposition

D-489 finds no independent Memory Freshness Organization method。Past use remains valuable as a scoped forecast
prior and may seed existing behavior candidates，but elapsed time、access and exposure do not create semantic currentness or
epistemic support。Those durable meanings remain owned by evolution/evidence Relations with scope and provenance。

Nowledge's decay/confidence fields、formula、daily refresh、importance floor and cleanup packaging remain downstream retrieval or
application choices。They must not be confused with InKCre's existing technical derived-record freshness contract。
