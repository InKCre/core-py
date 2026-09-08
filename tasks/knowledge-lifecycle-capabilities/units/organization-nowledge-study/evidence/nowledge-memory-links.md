# Evidence: Nowledge Memory Links

- **Question served**: What Product loss、authority and persisted meaning does Memory Links own，and what can an automatic
  info-base Organization learn from an explicitly created “read together” relation？
- **Consumer**: [Product design](../product-design.md#memory-links--initial-product-inquiry)。
- **Evidence horizon**: Nowledge official documentation observed 2026-08-31。Recheck before any version-sensitive Product or
  Technical claim。

## Official Evidence

- A Memory Link tells Nowledge that two Memories should be read together because one changes how another should be understood。
  It is explicitly distinguished from search similarity。Source：[Memory Links](https://mem.nowledge.co/docs/concepts/memory-links)。
- Creation selects two Memories in the same Space，adds a short relation name and optionally a reason。Same-Space restriction is
  described as preventing accidental links across work、projects、clients and agent teams。Source：[Memory Links](https://mem.nowledge.co/docs/concepts/memory-links)。
- Later an Agent or graph tool can bring the linked Memory nearby and know why it matters；the relation name and reason are
  inspectable on the graph edge。Source：[Memory Links](https://mem.nowledge.co/docs/concepts/memory-links)。
- Relation names are open vocabulary and normalized across spelling forms。Examples include `supports`、`contradicts`、
  `depends_on`、`example_of`、`blocks` and `same_topic`；domain-specific names are allowed。Source：
  [Memory Links](https://mem.nowledge.co/docs/concepts/memory-links)。
- Memory Links is explicitly separated from EVOLVES version/evidence relations、broad Labels、Entity graph facts and Search
  relevance。AI suggestion may draft a name/reason but Human intent still decides what is persisted。Source：
  [Memory Links](https://mem.nowledge.co/docs/concepts/memory-links)。
- The graph stores one stable Memory-to-Memory edge。The relation API exposes source/target、relation type、strength、confidence、
  bidirectionality、status、reviewed/source/author/agent/source-app provenance、reason、properties and direction。The concept
  documentation does not define exact semantics for all API fields。Sources：[Memory Links](https://mem.nowledge.co/docs/concepts/memory-links)、
  [List Memory Relations](https://mem.nowledge.co/docs/api/memories/memory_id/relations/get)。

## Evidence Versus Inference

| Evidence / observation | Current inference | Missing evidence / confidence |
| --- | --- | --- |
| Link means two exact Memories should be read together for a reason。 | The durable Product distinction is contextual commitment，stronger than candidate similarity。 | High。 |
| Human or clear-intent Agent decides what to save。 | Nowledge's authority comes from explicit intent；InKCre already admits automated Organization linking but must define its own correctness and graph-assertion contract。 | High product difference；exact automatic evidence remains open。 |
| Open normalized name plus inspectable reason。 | Reason may carry instance meaning that an open label cannot；normalization only provides lexical identity。 | Medium-high；consumer behavior beyond graph/Agent description is undocumented。 |
| API exposes strength/confidence/review/source/direction fields。 | Implementation has more axes than the simple Product story，but field presence does not establish Product semantics。 | High caution；creation/default/update contracts not yet recovered。 |
| Memory Links is separate from EVOLVES、Labels、Entity links and Search。 | Descriptive contextual links should not silently acquire lifecycle、evidence or operational-force state laws。 | High。 |

## Product Reconciliation / Closure

Existing InKCre Product truth defines a Relation as a directed semantic link whose payload states contract-owned meaning，without
one universal registry；Organization may be explicit or automated and linking is already a known operation。This removes Human
confirmation as a required transfer and makes the active question one of evidence-to-assertion admission。

The accepted learning is a **candidate-to-assertion boundary for contextual linking**：separate candidate relevance from the
exact persisted relation assertion；retain rationale as semantic payload only when label、endpoints and direction do not already
preserve why the connection changes later interpretation。Open descriptive vocabulary still does not authorize operational
force semantics。

D-477 further prevents overfitting the rollout/capacity example：referent、scope、unit and semantic role are case-specific
judgment dimensions，not universal persisted fields。Existing Resolver interpretation plus LLM/Agent contextual reasoning is the
current direction，while Organization retains mutation authority。Memory Links is closed under D-476–D-477 with no runtime or
relation vocabulary approved。
