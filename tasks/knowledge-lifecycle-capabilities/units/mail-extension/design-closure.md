# Mail Extension Design Closure Ledger

> Compact steering surface for finishing design。Decision shards remain the authority；technical-design files explain the
> current contracts。This ledger distinguishes unresolved product judgment from implementation-owned detail。

## Frozen Design Surfaces

| Surface | Status | Authority span |
| --- | --- | --- |
| Delivery scope and user value | Frozen | D-201–D-220：communication-record baseline，ordinary collect/backfill，remote deletion，jobs，lazy attachments，reply facts，generic use surface |
| InfoBase client rendering/navigation | Frozen | D-221–D-238、D-312：SolvedContentRenderer、BlockInspector/Popups、InfoBaseRouter port、GraphSurface realization、route/loading ownership、HTML isolation/privacy |
| Source provenance and Mail graph | Frozen | D-239–D-259：lazy Source anchor，Mailbox scope，Email/body/MIME/address/reply graph，source-native decomposition |
| Email identity and mutable state | Frozen | D-260–D-270：linear reconciliation，exact-one reuse，flags，QRESYNC/CONDSTORE degradation，checkpoint/locator split |
| Mail protocol runtime topology | Frozen | D-271–D-281：no-guess MIME access，Source/Resolver sibling Adapter callers，public protocol config，factory，async scope，Adapter ownership |
| Writable Storage policy | Frozen | D-282–D-285：Source → deployment → PostgreSQL fallback，`sources.storage`，registry-owned `storage_types.writable` |
| MIME durable completion authority | Frozen | D-286：metadata `--content-->` semantic child |

## Remaining Design Closure

| ID | Surface | What remains | Human discussion need |
| --- | --- | --- | --- |
| R1 | MIME materialization command | [Approved](technical-design/mime-materialization.md)：existing-child short circuit、singular direct solved content、non-stable singular graph read、concurrent create、failure/refresh | Closed through D-291 |
| R2a | Common Source foundation/config | [Approved](technical-design/runtime-closure.md)：Source/storage policy、global Job/Cron、distributed occurrence materialization、core-py/client-web eligible workers、timeout and no-misfire semantics | Closed through D-306；exact implementation mechanics delegated to plan/preflight |
| R2b | Mail collect/backfill command | [Approved](technical-design/runtime-closure.md)：command forms、exclusion materialization、checkpoint merge、partial failure、remote-action timing and access-context continuity | Closed through D-311；Adapter DTO detail stays preflight-owned |
| R3 | Client-web delivery | [Approved](technical-design/block-rendering.md)：route destination lifecycle、SolvedEmail projection、renderer navigation/materialization actions、HTML isolation and remote-resource policy | Closed through D-312；exact component/library seams stay preflight-owned |
| R4 | Acceptance | [Approved](acceptance.md)：four vertical Dovecot/client-web journeys、acceptance-owned useful corpus and optional external-provider smoke；no focused negative-path suite | Closed through D-314 |
| R5 | Implementation plan/preflight | [Approved plan](implementation-plan.md) + [completed preflight](implementation-preflight.md)：behavior-rewrite slices，database/client-web/shared-contract blast radius，migration/reset strategy，branch simulation、exact MIME Peer command and Impact Handshake draft | Closed through D-315 |

## Delegated Detail

- Exact MailAdapter request/result names、pagination/batching and protocol checkpoint serialization are implementation-owned
  under D-281 unless they pressure a frozen boundary。
- No organization、retrieval or generic query increment is assumed。Real Mail Acceptance may reveal one；only that observed
  blocker can authorize a minimal horizontal change。
- Durable PRD/Product TDD、core-py Unit TDD and client-web architecture updates follow implementation evidence and owner
  boundaries；the promotion candidates already live in the program documentation ledger。

## Adaptive Discussion Batches

- This is a temporary `mail-extension` design-closure tactic，not a task/program-wide workflow rule and not a precedent that
  automatically governs later units。Each later unit chooses its collaboration granularity from its own uncertainty and risk。
- Batch size follows one coherent dependency/risk closure，not a fixed number of fields or decisions。Closely coupled
  config、command、effect and outcome choices should be reviewed together when separating them would repeat context。
- Escalate only choices that materially change observable product behavior、domain ownership、durable authority、public
  contracts、irreversible data effects or a high-cost failure path with more than one credible answer。
- The main agent derives low-risk consequences、exact names、mechanical validation、ordinary error mapping and other natural
  implementation details，records them in the task packet and summarizes them at the batch boundary instead of asking for
  item-by-item approval。
- Implementation evidence may reopen a frozen boundary only when it demonstrates real pressure；the mere existence of
  another possible design does not restart discussion。
- Before escalating any question，apply the program [design-taste filter](../../design-taste.md)。Do not ask Sir to choose a
  dominated option merely to keep discussion moving；only credible non-dominated forks survive to human review。

## Shortest Closure Path

1. Close R1 MIME materialization with full input/effect/failure information。
2. Close R2a Source foundation/config，then R2b Mail collect/backfill；combine only mechanics that have no independent
   product/authority judgment。
3. **Use + Acceptance closure batch（closed）**：R3 is closed through D-312 and R4 through D-314。
4. **Delivery batch（closed）**：R5 and the derived exact MIME materialization Peer command are closed through D-315。
5. **Current gate**：perform the final Impact Handshake and wait for Sir's explicit start。
