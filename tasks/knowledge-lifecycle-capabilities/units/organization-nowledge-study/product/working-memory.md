# Product Study: Nowledge Working Memory / Daily Briefing

- **State**: closed under D-486；no independent info-base Organization transfer。
- **Evidence**: [Nowledge Working Memory](../evidence/nowledge-working-memory.md)。
- **Decision authority**: [D-486](../../../decisions/D481-D490.md)。

## Nowledge's Current-Context Artifact

Nowledge generates one Working Memory briefing for each active space every morning and refreshes it after new Memories arrive。
The briefing includes active focus、open/unresolved items、recent knowledge changes and priority based on recent activity。Its
generation context includes a digest of the previous week、yesterday's Working Memory、graph statistics and recent resolution
patterns，subject to a context cap。Connected Agents receive it through the Context Bundle or a lightweight Working Memory read。
Users may edit the briefing，and prior days are archived/readable。

The downstream-consumer loss is concrete but different from the previous mechanisms：a new Agent run may begin with “continue” or another
underspecified request before it has enough query intent to retrieve relevant information。Searching the whole info-base is too
large；waiting for an exact query loses continuity。Recent activity can forecast a bounded near-term working set，even though the
system cannot know the actual future task。

Here `Agent` means Nowledge's connected downstream consumer。It is not the internal LLM-backed Agent that an InKCre Organization
behavior may use to explore and propose graph changes。InKCre is neutral among Human、Application and Agent consumers；the needs of
one Agent run therefore do not define Organization authority。

## Representation-Lens Decomposition

Working Memory mixes several possible meanings that require separate authority：

| Briefing content | Candidate owner | Reason |
| --- | --- | --- |
| an already persisted decision、plan、flag or synthesis | Block / Relation graph authority | the briefing should project and cite it，not restate it as new truth |
| a genuinely new insight produced during briefing generation | owning Organization behavior | independently reusable information should enter the graph with provenance before projection |
| “recently active / likely relevant now” selection | Application context assembly | this is a per-space/per-Agent forecast for near-term use，not an intrinsic information property |
| token-budget ordering and truncation | downstream Application/Agent integration | it belongs to the consuming run and can differ by profile、space and budget |
| Human-authored standing focus/context | explicit source information or configuration | it must not silently share authority with generated text |

This rejects both extremes：Working Memory is not merely a cache of graph content，because selection、ordering and compression
have use-facing semantics；but it is not automatically a new graph Block，because most of its value expires with the run、time
and scope that requested the projection。

## Candidate Boundary：Near-Term Context Assembly Is Use，Not Organization

```text
Agent/profile/space/run context
  + recent activity and retrieval projections
  + Resolver-readable graph authorities
  + unresolved Organization outputs
  -> Application-owned selection、ordering and token-budget compression
     -> ephemeral/use-facing context bundle
        -> Agent begins with a bounded forecast of likely relevant information
```

The candidate return is a boundary learning，not a new Organization behavior：**past activity may forecast near-term use at the
Application context-assembly boundary**。This is more specific than the Product-admission forecast used to justify an
Organization distinction，and still does not claim knowledge of the future query。

If assembly discovers a new reusable insight、decision or synthesis，that item routes through its owning Organization/source
behavior and becomes ordinary graph authority；the context bundle may then cite/project it。Generated focus and priority should
not be written back as evidence about the underlying information merely because they appeared in the briefing。

## Derived-On-Derived Feedback Risk

Nowledge includes yesterday's Working Memory in today's generation context and also permits direct Human edits。Copying that
shape naively would merge three authorities：source information、model-generated projection and Human-authored direction。It also
allows a concise generated claim to survive by being repeated by later generations even when its original evidence has left the
window。

The simpler InKCre learning is：

- recompute the projection from current authorities and explicit run context；
- if continuity from a prior projection is useful，treat it as presentation continuity，not supporting evidence；
- keep Human-authored standing direction in an explicit source/configuration surface and layer it into context assembly；
- archive projections only for application history/audit when a proven use needs it，not as default info-base knowledge。

This preserves KISS/stateless execution without claiming that the persisted info-base itself is stateless。

## Accepted Product Boundary

D-486 rejects Working Memory as an info-base Organization behavior and retains one learning：a future downstream
Application/Agent-context capability may assemble a bounded、per-run near-term working-set projection from graph authority，while
new reusable meaning must first route to its owning Organization behavior。No Working Memory file/Block、daily schedule、archive、
Context Bundle、ranking rule、token cap、Human-edit surface or implementation owner is approved。
