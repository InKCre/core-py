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
| [D-241–D-250](D241-D250.md) | Relation predicate normalization → Mail source-native graph decomposition |
| [D-251–D-260](D251-D260.md) | Core Email body reuse → exact-occurrence Email identity |
| [D-261–D-270](D261-D270.md) | Canonical Email restoration → Mail sync checkpoint placement |
| [D-271–D-280](D271-D280.md) | Remote MIME reconciliation safety → current edge |
| [D-281–D-290](D281-D290.md) | Mail adapter command ownership → writable Source targets |
| [D-291–D-300](D291-D300.md) | Singular graph reads without duplicate-policy promotion → current edge |
| [D-301–D-310](D301-D310.md) | Cron coalescing/activation semantics → current edge |
| [D-311–D-320](D311-D320.md) | Mail access-context continuity → retrieval capability/unit distinction |
| [D-321–D-330](D321-D330.md) | Lexical document-body completeness → current edge |
| [D-331–D-340](D331-D340.md) | Media-interpretation convergence → multimodal AI、maintenance Jobs and Render self-host profile |
| [D-341–D-350](D341-D350.md) | Self-host/canonical-production separation → Graph focus-set / UI ownership boundary |
| [D-351–D-360](D351-D360.md) | InfoBase View initialization and recall ownership → active-scene navigation |
| [D-361–D-370](D361-D370.md) | Graph scale/layout/route state → endpoint-closed retrieval outcomes |
| [D-371–D-380](D371-D380.md) | Random focal/path ownership → MCP sink activation |
| [D-381–D-390](D381-D390.md) | MCP→Resolver use topology → monotonic Extension types / Peer-scoped Sink enablement |
| [D-391–D-400](D391-D400.md) | Explicit Sink Manager/Base lifecycle → Agent Skill / live MCP Resource projection |
| [D-401–D-410](D401-D410.md) | MCP batch outcome contract → current edge |
| [D-421–D-430](D421-D430.md) | Telegram private delivery inbox → repository-wide Towncrier release-contract expansion |
| [D-431–D-440](D431-D440.md) | Core release selection → Towncrier guidance、peer collaboration and Telegram acknowledgement reaction |
| [Withdrawn frames](withdrawn.md) | Explicitly rejected organizing frames and proposals |

## Register Rules

- Decision IDs remain monotonic across shards。Under parallel execution，each peer claims a non-overlapping range in the latest
  [parallel roster](../collaboration/roster.md)，checks the directory for collisions and writes only its reserved shards。The
  peer may add the narrow index navigation/current-edge consequence of its own accepted decisions。
- A later correction gets a new ID and names the superseded decision；do not rewrite history merely to remove disagreement。
- Unit packets and design files cite decision IDs and link to this index or the exact shard；they do not duplicate decision
  authority。
- When a shard reaches ten decisions，create the next fixed-width range file and add one index row。
- Task-state truth is promoted to the owning durable document only after implementation evidence and owner reconciliation。

## Current Edge

- Latest confirmed decision: [D-438](D431-D440.md)。MCP sink owns reserved range D-381–D-420；Telegram extension owns
  reserved range D-421–D-460。
- Active units: [mcp-sink](../units/mcp-sink/packet.md) in implementation/delivery and
  [telegram-extension](../units/telegram-extension/packet.md) with implementation plan、preflight and Impact Handshake
  prepared。Telegram retains D-421–D-460 after its approved expansion to the repository-wide Changie→Towncrier
  release contract；the expansion changes placement/overlap, not decision ownership。
- Parallel placement and integration surfaces are shared peer control in the [roster](../collaboration/roster.md)；there is no
  coordinator role。
