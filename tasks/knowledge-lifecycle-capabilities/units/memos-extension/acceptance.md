# Memos Extension — Backend MVP Acceptance Contract

当前 MVP 验收的是 Memos `0.29.1` wire subset 与 MoeMemosAndroid `2.0.4` journey 的可证明闭环。
每个通过项给出适用的 HTTP、持久 graph/resolver 和 native response 证据；mutation 不得以单个
200 response 代替 primary info-base mutation 已持久化。

## Fixture contract

- **Server fixture**：以 MoeMemos base URL `https://<deployment>/memos/` 运行 Memos-compatible
  endpoint，`instance/profile` 报告 `0.29.1`，投影
  一个 deployment-scoped profile/creator，并使用一个无时间到期点、可替换/撤销的 Bearer
  credential 和至少两页
  NORMAL/ARCHIVED memo 数据。
- **Memo fixture**：Markdown body（含空白与 hashtag）、memo-side `createTime/updateTime`、
  visibility/state/pinned，以及至少两个可重排 attachments；root content 只保存
  `CanonicalMemo`，附件由 component block/relation 表达。
- **Graph proof**：create/update/delete 后检查 root block、component block、relation 和
  resolver solved result；禁止引入并行 Memos memo store。成功证明 primary mutation 已持久且
  response 与实际 committed state 一致；D-041 不要求 failure 后没有 orphan/stale components。

## Approved primary client matrix

下表覆盖 MoeMemos APK journey，并由 D-047 固定为 executable fixture contract。

| ID | Stimulus | Required proof | Execution | Decision prerequisite |
| --- | --- | --- | --- | --- |
| U-01 | APK 2.0.4 以 `/memos/` base URL 和 Bearer token 登录；version detection 经过 profile | `/memos/api/v1/auth/me`、GENERAL settings 成功；profile 为 `0.29.1`；单一 creator 稳定 | APK + unit | D-039, D-047 |
| U-02 | 同步 NORMAL 与 ARCHIVED | 两次 state 分流；每次 `pageSize=200`、creator filter、page token 直到末页；response 可解析 | APK + unit | D-042, D-047 |
| U-03 | 新建含 body、visibility、时间和 attachments 的 memo | MoeMemos 可先提交 unattached attachment；`POST /api/v1/memos` 成功后 primary root 已持久；resolver response 可被 APK 展示，允许 graph residue/incompleteness | APK + unit | D-042, D-043, D-044, D-047 |
| U-04 | 编辑 body/visibility/state/pinned/attachments | 缺失 mask 按 D-034 从原始 JSON key presence 推导；显式合法 `updateMask` query 保持 upstream 语义；两者都只改变选定 root fields；attachment omission/present-empty/set 被区分 | unit + APK evidence | D-042, D-043, D-044, D-046, D-047 |
| U-05 | 删除 memo | success 后 root 不再被 list/read；owned cleanup 遵循 D-046，允许 residue但不得误删 shared target | APK + unit | D-046, D-047 |
| U-06 | 上传、列举、下载、删除 attachment | `memo=null` orphan 可列举/删除；raw `/memos/file/...` 需 Memos Bearer；attach/reorder 保留 D-040 顺序；failure residue 可诊断 | APK + unit | D-039, D-043, D-044, D-046, D-047 |
| U-07 | resolver/native round-trip | graph → resolver → Memos response 保留 D-042 root facts 与 ordered attachment references；graph-owned fields 不复制进 CanonicalMemo | unit | D-042, D-040, D-044 |
| U-09 | 未列入最小集合的调用 | Explore/users、relations、reactions 等不作为 APK 必需条件；unsupported behavior 不伪装成成功 | unit negative | D-047 |
| U-10 | 经现有 extension API 执行 enable → disable → re-enable | route availability 在同一进程依次为 available → 404 → available；re-enable 无 duplicate routes，core routes 不受影响；decoder remains available for existing blocks | ASGI lifecycle | D-038, D-039 |
| U-11 | 不带 token、带 peer JWT、带 Memos token 分别访问 public detection、core API、Memos protected API | public detection 无凭据可达；core API 只接受 peer JWT；Memos protected API 只接受有效 Memos credential；两种 token 不可互换，普通 extension 仍默认 peer-protected | ASGI auth matrix | D-036, D-039, D-047 |
| U-12 | 经 peer-auth config surface 建立、读取、替换、撤销 PAT，并发送 omitted/invalid updates | persisted/runtime/read PAT config 一致；replace 后 old 立即 `401`、new 成功；revoke 后 protected `401`；omitted 保持、invalid/DB failure 不改变 persisted/runtime state；validation 发生在 persistence 前且不新增 Memos-specific config hooks | config + ASGI | D-039 |

## Approved packet-required protocol matrix

Comments 是首版 unit contract，但 MoeMemos 2.0.4 core sync 不调用它。它单独作为 protocol +
graph gate，不计入 APK E2E：

| ID | Stimulus | Required proof | Execution | Decision prerequisite |
| --- | --- | --- | --- | --- |
| U-08 | `POST/GET /api/v1/memos/{parent}/comments`，再以普通 memo endpoint 更新/删除 comment | comment 是独立 memo root，并以 parent relation 连接；list/read 可由 resolver 还原，update/delete 有 graph 断言 | protocol + unit | D-042, D-044, D-046, D-047 |

## Exact fixture architecture — D-047 / D-048

“Exact” means version-pinned and executable，not complete-server coverage：

1. **Product-generation fixtures**：Memos 0.29.1 JSON/query/header/status/error examples for only the
   approved endpoint subset。
2. **Client-compatibility fixtures**：MoeMemos 2.0.4 call ordering and deviations，especially public v1
   detection、missing `updateMask`、page token loop and pre-memo attachment upload。
3. **Family fixtures**：native input → D-042 CanonicalMemo / D-044 graph → solved resolver output，without
   importing Memos DTOs into the family layer。
4. **Runtime/integration fixtures**：route auth/hot lifecycle、PostgreSQL binary storage、residue/delete
   safety and client-web config request shape。

Candidate test ownership mirrors D-048：

```text
tests/extensions/memos/family/
tests/extensions/memos/products/memos/v0_29_1/fixtures/
tests/extensions/memos/products/memos/v0_29_1/test_adapter.py
tests/extensions/memos/backend/
tests/extensions/memos/integration/
```

Future flomo adapters add their own product-generation fixtures and must satisfy the reusable family
contract suite。Future collectors reuse family/product mapping tests where applicable but own separate
transport、cursor、reconciliation and partial-result fixtures。

## APK/tag evidence

- 验收 APK 必须是官方 `2.0.4` tag（commit
  [`9bfc6517`](https://github.com/mudkipme/MoeMemosAndroid/tree/2.0.4)）构建/下载的
  `moememos-v2.0.4.apk`，并记录 SHA-256
  `5043f14d27c4cc283cb1507a23a84f251e159ab8d3937da9842f2060bd7fe8fa`。
- 服务端必须固定在 Memos `v0.29.1` tag（commit
  [`5f194da`](https://github.com/usememos/memos/tree/v0.29.1)）；测试报告附 profile 返回的
  generation，不能只记录镜像的 `latest` 标签。
- 证据包至少包含：脱敏 HTTP transcript、APK tag/digest、持久 graph 快照、resolver solved
  result 与 create/update/delete 的客户端可见结果。

## Execution mapping ownership

- Acceptance gate 已批准 behavior/fixture contract；candidate test paths表达 owner，不假称文件已实现。
- [Implementation baseline](implementation-plan.md) 已把 U-ID 映射到 candidate test address、runner、
  command 与实现增量。
- Preflight 在 packet 中附上已核实的版本、地址、环境与可重复命令；Impact Handshake 再引用
  这些证据决定是否进入 Execute。

候选 test root 是 `tests/extensions/memos/`，按上面的 family/product/backend/integration ownership
分层。ASGI routes、PostgreSQL integration 和 APK E2E 是不同证据，任何一层都不能替代其他层。
