# Product Study: Nowledge Rule Suggestions

- **State**: closed under D-488；descriptive synthesis and source-relative Rule retained，automatic normative promotion rejected。
- **Evidence**: [Nowledge Rule Suggestions](../evidence/nowledge-rule-suggestions.md)。
- **Decision authority**: [D-488](../../../decisions/D481-D490.md)。

## Concrete Product Case

Assume the info-base contains three records from one project：a review says “generated API docs must not be hand-edited”；a later
incident attributes a broken release to a manual edit；and an authoritative project instruction explicitly repeats the
prohibition。Several distinct meanings exist：

- the review and incident are evidence of a recurring practice/problem；
- Organization may derive an observed pattern or an inferred scoped preference with provenance；
- the authoritative instruction is source-authored normative information；
- making every downstream Agent obey it is a consumer-side activation decision。

If the authoritative instruction were absent，the first two records would not by repetition alone establish that someone with
the relevant authority commanded future behavior。This is the key difference between discovering a regularity and creating a
Rule。

## What Nowledge Bundles Into One Feature

Nowledge defines a Rule as an always-on instruction that shapes connected-Agent behavior before search、tools or task-specific
Skills。A Rule may apply to everyone、one Agent profile or one Space。Its suggestion mechanism periodically notices repeated
preferences/project habits，creates a draft and lets the Human accept、edit or ignore it；accepted Rules enter the Context Bundle
for matching Agents。

That packaging combines three responsibilities：

1. infer a repeated preference、habit or standing-practice candidate from work evidence；
2. decide that the candidate should become a normative instruction with actor、scope and authority；
3. project the active instruction into downstream Agent behavior before other work begins。

Only the first responsibility is naturally Organization-authored。The second requires an authorized source；the third belongs to
the downstream consumer contract。

## The `is -> ought` Boundary

```text
past records repeatedly show X
  -> Organization may derive:
       “actor/project repeatedly preferred or practiced X”
       + provenance / scope / counterevidence / uncertainty

authorized source states “future actor(s) must do X”
  -> normative rule information
     -> downstream rule owner may activate/inject it for matching consumers
```

The upper path is descriptive inference。The lower path carries normative force。Frequency、consistency or model confidence can
strengthen evidence for the first claim，but cannot manufacture the issuer authority required by the second。A Human accepting or
editing a suggestion can become the authorized source of a new directive；that act is not merely validation of an Organization
fact。

## Representation-Lens Decomposition

| Meaning | Candidate representation / owner | Boundary |
| --- | --- | --- |
| repeated behavior or expressed preference | D-472 n-ary synthesis with actor、scope、time and provenance | descriptive derived information only |
| explicit standing instruction / policy | ordinary information plus source-relative `rule` or more exact Relation content | records what a source directs；does not imply global authority |
| support、challenge or replacement evidence | accepted evidence-stance / evolution Relations | changes interpretation under the owning model，not activation by connectedness |
| draft suggestion | downstream promotion proposal that cites graph evidence | no behavioral force while only a candidate |
| accepted/edit-created directive | new Human/authority-authored information or configuration | authority comes from the actor/event，not the prior model confidence |
| global/profile/space matching and Context injection | downstream Agent-profile/context contract | use projection，not info-base Organization |

An exact source-relative `rule` Relation may preserve the continuing prescriptive role in which a source presents information
when weaker wording such as `decision` or `preference` would lose it。D-493 removes any preferred primitive-list status；the word
is justified only by the exact source/behavior meaning and remains non-exclusive：

```text
Authoritative source S --rule--> instruction U
```

This Relation alone does not make U active。Any operational force requires a consumer contract that resolves issuer authority、
target actor、scope、applicability、priority/conflict and activation status。Generic Relation content must not silently become an
execution policy engine。

## Relation To Accepted Organization Behaviors

Rule Suggestions exposes no irreducible Organization method so far：

- repeated-preference/pattern discovery fits provenance-preserving n-ary synthesis；
- explicit directives are collected source information and source-relative semantic-role linking；
- later directives may replace/refine earlier ones through evolution models；
- evidence can support/challenge a directive through evidence stance；
- downstream selection and injection are application/capability projections。

The valuable new distinction is not a behavior but an authority law：**Organization may propose descriptive or promotion-
candidate information，but only an authorized actor/source can create normative force**。

## Accepted Product Boundary

D-488 closes Rule Suggestions with no independent Organization method and retains two narrower results：

1. repeated preferences/practices are a scoped n-ary synthesis case and must remain descriptive until authorized；
2. an exact source-relative `rule` Relation may record prescriptive source meaning，while activation、scope matching、conflict
   resolution and Context injection remain downstream contracts；D-493 gives it no registry/starter-list status。

No Rule registry、confidence threshold、three-day schedule、draft/accept UI、global/profile/space configuration model or Agent
injection behavior is approved。
