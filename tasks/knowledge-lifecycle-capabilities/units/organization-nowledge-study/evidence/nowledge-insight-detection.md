# Evidence: Nowledge Insight Detection

- **Question served**: Does Nowledge Insight Detection expose an Organization distinction beyond linking、evolution、Crystal
  synthesis and retrieval projection？
- **Consumer**: [Insight Detection Product shard](../product/insight-detection.md)。
- **Evidence horizon**: Nowledge official documentation/API observed 2026-09-03。Recheck before version-sensitive Product or
  Technical claims。

## Official Evidence

- Insight Detection runs weekly and searches for cross-domain connections and patterns across the knowledge base。Source：
  [Background intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)。
- The documented quality gate compares against insights from the previous two weeks to suppress duplicates。This is stated as a
  noise-control measure alongside other background-task quality gates。Source：
  [Background intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)。
- Product examples include the same failure pattern appearing in different projects、a decision being revisited several times
  over a period and older context contradicting a later approach。Every surfaced insight cites its sources；the stated Product
  preference is one non-obvious valuable insight over many obvious ones。Source：
  [Background Intelligence / Insights](https://mem.nowledge.co/docs/advanced-features#insights)。
- The public API exposes a manual `POST /agent/trigger/insight-detection` operation but documents no meaningful response schema or
  persisted result shape。Source：
  [Trigger Insight Detection](https://mem.nowledge.co/docs/api/agent/trigger/insight-detection/post)。
- Background Intelligence surfaces findings through the Timeline/Feed，whose events have separate read、resolve、retry and
  soft-delete APIs。Current public documentation does not prove that all Insight results become Memory/graph authority。Sources：
  [Background Intelligence](https://mem.nowledge.co/docs/advanced-features)、
  [API Reference](https://mem.nowledge.co/docs/api)。

## Evidence Versus Inference

| Evidence / observation | Current inference | Missing evidence / confidence |
| --- | --- | --- |
| The task searches across domains and reports patterns。 | Candidate selection deliberately crosses ordinary topic/referent neighborhoods。 | Medium；exact retrieval/graph algorithm is undocumented。 |
| Examples include recurrence、contradiction and shared failure mechanisms。 | “Insight” is a Product presentation envelope over several possible semantic operations，not one demonstrated graph law。 | High decomposition confidence。 |
| Every Insight cites sources。 | Provenance is part of the useful result，not incidental explanation text。 | High Product confidence；edge/persistence shape unknown。 |
| Recent duplicate comparison suppresses noise。 | Two-week lookback is a candidate-quality heuristic rather than the semantics of an insight。 | High。 |
| Findings surface in Timeline/Feed；trigger result is opaque。 | A surfaced event may be an application projection rather than independently reusable information。 | Medium；durable result authority is unknown。 |

## Product Return And Closure

The representation lens separates four possible outputs：

1. an existing-information Relation when the value is simply “read these together”；
2. an evolution/evidence relation when the value is contradiction、supersession or corroboration；
3. an application event when the value is timely attention rather than durable new information；
4. a derived Block with provenance/contribution Relations when the system has produced a new、independently reusable scoped
   pattern、analogy or hypothesis through accepted n-ary synthesis。

The fourth output does not justify a new behavior：D-472 already accepts provenance-preserving n-ary synthesis without requiring
source agreement。The retained candidate heuristic is **cross-context pattern induction** inside that pattern。Instead of starting
from an already shared first-order subject or related cluster，candidate formation compares relational/causal structure across
different contexts；qualification may infer a higher-order shared mechanism and then applies D-472's scope、contribution、
provenance、disagreement and uncertainty requirements。

Current evidence is insufficient to import Nowledge's schedule、two-week duplicate window、Feed packaging、candidate algorithm、
confidence policy or persistence shape。The Product inquiry is whether the inferred higher-order synthesis subject is a valid
refinement of D-472 qualification，rather than treating the `Insight` feature name as proof of a separate method。

D-493 reclassifies D-485's refinement as a behavior-specific n-ary candidate/qualification heuristic。It does not add durable
Product semantics、another parallel Organization method or transfer the surrounding Insight feature。
