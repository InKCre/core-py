# Memos Extension

- **Unit ID**: `memos-extension`。
- **Active delivery scope**: `memos-backend` MVP。
- **Objective**: 建立拥有 memo-family CanonicalMemo、graph mapping、resolver 与
  product-generation adapters 的 core extension；首个 MVP 让 MoeMemos Android 2.0.4 把
  InKCre 当作 Memos 0.29.1-compatible backend 使用。
- **Guardrails**: unit boundary 是 Memos extension，不是当前接入关系；backend MVP 只实现经
  上游合同与真实客户端调用共同证明的 API 子集；MoeMemos 是验收 client，不是协议 authority；
  不得建立并行 Memos object store；backend read 必须经过 resolver。collectors、flomo、完整
  Memos server、旧 generations、社交/分享能力不在当前 MVP，但可作为 extension 后续 scope。
- **Verification**: 以 [acceptance.md](acceptance.md) 的 HTTP → committed graph → resolver
  output → Memos response fixtures 为合同，并用发布版 MoeMemos APK 完成真实客户端 E2E。D-041
  明确不承诺“无部分 graph”；验证只证明成功响应对应的 primary mutation 已持久，且响应与实际
  committed state 一致。
- **Current Truth**: backend MVP 的 Product gate 已通过。InKCre deployment 是
  single-user/owner context；
  Memos profile 只是协议兼容 projection，不引入 core User、tenant 或 per-row ownership。
  Technical 与 Acceptance 已冻结；[implementation-plan.md](implementation-plan.md) 已经过
  implementation-address preflight 并成为 Execution baseline。MoeMemos 可通过 pathful base URL 复用现有
  `/{extension_id}` routes；没有证据需要重做 artifact/resolver registry。已确认需要的公共演进是
  route-auth composition、hot lifecycle repair、validated config update、session-aware graph mutation
  与 writable storage。D-039–D-048 已关闭 PAT/config、attachment order、partial-graph boundary、
  CanonicalMemo v1、PostgreSQL binary storage、relation grammar、client-web config path、owned deletion、
  exact API fixtures 和 future adapter/access-mode seams。Technical/Acceptance questions 已由
  D-039–D-048 关闭；完整排障见 [preflight.md](preflight.md)。I-01–I-08 均已关闭；官方 MoeMemos
  2.0.4 APK 已证明登录、双 state 多页同步、create、attachment upload/read、pin/edit、archive/delete，且
  真实调用发现并修复了显式空 `pageToken=` 的首页兼容缺口。E2E 数据、PAT 与 runner 已精确清理。
- **Next Step**: Sir 复审本 unit 的实现与 evidence；通过后再启动独立 durable documentation promotion
  batch，并另行决定 commit/publish 节奏。

## Lifecycle Gates

| Gate | State | Exit evidence |
| --- | --- | --- |
| Product | **Approved for backend MVP** | D-029–D-033, D-035；用户旅程、范围、single-user boundary、成功与失败语义获批 |
| Technical | **Approved** | D-034–D-048；owner、wire、auth、canonical、storage、relations、failure/delete 与 extension seams 获批 |
| Acceptance | **Approved as fixture contract** | D-047 + [acceptance.md](acceptance.md)；每个必要行为映射到分层 executable fixture |
| Implementation Plan | **Execution baseline** | [implementation-plan.md](implementation-plan.md) 已吸收 preflight 与全部获批决定；state diff 等待 Impact Handshake |
| Preflight | **Completed for current probe** | [preflight.md](preflight.md) 固定 pinned upstream/client、实现地址、运行环境、blast radius 与失败分支 |
| Impact Handshake | **Approved** | Sir 已批准 [impact-handshake.md](impact-handshake.md) 所界定的 address/object、state diff、blast radius、invariants、verification 与 uncertainty |
| Explicit Start | **Granted** | Sir 已明确说“批准，开始” |
| Execute / Verify | **Completed** | I-01–I-08 已通过 unit、repository-wide、migration/readiness、PostgreSQL HTTP→graph→resolver/storage/delete 与官方 APK journey；E2E residue 为 0 |

只有本文件维护 Memos extension 当前 delivery scope 的 phase、gate 和 next step。supporting
documents 只保存设计、证据和验收内容，不另设控制状态；未来 scope 不继承 backend MVP 的
approval。

## Approved Backend MVP Contract

### User journey

1. 用户在 MoeMemos 配置 InKCre endpoint 与 Bearer token。
2. MoeMemos 完成启动探测、读取当前用户/设置并同步 memo 列表。
3. 用户通过 MoeMemos 创建、编辑、归档或删除 memo，并处理附件。
4. 独立 protocol fixture 覆盖 comment create/list/update/delete；不假称 MoeMemos 2.0.4 会
   调用它。
5. write success 表示 primary memo mutation 已持久；随后 sync/read 从 resolver 的实际 committed
   state 重建相容响应，不额外保证 graph completeness。

### Success and observable failure

- 客户端看到 create/update/delete 成功，表示该 command 的 primary effect 已持久。
- 认证失败、unsupported behavior、unknown resolver generation、storage failure 或 graph
  mutation failure 必须返回明确 non-2xx；failure 后允许留下 orphan/stale graph components，不增加
  compensation/replay 机制只为恢复完整 graph。
- 对兼容范围之外的 endpoint 或 generation 明确拒绝，不以空响应伪装兼容。

### Included

- Memos 0.29.1 generation 的最小 startup/auth/settings、memo list/write 与必要 read-back。
- MoeMemos 2.0.4 实际依赖的 attachment upload/list/delete/download。
- comment 作为独立 memo root，并以 parent relation 连接；这是明确产品要求，即使 MoeMemos
  核心同步目前不调用 comment API，也要有独立协议 fixture。
- `NORMAL` / `ARCHIVED`、visibility 等进入已证明客户端旅程的必要 Memos 行为；其持久 owner
  已由 D-042 冻结。

### Not included in the MVP

- flomo backend；官方客户端尚无已证明的 replaceable-backend path，可在 extension 后续 scope
  发现新证据时重开。
- Memos 或其他产品 collector、webhook、export / backup ingestion；它们是 extension 的后续
  delivery scopes，不是另一个 canonical ownership unit。
- Memos 0.30 或 0.29.1 之前的 generation；未来 breaking generation 使用独立 adapter。
- 完整 Memos administration、explore/social、reaction、share 或与本旅程无关的 endpoint。
- InKCre info-base 的浏览、检索或 organization UI。

## Closed Technical Contracts

| Contract | Confirmed result |
| --- | --- |
| Canonical/graph | D-042/D-044：exact root wire；ordered attachment、parent、reference relation grammar |
| Storage/failure/delete | D-041/D-043/D-046：PostgreSQL binary storage；不保证 graph completeness；primary delete + best-effort cleanup |
| Protocol fixtures | D-047：只覆盖 bounded 0.29.1 subset、MoeMemos deviations 和 InKCre graph/resolver effects |
| Extensibility | D-048：family core、product/generation adapters、backend/collector access modes 分层；不提前造 registry/framework |

上述合同已获批。若 Impact Handshake 或实现证据发现新的 owner/behavior 分叉，必须退回对应
gate，而不是在 Execute 中临时决定。

## Confirmed Decision References

- Program/graph boundary: [D-001–D-007](../../decisions.md#confirmed)。
- Memo role and graph mapping: D-008–D-013、D-017。
- Canonical/resolver boundary: D-019–D-028、D-032。
- Unit identity, current delivery, deployment, PATCH, auth、hot lifecycle、canonical/storage/relation、
  failure/delete、fixtures and extensibility boundary: D-029–D-048。

`decisions.md` 是本任务唯一决定登记册。本文件只描述这些决定如何约束当前 implementable
unit，不复制完整 rationale。

## Supporting Material

- [design.md](design.md): 当前产品与技术合同的内聚草案。
- [auth-contract.md](auth-contract.md): D-039 的 exact credential、public-route、state transition 与
  minimal core seam contract。
- [evidence.md](evidence.md): released upstream、MoeMemos 调用面与现有 core 的可复核证据。
- [acceptance.md](acceptance.md): 实现前要冻结的行为/graph/resolver/E2E 合同。
- [implementation-plan.md](implementation-plan.md): 已冻结的端到端增量、代码地址、依赖与验证
  execution baseline。
- [preflight.md](preflight.md): pinned upstream/client、实现地址、纠偏结论、失败分支与 blast radius。
- [impact-handshake.md](impact-handshake.md): execution state diff、blast radius、invariants、verification and uncertainty。
- [Program packet](../../packet.md): program 范围、单元路由与交付循环。
- [Documentation promotion](../../documentation-promotion.md): 讨论产生的 durable-doc pressure。
- [Pressure ledger](../../pressure-ledger.md): 本单元传导出的横切机制压力。

## Gate Discipline

- Product、Technical、Acceptance 分别由 Sir 审查；提前形成的 Acceptance 与 implementation-plan
  probe 是发现问题的工具，不构成隐式 approval。
- implementation plan 可以在 Technical 阶段先形成 probe，并由 preflight 核实版本、地址、环境
  与失败分支；只有上游合同获批并关闭其暴露的分叉后，才成为可执行 baseline。
- 若 Preflight 新证据改变已获批行为、owner 或 blast radius，退回相应 gate，而不是在 Execute
  中临时改设计。
- durable docs promotion 仍延后到实现证据齐备后的独立批次；业务代码已在获批 Impact
  Handshake 与 Sir 明确开始后进入 Execute。task packet 在当前任务边界内持续记录执行状态。

## Execution Evidence

### I-01 — completed

- Core peer JWT 从全局 catch-all middleware 移到显式 protected route tree；health/docs 与 unmatched
  paths 不再被全局认证拦截。
- Extension API 默认继承 peer dependency；需要 public/self-auth 的 extension 通过唯一
  `api_dependencies()` hook 返回 auth-neutral root，再在内部组合自己的 dependencies。
- Extension route 以 retained child router 发布；disable/close 先撤销 routes，并用 FastAPI 0.139.2
  的 child + app route invalidation 行为测试固定热启停。
- 修复 running membership、duplicate start、close retry；close failure 后 routes 保持 fail-closed，
  runtime entry 保留用于重试。
- installed extension decoders 在 live API/source 之外加载；disable 不移除 persisted block 所需 decoder。
- Config update 采用 current + shallow patch → config model validate → normalized DB commit → live assign；
  invalid config 不写 DB/runtime，`on_close()` 不再回写 stale runtime config。
- Verification：`30` 个 focused tests、`159` 个 repository-wide tests 通过；I-01 touched files 的 Ruff
  与 Pyrefly 均通过。

### I-02 — completed

- 新增 checked-in `memos` artifact/profile 与 auth-neutral extension root；Memos 0.29.1 product-generation
  backend 将 public profile 与 PAT-protected routes 组合在自己的 child routers 中。
- `GET /memos/api/v1/instance/profile` 固定返回 `0.29.1`；v0 status 保持 unregistered；current user
  固定投影为 `users/inkcre`，其 role 使用 0.29.1 proto authority 的 `ADMIN`（而不是旧 generation 的
  `HOST`），GENERAL settings 固定默认 `PRIVATE`。
- PAT 是 ordinary nullable extension config，严格匹配 `memos_pat_` + 32 alphanumeric，request-time
  constant-time comparison 支持 hot replace/revoke；public profile 完全不评估 Authorization。
- Pinned JSON fixtures 固定 profile/current-user/settings wire；auth matrix、unknown user、hot revoke、
  disable/re-enable 与 route ownership 均有 ASGI tests。
- client-web 已在独立 repo batch 将 config request 从 `/{id}/config` 修正为
  `/extensions/{id}/config`，并增加 focused request-shape test。
- Verification：core-py `178` tests、Ruff、Pyrefly 通过；client-web focused Vitest、Oxfmt、Oxlint 与
  `@inkcre/core` TypeScript check 通过。

### I-03 — completed

- 冻结 exact CanonicalMemo v1 root content、UTC-aware timestamps 与 deterministic JSON；unknown root
  facts 和 naive timestamps 明确拒绝，attachments/parent/references 只从 relations 解出。
- 新增 family-owned graph repository、application command service 与
  `extensions.memos.memo.v1` resolver；product adapter 只做 0.29.1 wire ↔ family 映射，family 不导入
  product DTO/transport。
- `POST /memos/api/v1/memos` 的 text-only slice 已接通，Memos validation 以 `400` 返回；non-empty
  attachments 在 I-05 前明确拒绝，不能静默丢失。成功响应来自 committed root 的 resolver solved
  value；相同 body 不去重。
- Core graph primitives 增加 caller-session block get/edit/delete、relation create/update/delete；修复
  relation 双向查询从错误 intersection 为 union，并使 resolver relation cache 按 requested direction
  区分。
- Verification：core-py `194` tests、full Ruff/Pyrefly 通过；worktree PostgreSQL 分别证明 equal-body
  distinct roots 与真实 PAT HTTP create → committed block → resolver → native response，并精确清理测试
  roots，未 reset development database。

### I-04 — completed

- Family query 只扫描 `extensions.memos.memo.v1` roots、解析 CanonicalMemo 并从 `parent` relation
  排除 comments；无 memo object store、projection 或 index。
- NORMAL/ARCHIVED 分流按 canonical `created_at DESC, block.id DESC`；opaque token 绑定 generation、
  exact creator filter、state 与 keyset cursor，terminal token 为 MoeMemos 所需空字符串。两页之间的
  新插入不会造成 offset shift/duplicate。
- 0.29.1 PATCH adapter 在 `updateMask` 缺失时只从 raw JSON key presence 推导；显式 mask 不增加
  inferred fields，并保留 `false`、`""`、`[]`。selected null、empty/unknown mask 在 primary write 前
  `400`；attachments selected 在 I-05 前明确拒绝。
- Family application service 的 update 只改 selected canonical root facts，commit 后经 resolver 返回
  native response；unknown memo `404`。
- Verification：core-py `219` tests、full Ruff/Pyrefly 通过；worktree PostgreSQL HTTP 证明 2+1
  NORMAL pages、ARCHIVED page、comment exclusion、query-bound token 与 inferred PATCH committed
  resolver round-trip，并精确清理测试 roots。

### I-05 — completed

- 新增 generic `WritableStorage` caller-session read/write/delete capability，以及 built-in
  `postgresql_binary` storage type/instance；raw table 只保存 opaque UUID + `BYTEA`，attachment identity、
  filename/media type/size/time 与 pointer 仍由 attachment block content 拥有。
- 新增 `f2c8a6d1e4b7` migration、metadata/application-table/database-contract projection、production profile
  head 与 migration integrity entry；built-in setup 改为消费同一 profile authority，不再复制 storage
  literals。
- 新增 exact CanonicalAttachment v1、`extensions.memos.attachment.v1` resolver 与 orphan/zero-or-one owner
  graph semantics；MemoResolver 按 ordered relations hydrate attachment solved values，CanonicalMemo root
  content 仍不复制 attachment facts。
- Memos 0.29.1 backend 支持 PAT-protected upload/list/delete/raw download；严格 base64、non-path filename、
  media type 与 32 MiB decoded cap。memo create/PATCH 接收 existing attachment identities，relation
  `attachment:<position>` 保留请求顺序；omission/present-empty/set 区分并删除 omitted owned components/raw。
- Exact Memos attachment fixture 与 ASGI tests 固定 orphan/owned upload、auth、validation、cap、list/download/
  delete、create attach 与 PATCH reorder；opt-in PostgreSQL integration test 固定 orphan → attach → reorder →
  resolver/download → set removal → block/BYTEA cleanup，并精确清理测试 identities。
- client-web database-contract generated projection 暂不从未提交 core worktree 同步：development descriptor
  仍以 build source revision 为 provenance authority；待形成 coherent core commit/image 后再通过既有 workflow
  同步，避免伪造 cross-repo revision provenance。该压力不影响当前 runtime/API 行为。
- Verification：`check:migrations`、worktree database readiness（repository head `f2c8a6d1e4b7`、catalog/
  privileges/seed all ok）、PostgreSQL attachment integration、core-py `234 passed, 1 skipped`、full Ruff 与
  Pyrefly 全部通过。

### I-06 — completed

- Comment 沿用 CanonicalMemo root generation，以 comment → parent 的 `parent` relation 表示 owner；
  `POST /memos/api/v1/memos/{parent}/comments` 将请求 visibility 归一为 parent visibility，resolver/native
  response 从 graph 还原 `parent`，不复制进 CanonicalMemo content。
- `GET .../comments` 只沿 incoming parent relations 读取 independent memo roots，以 block identity
  descending keyset 分页；opaque token 绑定 parent，default/max page size 与 pinned generation 一致。
  top-level memo list 继续排除所有拥有 parent relation 的 comments。
- Ordinary memo PATCH 可更新 comment body/attachments；任何 root patch 都重新应用 parent visibility，
  防止 comment 漂离当前 parent policy。ordinary DELETE 同时适用于 top-level memo 与 comment；unknown/
  repeated delete 为 `404`。
- Owned deletion 在 primary transaction 前构造有限 visited traversal plan，只沿 exclusive parent 与
  attachment ownership，明确不沿 reference；multiple-parent/multiple-owner corruption 被跳过。primary root
  先 commit，随后 comment/attachment/raw cleanup best-effort 执行，failure 留 residue 但不撤销 primary
  success。
- Pinned protocol fixture 与 ASGI tests 固定 comment create/list token/parent response 和 ordinary delete；
  pure traversal fixtures 固定 nested postorder、multiple owner/parent skip、reference preservation 与 cycle
  termination。
- PostgreSQL proofs 覆盖真实 comment HTTP create → committed graph → resolver list/PATCH/delete、parent
  visibility、nested owned cleanup、reference/shared attachment target survival，以及注入 cleanup failure 后
  primary root removed + component/BYTEA residue retained；全部测试 identities 均精确清理。
- Verification：opt-in PostgreSQL `4 passed`；`check:migrations`、worktree readiness、core-py
  `240 passed, 4 skipped`、full Ruff 与 Pyrefly 全部通过。

### I-07 — completed

- Bounded protocol matrix 固定 public profile、PAT route、peer-token rejection、unknown user/resource、
  unsupported users/reactions/relations/admin surfaces、non-canonical identities、invalid JSON/filter/token/mask
  与 not-yet-supported input 均返回明确 non-2xx，不以空 response 伪装兼容。
- Route lifecycle proof 固定 disable 只撤销 extension-owned route set，re-enable 不重复注册 route/OpenAPI
  path；PAT replace/revoke 不重建 routes 即刻生效。Memos error translation 保持 validation `400`、unknown
  root `404` 与 unsupported route `404/405` 的边界。
- Verification：core-py `258 passed, 6 skipped`；Ruff 全量通过；Pyrefly `0 errors`；migration integrity
  `22 passed`、head `f2c8a6d1e4b7`；development database catalog/contract/migration/privileges/roles/seed
  readiness 全部为 `ok`。

### I-08 — completed

- Runner 使用官方 MoeMemos Android `2.0.4` release APK；SHA-256 为
  `5043f14d27c4cc283cb1507a23a84f251e159ab8d3937da9842f2060bd7fe8fa`。为避免占用主盘，本任务新增的
  Android 14 AOSP system image 与专用 AVD 实际放在 `/Volumes/WorkSSD/Android/inkcre-e2e/`，主盘只保留
  SDK 可发现它们所需的小型 link/index；runner 结束后整体清理。
- APK 以 pathful `/memos/` endpoint 和 synthetic PAT 登录；实际 call graph 依次经过 unregistered v1
  status fallback、0.29.1 instance profile、current user、GENERAL setting，然后分别完成 NORMAL 与
  ARCHIVED 的两页同步。为强制证明 cursor loop，数据库临时写入带唯一 marker 的 201+201 roots。
- 真实 MoeMemos 请求在第一页显式携带 `pageToken=`；原 parser 将它误判为 malformed token 并返回
  `400`。adapter 现将 empty token 与 absent token 同义解释为 first page，同时继续拒绝 malformed opaque
  token；exact MoeMemos query、comment empty token 与 route fixture 已回归固定。修复后四个 list calls
  均为 `200`，第二页使用 query-bound opaque token。
- APK 创建正文 `InKCre MoeMemos E2E create #inkcre-e2e` 并选择两张图片；committed root `475` 的
  attachment relations 为 `475 -> 473 attachment:0`、`475 -> 474 attachment:1`。resolver 以相同顺序
  组装两张附件；PostgreSQL `BYTEA` 大小分别为 `98981`、`100322`，declared/stored size 一致。客户端
  可显示正文与两张图片。
- APK 随后 pin 并将正文编辑为 `InKCre MoeMemos E2E edited #inkcre-e2e`；真实 PATCH 返回 `200`，resolver
  projection 保持 `pinned=true`、`visibility=PRIVATE` 与 `[473, 474]` attachment order。Archive 再次通过
  PATCH 完成；ARCHIVED list 读回 exact edited projection。客户端在 edit 后曾短暂保留本地
  `Memo not synced` 标记，但服务端 `200`、committed graph 与 resolver/API read-back 一致，故只作为
  client-local observation 记录，不改变 backend success 结论。
- 经 action-time confirmation，APK archived menu 的 Delete → Confirm 发出真实 DELETE 并回到列表；
  `memos/475` 在 NORMAL/ARCHIVED 都为 0 matches，blocks `473/474/475`、相关 relations 与 owned
  attachment list 都为 0，两个 raw URLs 均返回 `404`。删除前数据库有四个 blobs；删除后只剩与
  orphan blocks `471/472` 一一对应的两个 blobs，证明 owned deletion 精确移除了 `473/474` 的 raw，
  没有把 orphan 上传误判为 owned component。
- Cleanup 先经 attachment API 删除 `471/472`，再以 exact resolver + unique marker guard 删除
  `402` 个分页 fixture roots；最终 marker roots、E2E blocks `471–475` 与 `storage_blobs` 全部为 0。
  Synthetic PAT 已设为 null，extension enabled clients 为空，热撤销后 profile route 返回 `404`；清理后
  opt-in PostgreSQL suite `6 passed`，再次清理后 E2E blocks/blobs 仍为 0，database readiness 全部为
  `ok`。
- 专用 emulator 已正常停止；`/Volumes/WorkSSD/Android/inkcre-e2e/`、主盘 system-image link、AVD index
  与临时 APK 目录均已移除。没有移动或删除既有 emulator/platform-tools/其他 AVD；清理后主盘约
  `15 GiB` free、WorkSSD 约 `737 GiB` free。
