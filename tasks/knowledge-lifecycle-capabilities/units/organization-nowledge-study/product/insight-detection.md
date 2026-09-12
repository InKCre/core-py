# Product Study: Nowledge Insight Detection

- **State**: closed under D-485 and reclassified by D-493；candidate heuristic，not an additional Product transfer。
- **Evidence**: [Nowledge Insight Detection](../evidence/nowledge-insight-detection.md)。
- **Decision authority**: [D-485](../../../decisions/D481-D490.md)、
  [D-493](../../../decisions/D491-D500.md)。

## What Nowledge Appears To Bundle

Nowledge runs Insight Detection weekly to search for cross-domain connections and patterns，and suppresses candidates that
duplicate recent insights。Its Product examples include：

- the same failure mechanism recurring in different projects；
- a decision or question being revisited several times over a period；
- earlier context that contradicts or materially bears on a later choice。

Each surfaced insight cites its sources，but current official documentation does not expose exact candidate generation、source
cardinality、persisted graph shape、confidence model or whether every surfaced Feed insight becomes independently retrievable
information。The trigger endpoint likewise documents only proactive execution，not the result schema。

This is not evidence for one independent Organization behavior。The examples route to several existing owners：

| Nowledge example | First InKCre owner | Resolution |
| --- | --- | --- |
| direct cross-domain connection worth reading together | contextual linking | persist a precise reason only when adjacency would lose the useful distinction |
| revisited several times in a period | application/temporal analysis | a projected count is not automatically reusable graph meaning |
| old context contradicts a later choice | evolution / evidence stance plus retrieval | surface existing graph meaning unless a new inference is actually produced |
| shared mechanism inferred across different cases | provenance-preserving n-ary synthesis | qualification may infer a higher-order shared subject across different first-order contexts |

## Concrete Use Failure：The Connection Is Not The Insight

Suppose the info-base contains：

```text
A: “Burst imports started five duplicate analysis runs；debouncing fixed it。”
B: “Webhook retries created duplicate downstream jobs；an idempotency key fixed it。”
```

Semantic retrieval may find A for imports and B for webhooks。A generic `related` edge lets a later reader traverse between
them，but still requires that reader to rediscover the reusable distinction：**event-triggered work needs an explicit duplicate-
suppression law**。The sources discuss different first-order subjects；a higher-order shared mechanism must be inferred before
they form a coherent synthesis set。

If that inferred distinction is forecast to matter later，the representational lens suggests：

```text
A --example / evidence--> H  “Event-triggered work needs an explicit duplicate-suppression law。”
B --example / evidence--> H
```

`H` may deserve an ordinary derived Block because its content is independently referable、queryable and reusable。The Relations
preserve which cases ground it；counterevidence or limits remain visible rather than being erased by the generalization。This is
neither entity extraction nor a direct pairwise link，and it does not require sources to assert the same conclusion。That last
fact does not distinguish it from D-472：accepted n-ary synthesis already preserves disagreement and never required convergence。

## Retained Heuristic：Cross-Context Pattern Induction Inside N-Ary Synthesis

The result is not another parallel Organization method。It is a candidate-formation and set-qualification mode inside accepted
provenance-preserving n-ary synthesis：

```text
heterogeneous information / graph neighborhoods
  -> seed structurally comparable cases across otherwise separated contexts
     -> behavior-directed Agent explores enough source and counter-context
        -> infer a candidate higher-order synthesis subject / mechanism
           -> qualify scope、distinct contribution and counterevidence under D-472
              |-> insufficient novelty、support or future-use forecast -> no-op
              `-> derived information Block + precise provenance/contribution Relations
```

Crystals taught graph-guided candidate formation from already related information and a compatible synthesis subject。Insight
Detection adds a different search pressure：use relational/causal structure，not only lexical or existing-topic proximity，to
hypothesize a higher-order subject across distinct first-order domains。The synthesis operation and output authority remain
D-472；the candidate/qualification path changes。

The LLM/Agent may explore beyond initial candidates under D-481。Its SOP needs to seek disconfirming context and retain scope /
uncertainty，because apparent analogy is especially vulnerable to superficial similarity。That does not justify a confidence
field、Human approval state or generic Insight registry。

D-493 classifies the higher-order-subject search as a behavior-specific candidate/qualification heuristic inside D-472，not an
additional Product distinction or Organization method。D-485 still closes the mechanism。No trigger、schedule、candidate
algorithm、Relation vocabulary、schema、runtime or Acceptance claim is approved。
