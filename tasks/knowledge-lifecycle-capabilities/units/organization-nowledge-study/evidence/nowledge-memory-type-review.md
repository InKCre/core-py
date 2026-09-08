# Evidence: Nowledge Memory Type Review

- **Question served**: What use distinction does Nowledge's primary Memory type provide，and how does its atomic Memory
  assumption change transfer to heterogeneous、possibly composite InKCre information？
- **Consumer**: [Product design](../product-design.md#memory-type-review--initial-product-inquiry)。
- **Evidence horizon**: Nowledge official documentation/API observed 2026-09-03。Recheck before version-sensitive Product or
  Technical claims。

## Official Evidence

- Every Nowledge Memory has one primary type：`fact`、`preference`、`decision`、`plan`、`procedure`、`learning`、`context` or
  `event`。Nowledge says this helps Agents decide how to use it；if a caller does not provide a type，Mem classifies during
  creation。Source：[Memories](https://mem.nowledge.co/docs/memories)。
- Search/FS recall can filter by `unit_type` or a by-type path。Source：[FS Recall](https://mem.nowledge.co/docs/api/fs/recall/get)。
- Memory Type Review runs every three days in small batches and after new Memories arrive。Nowledge describes it as safe
  housekeeping that improves filing without rewriting Memory text；high-confidence fixes may be applied from bounded batches。
  Source：[Background Intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)。
- On-demand reclassification defaults to dry-run，scans bounded weakly typed Memories，accepts a minimum classifier confidence
  and updates only graph/search-filter metadata in apply mode；it does not change content、embeddings or rebuild the index。
  Sources：[Reclassification API](https://mem.nowledge.co/docs/api/agent/trigger/unit-type-reclassification/post)、
  [CLI](https://mem.nowledge.co/docs/cli)。

## Evidence Versus Inference

| Evidence / observation | Current inference | Missing evidence / confidence |
| --- | --- | --- |
| One primary type helps Agents decide how to use a standalone Memory。 | Type is intended as use-facing semantic role，not merely a display category。 | High。 |
| Type can filter recall and updates graph/search metadata。 | Nowledge combines a persisted Memory property with an application filter projection。 | High。 |
| Review targets weak classification and applies only high-confidence bounded fixes。 | Model judgment is fallible，but Nowledge treats the type slot as one mutable classification authority。 | High；exact confidence evidence unknown。 |
| Nowledge defines Memory as one durable takeaway。 | Primary type assumes a more atomic unit than arbitrary InKCre Blocks such as documents、messages or source records。 | High product difference。 |

## Product Return And Audit Correction

The eight types do not form one orthogonal axis：`fact` concerns epistemic/assertive status；`preference/decision/plan` concern
agency、normativity or future intent；`procedure` concerns operational affordance；`learning` concerns acquisition/history；
`context` concerns discourse role；`event` concerns occurrence/time。One information item can legitimately have several。

The first candidate used roles only to guide breakdown，but that would not preserve the role for later use。D-483 then mapped
Nowledge's words to source-relative Relation content：

```text
Source Block
  |--fact / preference / decision / plan / procedure / learning / context / event--> reusable information unit
  `--more exact open relation content when a primitive loses material meaning-------> reusable information unit
```

The Relation principle preserves both provenance and the target's role relative to the source；it does not intrinsically type the
target，and several role Relations may coexist。The audit nevertheless found that treating the exact eight words as a starter
guideline still copied source vocabulary：the dimensions are heterogeneous，`fact` can imply global truth，`learning` imports an
epistemic subject and `context` is often too weak to preserve later-use meaning。

D-493 therefore retains only open、source-relative、non-exclusive semantic-role Relation content and returns the eight words to
official evidence/examples。Any of them may still be used when exact，but none is preferred or registered。No type registry、Block
field、mandatory breakdown、automatic review or consumer behavior is approved。
