# Product Study: Nowledge Flags / Memory Maintenance

- **State**: closed under D-492；no independent Organization behavior，one residual `needs verification` pressure retained。
- **Evidence**: [Nowledge Flags / Memory Maintenance](../evidence/nowledge-flags-memory-maintenance.md)。
- **Decision authority**: [D-492](../../../decisions/D491-D500.md)。

## Concrete Product Case

Suppose later use retrieves three pieces of information：

- an old deployment decision with an explicit newer replacement；
- two scoped assertions that challenge each other；
- one consequential factual assertion from a single source，with no known supporting or challenging Relation。

The first two already expose durable graph meaning。A UI can display “stale” and “contradiction” reminders derived from them without
persisting another Flag fact。The third is different：absence of evidence Relations may mean “no corroboration exists”，or merely
“Organization has never searched for it”。Treating those states as identical would overclaim knowledge about an open world。

## What Nowledge Packages As Flags

Nowledge presents three Flag meanings in its Timeline：

| Nowledge Flag | Documented meaning | Existing InKCre route |
| --- | --- | --- |
| Contradiction | two Memories disagree | evidence stance / `challenges` relation |
| Stale | newer knowledge supersedes older information | supersession currentness；derived-artifact source changes route through D-473 propagation |
| Needs verification | a strong claim has no corroboration | unresolved evidence-coverage question |

Users may dismiss、acknowledge or link a Flag to a resolution。Those actions mix attention state with possible new semantic
information；they must not be interpreted as one generic graph mutation。

## A Flag Card Does Not Own The Underlying Meaning

For example，if the graph contains `A --challenges--> B`，that Relation is the durable evidence meaning。A UI may show a
“contradiction” card because of it。Closing that card changes only what the UI shows；adding source C or deciding that B replaces
A would be separate graph actions with their own authority。

- Dismissing means “do not keep presenting this attention item”，not “the contradiction is false”。
- Acknowledging means “the actor has seen it”，not “the underlying information is resolved”。
- Linking a resolution may create precise provenance/evolution/evidence meaning，but the relation and authority depend on the
  actual resolution action。

The Flag envelope therefore has no common semantic state law。This is only a concrete owner decomposition，not a new
cross-cutting Product pattern named `condition -> attention projection -> exact action`。

This also corrects an imprecision in the D-486 Working Memory analysis：an existing **semantic condition** may be graph authority；
a presentation-level Flag derived from that condition is not automatically graph authority merely because a briefing mentions it。

## `Contradiction` And `Stale` Reconciliation

`Contradiction` adds no behavior beyond accepted Knowledge Evolution：the Organization behavior must establish comparable
referent、scope and assertion roles before persisting a `challenges` relation。An Application may keep displaying a reminder
derived from that Relation until the owning model says the tension no longer applies。

`Stale` has at least three meanings and must not become one boolean：

1. explicitly superseded information is non-current under a supersession model；
2. a synthesis whose source graph changed receives D-473 reconsideration pressure；
3. old/unvisited information has low use salience under D-489 but is not semantically stale。

Only the first two have Organization/evolution meaning。The third is a retrieval/lifecycle projection。

## `Needs Verification` Is A Real Residual，But Not Yet A Method

The underlying use problem is legitimate：later consumers benefit from knowing that an important-looking assertion currently has
weak or unexamined support。However，the phrase “strong claim with no corroboration” leaves critical semantics undefined：

- who or what makes the claim strong enough to inspect；
- which evidence universe was searched and with what candidate/exploration law；
- whether sources are independent and actually comparable；
- whether “not found” means absent、unavailable or not processed；
- how long the assessment remains useful as the graph grows；
- whether the output is a reusable evidence-coverage assessment or only a warning for one use。

Existing evidence stance represents found support/challenge Relations，but **absence of a Relation is not proof that an evidence
search occurred**。A credible durable result would need a bounded coverage witness such as：

```text
claim C
  + evaluated evidence scope/basis B
  + evaluation time/model E
  -> found support/challenge set S
  -> unresolved coverage gap G
```

That may eventually justify a distinct evidence-assessment behavior or a specialization of n-ary synthesis。It may instead
remain a query-time reliability projection when the required evidence scope depends on the actual use。Current Nowledge evidence
does not resolve this Product fork，and inventing a generic `unverified` flag would hide rather than solve it。

The current recommendation is therefore to preserve this as a named Product pressure，not approve a Flag node/state or a new
Organization method yet。

## Memory Maintenance Decomposition

Nowledge Memory Maintenance prepares a Timeline review when old or overlapping Memories may add noise。After review，low-risk
facts/events can move out of everyday recall；richer semantic material routes toward organization or compaction。Its action APIs
re-read current source-of-truth state and re-run classification before archiving or queueing compaction。

| Maintenance lane | InKCre route |
| --- | --- |
| old/unvisited/low-salience candidate | D-489 use-side ranking/display；no semantic invalidation |
| superseded information | evolution currentness projection |
| duplicate/overlapping information | D-480 duplicate linking / compaction behavior |
| rich information needing semantic work | exact linking、synthesis、evolution or other behavior；no generic maintenance method |
| Human retires information from ordinary recall | explicit downstream/source lifecycle action，not age-driven Organization truth |
| deletion | explicit destructive info-base command，never inferred from tidiness pressure |

Nowledge's apply APIs re-read rows and re-run classification before acting on an earlier review。That is evidence about
Nowledge's own UI/task/lifecycle model，not an InKCre transfer。InKCre has no approved generic archive/compaction review plan whose
staleness needs this extra mechanism；its peer + central-database topology and ordinary command/transaction contracts must handle
the exact future action if one is ever designed。Do not pre-design a revalidation protocol here。

## Closure Decision

D-492 closes the Product review with the following result：

1. close `Contradiction`、semantic `Stale` and Memory Maintenance by routing them to existing evolution、evidence、use-projection、
   compaction and explicit-action owners；
2. keep Flag dismissal/acknowledgement as Application-only presentation state and require any graph-changing resolution to use its
   actual evolution/evidence/source behavior，without introducing a named cross-cutting pattern；
3. retain `Needs verification` as an unresolved **bounded evidence-coverage** pressure rather than creating a generic Flag or
   claiming no Organization value exists。

No Flag type/node、mutable acknowledged/dismissed graph state、generic maintenance behavior、automatic archive/delete policy、
Memory active/archive lifecycle、cleanup threshold or review-plan revalidation mechanism is approved。
