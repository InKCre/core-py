# RSS Extension Hardening

- **Unit ID**: `rss-extension-hardening`。
- **State**: **Complete**；Sir 于 2026-08-03 接受最终验收方案，B0–B8 implementation、verification、
  durable reconciliation 与 owner-specific commits 均已完成。
- **Objective**: 让一个配置好的 RSS 2.0 / Atom source 能可靠地把 feed-native information 收集为
  resolver-readable graph，并建立可信的
  `source instance → collect job → graph → resolver → source state` reference contract。
- **Guardrails**: feed-authored information 保持 authority；full text 与 downloaded enclosure 是独立
  enrichment/materialization；不把 feed reader、organization、retrieval、所有协议 edge cases、S3 或
  generic source framework 偷渡进本 unit。
- **Verification**: 以真实 HTTP transport double + migrated PostgreSQL 驱动 source/job/graph/resolver/state；
  横向以真实格式 bytes、migration、PostgREST probe、core-py/client-web 全仓 static/runtime checks 证明。
- **Current Truth**: RSS/Atom behavior rewrite、shared hydration/storage/resolver contracts、Memos attachment v2、
  producer cut-over 与 durable owner projection 已落地。core-py `835f89a`、client-web `765b22f`、Hub docs
  `48b069f` 已提交；未 push、未 bump Spoke shared refs、未执行 production migration。
- **Next Step**: none for this unit。Program 重新选择下一个 implementable unit；future RSS hardening 只有在新
  product pressure 或已接受的 non-blocking gap 变成实际问题时才重新进入 gate。

## Completion Outcome

- RSS 与 Atom 保留既有 source type identity，内部共享 bounded HTTP/feedparser collection service。
- manual/scheduled path 产生普通 collect job；pending claim atomic，job diagnostics/status 与 source-state
  advance 对齐。
- exact feed/item identity、same-ID update、idempotent replay、conditional HTTP、unidentified
  create/discard/watermark、missing-old-item retention 与 retry residue 已形成明确行为。
- feed、item、enclosure 是 versioned canonical blocks；components/associations 只通过 relations 表达。
- feed-authored content 保持 authority；默认 full-text extraction 形成独立 `full_text` block，失败不改变
  primary collection contract。
- manual/automatic enclosure materialization 通过 resolver-instance command 与 configured writable storage
  形成唯一 semantic content child；image/audio/video/PDF/EPUB/ZIP/file 使用 exact `core.<kind>.v1` resolver。
- common horizontal result 包括 block-owned hydration、generic HTTP bytes、PostgreSQL bytes CRUD、九种 exact
  semantic resolvers、Memos attachment v2 与 client-web peer-local parity。

完整决定由 [program decision authority](../../decisions.md) 的 D-049–D-078 拥有；本 packet 不再复制逐条
decision text。稳定技术合同已投影到 [RSS Unit TDD](../../../../docs/30-unit-tdd/rss-extension.md) 与 Hub
PRD/Product TDD。

## Accepted Verification Horizon

### Primary product authority

[PostgreSQL integration suite](../../../../tests/extensions/rss/integration/test_feed_collection.py) 使用真实
loopback HTTP server 提供 RSS 2.0 / Atom bytes，并执行真实 parser、source instance、collect job、committed
PostgreSQL graph、storage hydration、resolver solved value 与 source state。它覆盖：

- atomic claim、success/failure status、structured diagnostics 与 legacy job-config rejection；
- first collect、304、same-ID update、new item、unchanged replay、missing old item 与 feed identity/config change；
- unidentified item create/discard/watermark；
- per-item partial persistence failure、state non-advance 与 retry convergence；
- separate full-text enrichment；
- manual/automatic enclosure materialization、real semantic bytes、MIME evidence precedence、unknown file fallback
  与 concurrent idempotency。

### Cross-cutting and regression authority

- Generated-on-demand real PNG/WAV/MP4/PDF/EPUB/ZIP/text/HTML/file samples prove Python semantic resolvers；derived
  outputs remain Git-ignored。
- A disposable migrated runtime passed authenticated PostgREST byte-exact create/read/same-pointer update/read/delete。
- Seeded Memos attachment v1 → v2 → downgrade and real PostgreSQL Memos graph journeys passed。
- core-py：Pyrefly zero diagnostics；293 passed / 19 environment skips；migration suite 22 passed / 2 skipped；
  real PostgreSQL Memos+RSS run 15 passed。
- client-web：complete `pnpm check` passed 56 tests、workspace type checks and production builds。
- repository lint、implementation-owned formatting、retired-ID scans、Hub SVC/doc-link validation passed；four
  unrelated pre-existing Markdown format drifts remain outside this unit。

### Accepted non-blocking limits

Sir 于 2026-08-03 明确接受以下 verification horizon，不把它们作为 unit-close blockers：

- 主验收是 business-runtime vertical integration，不是启动完整 deployment 后从外部 source API 配置并运行的
  process-level black box；source setup 与 job execution 部分直接使用 database/manager boundary。
- [live protocol smoke](../../../../tests/extensions/rss/integration/test_live_feed_protocols.py) 是显式 URL 驱动的
  optional fetch/parse check；最终验收未选择公网 endpoint，因此它被 skip，也不声称证明完整 collection graph。
- transient HTTP timeout、malformed whole feed、enrichment/storage/resolver failure、process interruption 与
  scheduler exact-one-job 的额外 failure probes 可作为未来 hardening evidence，但当前核心 MVP 后果已经具有
  足够可信度。

## Test Infrastructure Extraction Review

本 unit 没有再新增 generic test harness：

- 已有可复用基础设施是 `tests/conftest.py` 的 hermetic environment 与 on-demand semantic asset fixture，以及
  `tests/assets/semantic-content/` 的 source case table/generator。
- RSS HTTP routes、protocol revisions、feed identity、job/state assertions 与 graph cleanup 都携带 source-specific
  semantics；把它们抽成通用 source framework 会降低测试可读性并提前约束 CalDAV/Nextcloud 等不同协议。
- `INKCRE_TEST_DATABASE_URL` gate 的少量重复不足以支撑新的 abstraction。
- 当第二个 external-source unit 重复需要 loopback protocol-server lifecycle、ordinary collect-job journey 或
  graph cleanup contract 时，再以两个真实 pressure 提取最小 helper；RSS suite 将作为第一份 reference consumer。

## Supporting Evidence

- [Implementation plan](implementation-plan.md)：B0–B8 addresses、dependency order 与 execution evidence。
- [Implementation preflight](implementation-preflight.md)：library/runtime/migration/branch replay。
- [Library evidence](library-evidence.md)：parser/extractor selection。
- [Media/storage evidence](media-storage-evidence.md)：横向 storage/resolver/Memos pressure。
- [Semantic-content resolver contracts](semantic-content-resolver-contracts.md)：exact resolver IDs 与 capability
  semantics。

这些 supporting files 保存 expensive-to-recover evidence，不维护独立 active state。Commit、push、Hub publication、
shared-ref bump 与 production mutation 是 owner-specific delivery operations，不改变本 unit 的完成状态。
