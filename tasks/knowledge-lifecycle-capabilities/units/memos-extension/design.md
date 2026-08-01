# Memos Extension — Backend MVP Design

本文把已经确认的产品边界与待审查的技术合同放在同一条端到端链路上。决定 authority 仍是
[decisions.md](../../decisions.md)；协议和代码事实见 [evidence.md](evidence.md)。

## 1. Product Shape

Memos extension 是 memo-like collection 的可实现 ownership unit；Memos-compatible backend
只是它的首个 MVP delivery scope。该 MVP 复用市面上的 MoeMemos Android 客户端作为低摩擦、
多端记录入口，但不把该客户端扩张成 InKCre 的 use surface，也不复刻整个 Memos 产品。

首版目标固定为：

- protocol authority：released Memos 0.29.1 generation；
- compatibility client：released MoeMemos Android 2.0.4；
- persistence authority：InKCre block / relation graph；
- canonical boundary：memo extension-owned CanonicalMemo；
- read boundary：memo resolver solved result；
- account boundary：deployment-scoped single-user；Memos profile 是 protocol projection，不是
  core User。

MoeMemos 只证明“用户旅程需要哪些协议行为”；字段和错误语义仍以选定 Memos release 为
authority。为 MoeMemos 所做的偏离必须作为狭窄 compatibility shim 命名和测试。

## 2. End-to-End Topology

```text
MoeMemos 2.0.4
       ↕ base URL /memos/ + Memos 0.29.1 relative HTTP paths + Bearer token
generation-specific API adapter
       ↕ native request / native response
memo application service
       ↕ CanonicalMemo + graph commands / solved memo
graph transaction ── block.content / relations / component blocks ── storage
       ↕
versioned memo resolver
```

写路径的成功边界是 primary memo mutation 已持久；D-041 不保证 graph 完整或 failure 后无残留。
读路径从 root block 进入 resolver；adapter 不直接查询并拼装 block/relation rows。这样 native
API、canonical memo semantics 和 graph persistence 各自只有一个 owner。

## 3. CanonicalMemo and Graph Authority

### CanonicalMemo owns root facts

CanonicalMemo 是 memo-family 的 durable content contract，序列化后直接成为 memo root
`block.content`。它不是 Memos DTO，也不是与 graph 并列的 object store。

D-042 已确认 CanonicalMemo v1 exact root wire：

```json
{
  "body": "今天想到…… #idea",
  "created_at": "2026-07-30T10:20:30Z",
  "updated_at": "2026-07-30T10:20:30Z",
  "archived": false,
  "visibility": "private",
  "pinned": false
}
```

- `body` 是用户 authored Markdown；允许空字符串以支持 attachment-only memo，不 trim 或
  重写用户 whitespace。
- 两个时间是 memo-side authored/source times，不是 block row 的 persistence timestamps；
  使用 timezone-aware RFC 3339 UTC，未知时不可用 collection time 猜测。
- info-base local identity 只使用 `block.id`，CanonicalMemo 不复制 local `id`。
- Canonical generation 由 versioned resolver identity 选择，不写入 payload；unknown resolver
  identity 明确失败。
- `archived`、`visibility`、`pinned` 是需要 list/update/read round-trip 的 memo facts，且没有独立
  identity；D-042 因而由 root content 唯一持久。它们不是 graph component 或 adapter-only
  projection。

Unknown keys are rejected；deterministic serialization and product-native casing/timestamps remain
fixture obligations rather than new ownership questions。

### Relations own independently meaningful structure

| Information | Authority | Consequence |
| --- | --- | --- |
| authored body and memo-side time | root CanonicalMemo content | resolver 的主要 text / time 输入 |
| local identity | root `block.id` | Memos-facing stable name 如何编码需协议 fixture 证明，但不再造一份 local ID |
| attachment | component block + root relation + storage when needed | memo-family 默认无序；Memos 0.29.1 是 D-040 source-defined ordered exception |
| comment | independent memo root + parent relation | comment 可有自己的 body、attachments、time 与 lifecycle |
| memo reference | relation to target memo block | 不复制进 root content；target 不是 parent-owned component |
| tags/title/snippet/property | resolver-derived projection when derivable | 不建立第二份 durable authority |
| creator/location | 首版确实采集时使用 graph entity/relation | 只有证明独立寻址/use value 后才建模 |
| state/visibility/pinned | D-042 root CanonicalMemo | 没有独立 identity；不得塞入 `extras` 或 adapter-only state |

D-013 的无序默认仍成立；preflight 已证明 Memos 0.29.1 会刻意持久并返回 request order，因此
D-040 要求该 adapter 作为例外保留顺序。D-044 在现有 `relation.content` 中使用
`attachment:<zero-based-order>`，不改通用 relation schema；parent/reference 分别使用 `parent` /
`reference`。

## 4. Adapter Boundary

API adapter 只承担：

- 验证并转换 Memos 0.29.1 request；
- 调用 memo application service 的 canonical/graph command；
- 把 resolver solved result 转换成 0.29.1 response；
- 在 compatibility contract 内处理命名、pagination、filters、field masks 与 HTTP errors。

它不得：

- 直接把 Memos DTO 序列化为 block content；
- 绕过 resolver 读取 graph rows；
- 建立 Memos-specific durable memo table；
- 把未知字段塞进无边界 `extras`；
- 为通过客户端启动而返回与 persisted graph 不一致的假数据。

首版 HTTP surface 的证据分类见 [evidence.md](evidence.md)。D-047 将其冻结为三组：

1. MoeMemos startup/auth/settings 必需；
2. memo sync/write 与 attachment journey 必需；
3. Sir 已明确要求但不由当前 APK 覆盖的 comment contract。

除此之外默认 unsupported，不能从 upstream server 的完整路由表反推首版范围。

D-048 additionally separates three axes：memo-family core（canonical/graph/service/resolver）、product
generation mapping（Memos 0.29.1、future flomo）and access mode（current backend、future collector）。
Family code never imports product DTOs or transport；adapter mapping does not own DB sessions/cursors；
backend/collector orchestration invokes the same family service。This dependency direction is required now，
while a generic registry/framework waits for a second concrete adapter/access mode。

## 5. Identity, Account, and Compatibility

### Backend identity

本单元中 InKCre 自己是 memo authority，不存在需要与另一个 Memos server reconciliation 的
第二份 memo。`block.id` 因而是 local memo identity；Memos resource name 的可逆编码由 adapter
负责。source-native provenance 和 `source_id` fallback 主要是未来 collector 的压力，不应为
当前 backend 提前建立 source binding table。

### Deployment and protocol identity — D-033

MoeMemos 需要 current user、general settings、Bearer auth 和 creator-scoped list；这些是目标
protocol shape，不证明 InKCre 需要 core User。当前 InKCre 的 `ClientModel` 表示围绕同一
info-base 的 runtime peer，业务 rows 没有 terminal-user/tenant/owner ACL。

首版因此只投影一个 deployment-scoped Memos-compatible profile 与 default settings；所有 memo
graph 隐式处于同一 owner context，不增加 User/tenant tables，不把 `ClientModel` 冒充人，也不
做 per-user row filtering。外部 source account 仍可作为 connector configuration/provenance，
但不是 InKCre user。

Memos Bearer credential 的生成、寿命、撤销和它与现有 short-lived peer JWT 的关系已由 D-039
关闭；single-user 决定本身不等于直接复用当前 JWT。Memos `creator` / `visibility` 可以作为
协议 round-trip facts，但不能因此暗中引入多用户 ownership model。

D-036 已确认 auth ownership：core routes 和普通 extensions 默认使用 peer auth；Memos extension
拥有自己的 protocol auth。它不实现成 `ExtensionBase` 三态 mode：peer
verification 变成 route dependency，core protected router tree 与普通 extension router 默认挂载
它；需要 mixed/public/custom policy 的 extension 显式移除 base dependency，并以 FastAPI child
routers 组合。Memos protected child router 使用自己的 credential dependency，version detection
只有经 D-047 证明的 child routes 才无 dependency。这样不在 catch-all JWT middleware 中维护
`/memos` override，也不需要 extension sub-app/middleware。

必须保留的 minimal implementation shape（最终 symbol/module 名由 preflight 核实）：

```python
# Core protected route tree.
peer_api = APIRouter(dependencies=[Security(require_peer_jwt)])
peer_api.include_router(block_router)
peer_api.include_router(extension_management_router)
api_app.include_router(peer_api)


class ExtensionBase:
  @classmethod
  def _api_dependencies(cls):
    return (Security(require_peer_jwt),)

  @classmethod
  def _build_router(cls):
    return APIRouter(
      prefix=f"/{cls.__extid__}",
      dependencies=list(cls._api_dependencies()),
    )


class MemosExtension(ExtensionBase):
  @classmethod
  def _api_dependencies(cls):
    return ()  # The root only composes explicitly classified child routers.

  @classmethod
  def _register_apis(cls, root):
    root.include_router(public_detection_router)
    root.include_router(
      protected_protocol_router,
      dependencies=[Security(require_memos_token)],
    )
```

这段 example 说明 ownership 与 dependency topology，不冻结尚未 preflight 的文件名或完整 API。
最终实现必须保持 ordinary extensions fail closed，并让 Memos public/protected routes 在代码结构上
可直接区分。

不新增 `/memos/admin/*`。Credential 的建立、替换和清除复用现有 peer-authenticated extension
config surface：PAT 作为 ordinary Memos extension config 被验证、持久化、加载并通过 trusted
config surface 读取，不建立 Memos-only digest/projection lifecycle。Exact update behavior 见
[auth-contract.md](auth-contract.md)：一个 deployment-scoped
`memos_pat_` PAT，只有 v1 instance profile public，v0 status 保持 `404`，replacement 无 overlap。

D-037 固定 lifetime：credential 默认无时间到期点，直到通过 config 显式替换或撤销。首版不
引入 refresh token、session、automatic rotation 或周期性重新登录。数据库或 peer config reader
可恢复 PAT 是当前 config trust boundary 的显式取舍；未来若建立 generic secret config，Memos 与
其它 credential-bearing configs 一并迁移。

### Generation compatibility

- 首版只暴露 Memos 0.29.1 generation；0.30 与更旧 generation 明确 unsupported。
- future breaking release 使用 generation-specific adapter；相邻 generations 可在迁移窗口
  并存，但不能移除仍服务 live route/config 的 adapter。
- product API generation 与 CanonicalMemo resolver generation 正交。协议变更但 canonical
  semantics 不变时，新的 adapter 可继续写相同 canonical generation。
- `latest` 文档或 main branch schema 不能替代 release-tag contract。

## 6. Mutation and Failure Contracts Still to Freeze

### PATCH compatibility — D-034

Memos 0.29.1 要求 non-empty `updateMask`，MoeMemos 2.0.4 不发送它。只在此 generation
adapter 对缺失 mask 启用 shim：从原始 JSON 中实际出现的可更新 keys 推导 mask；显式合法
`updateMask` query 仍按上游语义处理。presence 判断保留 `false`、空字符串与空列表；未知/不可更新 key、空 mask
或不被字段合同允许的 `null` 明确失败。不得把这一宽松规则下沉成通用 update behavior。

### Coordinated writes — D-041

一次 native mutation 可能同时改变 root、attachments/comments/relations 与 storage。它们必须
由一个 application service 协调，避免 convenience paths 隐式决定业务顺序；但不对外承诺
transactional graph completeness。共享 PostgreSQL session 在实现更简单时可以使用，failure 后
orphan/stale components 允许保留。MoeMemos 先前成功上传的 unattached attachment 更是独立资源。

### Delete ownership — D-046

推荐 delete success 以 parent root 不再 list/read 为 primary effect，并 best-effort 清理 parent
relation、comment subtree 与 exclusively-owned attachment components/raw storage。shared reference
targets 保留；D-041 允许 residue；repeated unknown delete returns `404`。

## 7. Implementation-Plan Findings and Cross-Cutting Boundaries

早期 [implementation plan](implementation-plan.md) 已用真实代码地址和 MoeMemos 2.0.4 client
code 检验这条链路。它不是 implementation approval，却把“现有机制能否承载”从原则问题
收敛成了可定位的事实：

- **可以复用**：checked-in extension artifact discovery/install、built-in profile、
  generation-specific adapter package、`/{extension_id}` route namespace、exact-key resolver
  registration。MoeMemos 的 relative endpoints 与 path-preserving host 可直接使用 `/memos/` 作为
  base URL；当前没有证据需要 top-level mount、downloader、artifact registry 或 resolver registry
  redesign。
- **确定不能直接承载**：global peer-JWT middleware 无法验证 Memos Bearer credential；read-only
  `Storage` 无法完成 attachment upload/delete/download。
- **需要最小工程演进**：namespaced Memos route 的 auth dispatch、现有 extension start/close/
  disable correctness、session-aware graph mutations、writable storage，以及把 embedding 等 derived
  side effects 与 native commit 分开。D-038 要求 same-process hot enable/disable；由
  `ExtensionManager` 直接发布/撤下 retained extension-owned route set，不增加 persistent per-route
  running dependency、request-drain generation 或 isolated dispatcher。
- **仍由 extension 拥有**：Memos wire、CanonicalMemo、memo graph predicates、resolver solved
  model、query/native projection 与 owned deletion semantics。不得为了公共 helper 把这些语义
  下沉进 `InfoBaseManager`。

这些 pressure 进入 [pressure-ledger.md](../../pressure-ledger.md)，但不自动批准某一种方案。
D-039–D-045 已关闭 credential、failure boundary、CanonicalMemo、writable storage、relation
grammar 与 client-web path；具体改动仍需在 Execution baseline 和 Impact Handshake 中限定 blast
radius。

## 8. Remaining Review Sequence

Technical/Acceptance decisions、preflight and Execution baseline are complete。The next step is the Impact
Handshake for exact code/client-web/migration/doc state diff，then Sir's explicit “开始”。Any newly discovered
owner/observable-behavior branch returns to design review。
