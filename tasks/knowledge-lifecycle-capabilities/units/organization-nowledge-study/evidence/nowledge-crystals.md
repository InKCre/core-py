# Evidence: Nowledge Crystals

- **Question served**: What Product loss、authority、n-ary synthesis behavior、trust lifecycle and source-change behavior does
  Crystals own，and which parts are organization rather than Memory-specific recall/ranking？
- **Consumer**: [Product design](../product-design.md)。
- **Evidence horizon**: Nowledge official documentation observed 2026-08-31。Recheck when Crystals formation、review or stale
  behavior changes，or before any version-sensitive Technical claim。

## Official Evidence

- Product loss：several Memories independently touch the same topic but remain scattered，so none provides the whole picture。
  A Crystal is a standalone synthesized reference Memory built from three or more source Memories；the system identifies each
  contribution and writes one coherent article。Source：[Crystals](https://mem.nowledge.co/docs/concepts/crystals)。
- Formation pipeline：EVOLVES creates related-memory edges；event-driven cluster evaluation checks for at least three same-topic
  sources with enough distinct information；synthesis creates one Crystal and one `CRYSTALLIZED_FROM` edge per source。A weekly
  review also scans for missed clusters。Sources：[Crystals](https://mem.nowledge.co/docs/concepts/crystals)、
  [Background intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)。
- The source-memory API exposes every provenance edge with a `contribution_weight` and sorts sources by contribution。Source：
  [Crystal source memories API](https://mem.nowledge.co/docs/api/library/crystal/crystal_id/source-memories/get)。
- Nowledge describes three independent sources as a quality gate：cross-platform sources are stronger than three messages from
  one thread。The exact definition and proof of independence are not documented。Source：
  [Crystals](https://mem.nowledge.co/docs/concepts/crystals)。
- Every Crystal starts unreviewed。Confirm adds a search boost；dismiss applies a heavy ranking penalty without deletion；editing
  title/content automatically confirms。Unreviewed Crystals get no boost。A confirmed Crystal is described as corroborated、
  user-verified knowledge，while semantic relevance remains the dominant ranking signal。Source：
  [Crystals](https://mem.nowledge.co/docs/concepts/crystals)。
- Crystals contribute to source-Memory confidence。The API counts Crystals separately from active and archived Memories，even
  though the Product describes a Crystal as a special Memory。Sources：
  [Crystals](https://mem.nowledge.co/docs/concepts/crystals)、[API reference](https://mem.nowledge.co/docs/api)。
- If a source is updated、challenged or replaced，the Crystal becomes stale and receives a re-evaluation proposal rather than
  silent rewrite。Confirmed Crystals are prioritized；dismissed Crystals are left alone。Source：
  [Crystals](https://mem.nowledge.co/docs/concepts/crystals)。
- Conversation synthesis preserves speaker role：a Human statement may be a decision，while an AI recommendation remains a
  suggestion。This prevents synthesis from converting explored options into user commitments。Source：
  [Crystals](https://mem.nowledge.co/docs/concepts/crystals)。

## Per-mechanism Record — Initial

1. **Problem**: related fragments remain individually useful but impose repeated hunting and integration cost；no standalone
   reference represents their combined contribution。
2. **Actor / trigger**: new EVOLVES edge triggers cluster evaluation；weekly review provides a scheduled catch-up path。
3. **Existing authority**: at least three persisted、apparently independent、same-topic Memories with distinct contributions。
4. **Operation**: qualify an n-ary cluster，read every source，synthesize one standalone derived Memory。
5. **Persisted result / provenance**: a separately identifiable Crystal plus one weighted `CRYSTALLIZED_FROM` edge per source，
   initial review state and later stale state。
6. **Reusable output**: one coherent reference、source drill-down、search surface and preserved source contribution context。
7. **Incorrect / uncertain result**: false convergence or lossy synthesis persists but remains unreviewed；confirmation、dismissal
   and edit alter trust/ranking；source changes invalidate freshness without silent rewrite。
8. **InKCre reconciliation**: not yet accepted。Memory/current-understanding language、three-source heuristic、Human confirmation
   semantics and ranking remain Nowledge-specific until their Product logic is recovered。

## Evidence Versus Inference

| Evidence / observation | Current inference | Missing evidence / confidence |
| --- | --- | --- |
| Cluster qualification reads 3+ sources and writes one Crystal with source edges。 | Crystals is an n-ary synthesis organization behavior，not pairwise evolution。 | High。Exact cluster/contribution quality oracle unknown。 |
| Source EVOLVES changes mark an existing Crystal stale and propose re-evaluation。 | Nowledge packages dependency-triggered maintenance with synthesis；this does not prove InKCre needs a separate lifecycle rather than propagation and version projection。 | High as Nowledge behavior；exact stale representation and cascade mechanics unknown。 |
| Crystal is persisted before review but gains trust/ranking only after confirm。 | Nowledge separates persistence from Human endorsement/ranking，but its Human disposition need not transfer into automatic InKCre Organization。 | High。Whether unreviewed Crystal participates in all non-search consumers is unknown。 |
| Cross-platform sources are described as stronger independence。 | Nowledge uses channel/thread diversity as a proxy for epistemic independence and importance。 | Medium；platform difference does not prove source independence。 |
| Confirmed Crystal is called user-verified knowledge。 | The Product still relies on one Human epistemic subject，which cannot transfer base-wide to InKCre。 | High for boundary，mapping not yet designed。 |

Official material does not document whether Crystal source-confidence feedback waits for confirmation。It says Crystal membership
itself is a confidence signal。If “confidence” means epistemic support，an automatically created synthesis feeding confidence back
to the same source set risks circular evidence；if it means predicted retrieval usefulness，membership can be a salience signal。
The Product language does not keep those meanings cleanly separated。

## Current Synthesis / Active Work

Crystals packages several Product mechanics behind one feature，but InKCre does not need to reproduce their packaging。D-472
accepts **provenance-preserving n-ary synthesis** as a method/pattern。D-473 rejects the earlier symmetric two-model framing：
source-change handling is better explained by reconsideration pressure travelling through derivation dependencies，followed by
the same synthesis pattern and common append-only/version-continuity semantics。

The inspected evidence separates four predicates that Nowledge partially compresses into “three independent sources”：

1. **recurrence / topic overlap** — enough items make a cluster worth considering；
2. **source independence** — agreement may carry epistemic weight；
3. **complementarity / distinct contribution** — synthesis can add a useful combined view；
4. **salience / predicted usefulness** — repeated appearance suggests the subject may matter later。

A count of three proves none of these by itself。Three copies can recur without independence；three independent sources can
disagree；three same-topic items can add no complementary content；one comprehensive source can already eliminate synthesis need。
The threshold is therefore best treated as a Nowledge candidate/quality heuristic，not the convergence model's defining property。
D-471 records Sir's acceptance of this boundary。

The persisted authority also separates：source Memories remain provenance evidence；the Crystal is organization-authored derived
information；search boost/penalty is an application projection。Nowledge's Human confirmation/dismissal is recorded as evidence，
not transferred into current InKCre Product design。

Active inquiry now moves to candidate-set formation and weighted contribution meaning。Official evidence shows
`contribution_weight` on each `CRYSTALLIZED_FROM` edge，but not whether it expresses coverage、causal dependence、confidence or
only ordering；those meanings must not be inferred from the field name。

## Candidate Formation / Contribution Analysis

Official formation order is causally useful：EVOLVES detection first persists relation edges；cluster evaluation then fires on
the resulting related-memory graph；only a qualifying cluster reaches synthesis。This supports an inference that prior
Organization output can bound the next Organization candidate region。It does not support treating connectivity as synthesis
authority：the documentation still performs a separate same-topic / distinct-information quality evaluation。

For InKCre，graph-guided n-ary candidate formation is a useful behavior-specific heuristic：typed prior relations route attention
to a bounded neighborhood，then synthesis independently evaluates subject、scope and complementarity。A universal connected-component
rule would permit transitive topic/scope drift and incorrectly treat heterogeneous relations as equivalent conductors。

The source-memory API documents `contribution_weight` only as a property used for descending source display order。No official
semantic contract ties the scalar to truth、confidence、invalidation or candidate admission。Until contrary evidence appears，
the field supports only an application ordering observation。The stronger Product requirement is traceable source contribution；
a scalar weight is neither necessary nor sufficient，and a low-weight source may still carry a decisive exception。

D-493 confirms that this candidate path is not durable Product semantics、a common Organization pipeline or an independent
transfer。D-472 synthesis and D-473 dependency response remain the Product returns。
