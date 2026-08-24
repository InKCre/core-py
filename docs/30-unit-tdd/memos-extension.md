# Memos Extension

## Purpose

本文件记录 core-py `memos` extension 的稳定本地架构。它实现 memo-family authority，并以
Memos-compatible backend 作为首个 access mode。Hub Product TDD 只拥有 generic collection / organization /
application、graph、resolver、storage 与 Extension contracts；本文拥有完整的 Memos-specific product/technical
contract，包括 Python package、resolver ID、relation grammar、API version、transaction 和 acceptance 边界。

## Current Delivery Boundary

- ownership unit：`memos-extension`。
- active delivered access mode：Memos `0.29.1`-compatible backend。
- released acceptance client：MoeMemos Android `2.0.4`。
- backend 只实现启动、profile/auth/settings、memo list/write、attachment、comment 与 ordinary delete
  所需的 bounded API subset；未实现 endpoint 明确返回 non-success。
- flomo、Memos collector、完整 Memos administration/social/share API、其他 Memos generations 与
  info-base browsing 不属于当前实现。

## Package Topology

```text
extensions/memos/
  __init__.py                     extension runtime composition
  auth.py + config.py             deployment-scoped PAT contract
  family/
    schema.py                     CanonicalMemo / CanonicalAttachment / solved values
    graph.py + attachment.py      graph grammar and persistence repositories
    resolver.py                   CanonicalMemo v1 + relations -> SolvedMemo
    attachment_resolver.py        attachment block -> SolvedAttachment
    service.py                    memo-family commands and queries
  products/memos/v0_29_1/
    wire.py                       pinned native DTOs
    adapter.py                    native <-> family mapping
    routes.py                     bounded HTTP surface
    pagination.py                 generation-specific page token contract
```

`family` 不 import product DTO 或 FastAPI transport。`products/memos/v0_29_1` 可以依赖 family，
因此未来 product adapter、API version 或 collector access mode 不需要复制 memo graph authority。

## Runtime, Authentication, And Configuration

`Extension.api_dependencies()` 返回空 dependencies，使 `/{extension_id}` root 保持 auth-neutral。
Memos adapter 在 root 内组合：

- public：instance profile；完全不评估 `Authorization`。
- protocol-protected：current profile/settings、memo、attachment 与 comment routes；使用 Memos PAT。
- unsupported surface：不注册，不以空列表或假成功模拟兼容。

PAT 是 nullable ordinary extension config：`memos_pat_` 加 32 个 ASCII alphanumeric。它属于当前
deployment trust boundary，不建立 session、refresh token、PAT table 或 terminal-user record。比较在
request time 执行，因此有效 config update 后 replace/revoke 立即生效，无需重建 routes。

ExtensionHost 的通用 config pipeline 先把 patch 与 current config shallow-merge，再用 `config_cls`
验证 complete next value，随后写 DB 并替换 live config。invalid config 不改变 durable/runtime state；
disabled extension 可以预配置 PAT。

Enable/start 发布一个 retained extension-owned route set；disable/close 直接从 FastAPI dispatch 与
OpenAPI surface 撤销这组 routes。Re-enable 重新发布同一 ownership surface，不重复注册。close cleanup
失败时 routes 仍保持撤销，runtime entry 保留，后续 close/enable 可以继续完成 reconciliation。

## Canonical Root And Resolver Contract Version

Memo root resolver ID 是 `extensions.memos.memo.v1`。其 inline `block.content` 是 deterministic
`CanonicalMemo` JSON，且只包含 root facts：

- `body`
- source-authored `created_at` / `updated_at`，必须有 timezone 并 canonicalize 为 UTC
- `archived`
- `visibility`
- `pinned`

Block row `created_at` / `updated_at` 只描述 persistence，不能替代 memo-authored time。Canonical
payload 不重复 schema version；exact resolver ID 选择 v1 decoder。unknown version 不能猜测或降级。

Memo root content 不保存 attachment IDs、parent 或 references。`MemoResolver` 联合 root inline content 与
outgoing local relations，递归解析 attachment components，生成 `SolvedMemo`；backend read adapter 只消费
该 solved value。

## Graph Grammar

| From | To | `relation.content` | Meaning |
| --- | --- | --- | --- |
| memo root | attachment block | `attachment:<zero-based-position>` | Memos 0.29.1 source-defined ordered attachment slot |
| comment memo root | parent memo root | `parent` | independent memo is a comment of parent |
| memo root | referenced block | `reference` | non-owned reference |
| attachment metadata | semantic content block | `content` | exact content meaning and storage-backed actual bytes |

Attachment positions must be contiguous, unique, and zero-based。Changing order rewrites slot mappings；
它不是 linked-list contract。Relation payload strings are owned by this extension grammar，不是通用 relation
type registry。

Comment 与 ordinary memo 使用同一个 CanonicalMemo generation。Comment visibility 始终投影 parent
visibility；top-level list 排除拥有 `parent` relation 的 roots。Reference relation 从不进入 owned cleanup。

## Attachment Storage

Attachment resolver ID 是 `extensions.memos.attachment.v2`。Attachment metadata block content 保存
`CanonicalAttachment`：filename、media type、size 与 authored create time；不保存 pointer。

Metadata block 通过唯一 `content` relation 指向 semantic content block。后者使用 MIME exact match 得到
`core.image/audio/video/pdf/epub/zip/text/html.v1`，无法匹配时使用 `core.file.v1`；其 `storage=-4`，
`block.content` 是 PostgreSQL binary storage 拥有的 opaque pointer。

Built-in `postgresql_binary` 实现 core `WritableStorage`，把 UUID 对应的 actual bytes 存在
`inkcre.storage_blobs`。Storage table 只拥有 bytes，不拥有 filename、MIME 或 attachment identity。Upload 对
base64、filename、media type 与 decoded 32 MiB cap 做严格验证。

MoeMemos 可以在 memo create 前上传 unattached attachment；该 attachment 是独立 component，后续通过
relation 被 memo 拥有。Attachment list omission、present-empty 和 explicit set 是不同 mutation。

## Commands, Query, And Native Projection

`MemoApplicationService` 协调 family graph commands，product adapter 负责 wire mapping：

```text
Memos request
  -> v0_29_1 adapter
  -> CanonicalMemo / family command
  -> blocks + relations + optional storage-backed semantic content
  -> commit primary mutation
  -> MemoResolver / AttachmentResolver
  -> SolvedMemo
  -> v0_29_1 native response
```

- Equal-body create 不去重；local memo identity 是 root `block.id`。
- List 只扫描 exact memo resolver contract version，排除 comments，并按 canonical `created_at DESC,
  block.id DESC` 做 keyset pagination。
- Opaque page token 绑定 generation、creator compatibility filter、state 与 cursor；terminal token 是空字符串。
- Missing `updateMask` 时，v0.29.1 adapter 只按 raw JSON key presence 推导 selected fields；explicit mask
  不增加 inferred fields，并保留 `false`、empty string 与 empty list。
- PATCH 的 attachment list 是 complete set，可以完成 attach、remove 和 reorder。

## Failure And Deletion Boundary

HTTP success 表示 command 的 primary mutation 已持久，并且 response 来自实际 committed resolver state；
它不承诺完整 graph transaction 或 residue-free cleanup。

Delete 在 primary transaction 前构造有限、cycle-safe ownership plan：只沿 exclusive comment `parent`
和 exclusive attachment ownership，不沿 `reference`。Primary root 先删除并 commit；owned comment、attachment
block 与 raw bytes 随后 best-effort cleanup。Shared/multiple-owner component 不删除；cleanup failure 被记录并
允许留下 residue，不回滚 primary success。

未知 memo、invalid JSON/filter/token/mask、unsupported behavior、unknown resolver version、storage 或
graph failure 返回明确 non-2xx。实现不增加 audit、replay 或 compensation subsystem 来隐藏已接受的 partial
effect。

## Extension Seams

- memo-family canonical version 与 external product API version 是正交版本轴。
- future Memos API version 使用独立 versioned product adapter；persisted old resolver decoder 必须在
  extension installed 时仍可加载。
- future collector 是另一 access mode，需重新设计 external identity、cursor、reconciliation 与 source
  deletion；不能继承 backend MVP approval。
- provenance/reconciliation 优先使用外部系统能证明的 stable identity scope；不足时接受 best-effort
  duplicate，不用 content/time fuzzy match 覆盖不确定 graph state。
- 当前证据不支持 generic resource/source-binding table、通用 protocol mount 或新 extension registry。

## Verification Authority

- schemas、types、migration checks and wheel builds own mechanically enforceable package and persistence facts；
- the retained PostgreSQL integration journey covers HTTP → committed attachment graph → Resolver/native response and
  PostgreSQL binary storage；
- the accepted MoeMemos Android 2.0.4 journey remains historical black-box evidence for login、sync、create、attachment、
  edit、archive and delete。It is not duplicated as a fixture-shaped unit suite and does not imply full Memos compatibility。
