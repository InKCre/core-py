# Product Study: Nowledge Skill Suggestions

- **State**: closed under D-487 and reclassified by D-493；procedure synthesis is a D-472 application，not another transfer。
- **Evidence**: [Nowledge Skill Suggestions](../evidence/nowledge-skill-suggestions.md)。
- **Decision authority**: [D-487](../../../decisions/D481-D490.md)、
  [D-493](../../../decisions/D491-D500.md)。

## Concrete Product Case

Suppose several independently collected release records show the same non-obvious working pattern：before a database rollout，
the operator exports a snapshot，runs a checksum after the migration，and only then advances traffic；one incident record further
explains that reversing the last two steps caused a silent mismatch。The reusable information is not merely that four records are
similar。It is a scoped procedure，its rationale/exception and the evidence from which that procedure was synthesized。

Later use may ask “how has this team safely performed this rollout？”A Human may read the procedure；an Application may show it；
an Agent may execute it after separate authorization。The info-base should preserve the same neutral procedure information for
all three consumers，without treating downstream Agent execution as Organization's purpose。

## What Nowledge Bundles Into One Feature

Nowledge Skill Suggestions combines at least four responsibilities：

1. detect repeated ways of working from Memories and Threads，with procedure-typed Memories as strong seeds；
2. synthesize a specific repeatable procedure and retain the source moments that taught it；
3. compile the procedure into a capability package such as `SKILL.md` plus optional scripts、references and evaluations；
4. let a Human enable it for connected Agents，then observe outcomes and sharpen/test later versions。

This bundle is coherent for an Agent Memory product，but the responsibilities do not share one authority in neutral InKCre。

## Representation-Lens Decomposition

| Nowledge responsibility | InKCre-side meaning | Candidate owner |
| --- | --- | --- |
| repeated-procedure candidate formation | comparable records may jointly indicate a reusable operational pattern | candidate mechanism for synthesis |
| scoped procedure + rationale/exception synthesis | new independently reusable information derived from n sources | D-472 provenance-preserving n-ary synthesis，specialized by a procedure SOP |
| source moments / Threads | contribution、provenance、counterexample and scope evidence | ordinary Blocks and precise Relations |
| `SKILL.md` / scripts / references compilation | one consumer-specific executable projection | downstream capability/integration owner |
| enable/disable and host materialization | authorization and deployment into connected Agent hosts | downstream capability lifecycle，not Organization |
| usage outcomes and sharpening | execution-performance feedback about a capability version | capability evaluation lifecycle；may later be collected as source information |
| `Checked` / `Proven` badges | evidence that a compiled capability passed one or more tests | capability-quality projection，not truth/confidence of the underlying procedure information |

The decisive boundary is **representation versus activation**：

```text
heterogeneous work evidence
  -> procedure-directed n-ary synthesis
     -> neutral procedure information + provenance / scope / exception Relations
        -> Human reads it
        -> Application presents it
        `-> downstream capability owner may compile + evaluate + authorize it for an Agent
```

The first graph result is reusable information。The last branch changes what a downstream Agent is allowed and equipped to do；
that is a separate operational effect and cannot be inferred merely because a `procedure` Relation exists。

## Relation To Accepted Organization Behaviors

The information-side result does not require a new `Skill` object or parallel Organization behavior。It is one application of
accepted D-472 provenance-preserving n-ary synthesis：

- candidate qualification looks for comparable repeated practice，including failures、exceptions and rationale；
- the synthesis subject is a scoped procedure rather than a generic summary；
- the derived Block remains linked to every materially contributing or challenging source；
- disagreement and uncertainty are retained rather than averaged into a confident recipe；
- weak、conflicting or merely generic evidence produces no-op/unresolved rather than a procedure。

An exact source-relative `procedure` Relation may make procedure-bearing information a useful candidate seed when that word
preserves the source meaning。Under D-493 it has no status as a member of a preferred primitive list；it also does not prove
repeatability，authorize execution or bound an exploratory Organization Agent to those seeds。

## Human Boundary

Nowledge keeps a suggested Skill off until a Human enables it。That review is justified by the operational transition from
represented information to an active Agent capability。It should not be copied backward as a mandatory Human acceptance state
for Organization's procedure synthesis：ordinary graph validation、provenance and later correction laws remain the information
authority boundary。

If a future InKCre capability owner compiles or deploys procedures，its Human/authorization model、target host、side effects、
versioning and evaluation must be designed there。No such Product capability is approved by this study。

## Accepted Product Boundary

D-493 reclassifies D-487's result：**repeated-procedure discovery is an application and candidate/qualification heuristic for
D-472 provenance-preserving n-ary synthesis；promotion of the resulting neutral procedure information into an executable Agent
capability is a separate downstream boundary**。This validates existing owners but is not counted as another Product transfer。

There is no independent Skill Suggestions Organization behavior and no transfer of Nowledge's Skill
registry、compiler、test badge、schedule、enable/disable state、host materializer or sharpening lifecycle。
