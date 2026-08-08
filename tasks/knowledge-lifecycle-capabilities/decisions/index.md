# Decision Register

> Task-state decision memory. Hub and code remain the final owners after promotion.

This directory is the single decision authority for the task packet。Decisions are sharded mechanically in groups of ten
so one stable ID has one predictable address；the shard boundary does not imply product or technical ownership。

## Navigation

| Range | Current subject span |
| --- | --- |
| [D-001–D-010](D001-D010.md) | Program boundaries → memo-like integration relationships |
| [D-011–D-020](D011-D020.md) | Collection success / memo graph → CanonicalMemo persistence |
| [D-021–D-030](D021-D030.md) | Memos backend/resolver/identity → flomo deferral |
| [D-031–D-040](D031-D040.md) | Memos 0.29.1、deployment、auth/config → attachment order |
| [D-041–D-050](D041-D050.md) | Memos graph/API/storage close → feed-content authority |
| [D-051–D-060](D051-D060.md) | RSS rewrite、identity、enclosures → Block hydration |
| [D-061–D-070](D061-D070.md) | Peer storage/resolver/media contracts → Memos MIME policy |
| [D-071–D-080](D071-D080.md) | RSS/Atom media、resolver IDs、unit close → semantic-quality pressure |
| [D-081–D-090](D081-D090.md) | Organization/use boundary、embeddings、AI topology → row timestamps |
| [D-091–D-100](D091-D100.md) | AI Provider/Model/Manager → Relation semantic projection |
| [D-101–D-110](D101-D110.md) | Embedding freshness/config → deployment-config reference defense |
| [D-111–D-120](D111-D120.md) | Config naming、retrieval results → Peer discovery/lease |
| [D-121–D-130](D121-D130.md) | Peer module/delegation/protocol → HTTP inbound destination |
| [D-131–D-140](D131-D140.md) | Peer persistence/wire completion → early organization taxonomy |
| [D-141–D-150](D141-D150.md) | Rumination understanding/depth → Agent/Graph forms |
| [D-151–D-160](D151-D160.md) | StarsGraphForm、GraphForm references → AI tool-calling terminology |
| [D-161–D-170](D161-D170.md) | Agent loop bound → cancellable Thread/turn topology |
| [D-171–D-180](D171-D180.md) | Structured-concurrent Tool batch → Agent validation / graph commands / rumination Agent selection |
| [D-181–D-190](D181-D190.md) | Organization-facing rumination completion → Peer Acceptance closure |
| [D-191–D-200](D191-D200.md) | Exact-target Peer delegation → clean shared-database rebuild |
| [D-201–D-210](D201-D210.md) | Mail communication-record foundation → current scope |
| [D-211–D-220](D211-D220.md) | Mail collect-job freshness → multi-Peer direction |
| [D-221–D-230](D221-D230.md) | Resolver behavior/content layers → SolvedContentRenderer and BlockInspector |
| [D-231–D-240](D231-D240.md) | InfoBase web route projection → Source Block provenance |
| [D-241–D-250](D241-D250.md) | Relation predicate normalization → current scope |
| [Withdrawn frames](withdrawn.md) | Explicitly rejected organizing frames and proposals |

## Register Rules

- Decision IDs remain monotonic across shards；append the next ID to its numeric shard。
- A later correction gets a new ID and names the superseded decision；do not rewrite history merely to remove disagreement。
- Unit packets and design files cite decision IDs and link to this index or the exact shard；they do not duplicate decision
  authority。
- When a shard reaches ten decisions，create the next fixed-width range file and add one index row。
- Task-state truth is promoted to the owning durable document only after implementation evidence and owner reconciliation。

## Current Edge

- Latest confirmed decision: [D-249](D241-D250.md)。
- Active unit: [Mail Extension](../units/mail-extension/packet.md)。
- Active surface: Canonical Email root-content versus graph-owned facts；Acceptance and implementation remain pending。
