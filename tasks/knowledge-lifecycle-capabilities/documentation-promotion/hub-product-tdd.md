# Candidate Hub Product TDD Batch

### Cross-unit contracts projected to Hub source

- block 是基本持久信息单元；block hydration 隐藏 inline/pointer 分支，resolver 联合 hydrated content 与
  local relations 得到 solved/use-facing interpretation，storage 只负责按 pointer 取得 actual content。
- source-specific input 通过 extension mapping 持久化为 block/relation graph；`SubGraphForm`
  是 write form，不是完整信息模型。
- memo root content 直接保存 memo-family `CanonicalMemo`；attachments、parent、references 只由
  graph components/relations 表达，backend read 只消费 resolver solved result。
- attachment relation 默认无序；正文内显式 attachment reference 是位置 authority。Memos 0.29.1
  是已证明的 source-defined order exception，应在现有 relation payload 中保留，不推动通用
  relation schema 变化。
- comment 复用 memo root mapping，并通过 parent relation 连接。
- product API version 与 CanonicalMemo resolver contract version 是正交版本轴；CanonicalMemo decoder
  由 versioned resolver identity 选择，不在 payload/BlockModel 重复 schema version。
- info-base local memo identity 是 `block.id`；不建立 generic `resource`、`source_key` 或 source
  binding table。
- future collector 采用 best-effort exact reconciliation；匹配不足宁可产生可整理 duplicate，
  不得 content/time fuzzy overwrite。
- 复杂度投入应由边际效益而不是理论完备驱动：先识别仍未解决的问题造成的实际损失，再选择能以最低
  dependency/obscurity 成本消除主要损失的机制，并在新增机制的边际收益不再覆盖其维护与错误成本时停止。
  D-056 是 reference pressure：content fingerprint 试图制造更强 identity，却带来 normalization/stability
  成本；独立 source-time watermark 以更弱、显式的保证取得足够的 duplicate reduction。具体 heuristic
  仍不得被描述为 identity、reconciliation 或 correctness proof。
- Cache/effect controls use stable，orthogonal vocabulary across peers：`refresh` bypasses and replaces an existing
  local snapshot from current authority；`materialize_missing` permits creation only when a required derivation is
  absent；`recompute` is an explicit organization command that regenerates an existing derivation；`invalidate`
  discards a cache without reading a replacement。`refresh` itself neither grants AI/graph mutation nor requests
  recomputation。Python uses snake_case and TypeScript uses camelCase。
- New InKCre-owned APIs do not use `force` or `reload` as aliases for `refresh`。Protocol-owned names remain exact，
  including a third-party `force` query parameter。Legacy source-job `full` is not a stable cross-source contract and
  must not be promoted before its mixed scan/reconciliation/order/pagination effects are separated。
- Direct relation selection uses `include_in` / `include_out`（TypeScript `includeIn` / `includeOut`）relative to the
  subject block：incoming has the subject as `to_`，outgoing has it as `from_`；neither option implies recursive graph
  traversal。
- D-039 已关闭 deployment-scoped Memos PAT：ordinary raw extension-config lifecycle、generic validated
  update ordering、exact public profile/v0-status-404 与 immediate replace/revoke。
- D-041/D-042/D-043/D-044 已关闭 partial-graph boundary、CanonicalMemo v1、PostgreSQL binary storage
  与 Memos relation grammar；D-045 要求单独修复 client-web config path；D-046/D-047/D-048 关闭
  owned cleanup、exact fixtures 与 family/product/access-mode extensibility seams。

### Implementation evidence used for promotion

- installed extension decoder retention、unknown resolver explicit failure、core-py route/config runtime
  与 client-web config path 已由 implementation/tests 证明。
- D-047 exact fixtures、D-046 deletion behavior、PostgreSQL binary storage、partial cleanup residue 与
  official MoeMemos APK journey 均有 executable evidence。
- existing `/{extension_id}` route 已由 MoeMemos pathful base URL 复用；route-auth composition、hot
  lifecycle、caller-session graph commands 与 writable storage 已实现。证据仍不支持 top-level mount、
  generic resource binding 或通用 extension/resolver registry redesign。

### Deferred technical scope

- collector scan/webhook/export、cursor、external identity 与 reconciliation。
- flomo/其他 memo product adapters 及其 fidelity contract。
- future perceptual/hybrid retrieval、new sink verticals and source-specific collection/reconciliation work。

