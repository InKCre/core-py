# info_base/ Local Guide

本文件只描述 `app/business/info_base/` 的局部事实、术语和编辑边界。跨
`extension/source/info_base/sink` 的结构先读
[business-pipeline-and-authority.md](../../../docs/30-unit-tdd/business-pipeline-and-authority.md)。

## 何时阅读

- 修改 `InfoBaseManager`、`BlockManager`、`RelationManager`；
- 修改 block hydration、resolver/storage contract；
- 修改 graph persistence、identity/dedup 或 embedding invalidation；
- 新增 common semantic content resolver。

## 关键文件

- `main.py`：`InfoBaseManager`，递归插入 subgraph；
- `block.py`：block CRUD/fetchsert 与 embedding trigger；
- `relation.py`：relation CRUD/fetchsert 与 direct direction query；
- `resolver/`：exact decoder registry 与 use projection；
- `storage/`：opaque pointer → actual bytes；
- `app/schemas/info_base/block.py`：persisted block 与 instance-local hydration cache。

## Content Vocabulary

- `persisted content`：`BlockModel.content` 字段；inline block 上是 actual text，storage-backed block 上是
  opaque pointer string。
- `hydrated content`：`BlockModel.get_hydrated_content()` 返回的 inline `str` 或 storage-backed `bytes`。
- `solved content`：resolver 根据 hydrated content 与 direct relations 形成的 typed/use-facing projection。
- `semantic content block`：用 exact core resolver ID 表达 text/image/audio/video/PDF/EPUB/ZIP/file 等信息的
  ordinary block。

不要在新文档/API 中重新引入 “real content” 或把 “raw content” 当作第二套 domain representation。Storage
与 resolver 内仍存在的 `get_raw_content` 是低层兼容 method name；它不改变上述共享 contract。

## Persistence And Graph Facts

- Source/extension 可以提出 `SubGraphForm` 或使用 caller-owned session 协调 graph command；info-base manager
  拥有实际 block/relation persistence。
- `InfoBaseManager` 先落 block 再落 relations；relation identity 当前是 `from_ + to_ + content`。
- Caller 传入 session 时，manager/helper 不得擅自 commit。
- Helper transaction boundary 不自动成为产品级 complete-graph guarantee；owning command 声明 partial effects。
- 默认 `Resolver.get_existing()` 仍按 `resolver + content` exact match；source-specific identity ladder 可在其
  repository/resolver 中拥有更强规则，不能在 route 层 fuzzy overwrite。

## Block Hydration

- `block.storage is None`：hydrated content 是 `block.content`。
- `block.storage is not None`：`block.content` 只交给 selected storage handler；handler 必须返回 bytes。
- Hydration cache 存在 Pydantic private state，以 `(storage, content)` 为 key，不映射到数据库、不进入 transport。
- `refresh=True` bypass 并替换当前 block instance snapshot；不承诺其他 ORM/peer instance invalidation。
- Storage-backed bytes 可独立变化，所以 `block.updated_at` 只表示 row 更新时间，不是 actual content freshness。

## Resolver Boundary

- `ResolverManager` 只按 exact ID select/register；unknown ID 明确失败，不存在 default decoder fallback。
- Core bootstrap 独立于 extension loading，注册九个 `core.<kind>.v1` semantic resolver。
- Duplicate registration：同 class 重复注册 idempotent，不同 class 抢同 ID 抛错。
- `get_text()` / `get_str_for_embedding()` 的 unsupported、supported-null 与 authored-empty 必须保持可区分。
- Resolver 可显式使用 `materialize_missing` 触发 absent derivation；读时写 graph 不是天然错误，但必须由 exact
  capability contract 声明。
- `include_in/include_out` 相对 subject block，且只筛 direct relations。

## Storage Boundary

- Storage 只解释自己的 pointer grammar 与 byte mechanics；不决定 MIME、filename、block kind 或 resolver。
- Writable storage 的 common create seam 接收 bytes 并返回可直接写入 `block.content` 的 pointer string。
- Extension 拥有 source/protocol-specific classification evidence order；`ResolverManager.match_media_type()` 只做
  exact common match。

## Embedding Ownership

- Block create/update 可以触发 embedding upsert/invalidation，但 embedding 仍是 application/sink derived support。
- Canonical block content 变化时必须移除 stale embedding；storage bytes 原地变化不会自动触发该机制。

## 编辑指引

- 修改 exact resolver ID、hydration/effect vocabulary 或 metadata→semantic pattern 时，先核对 Hub
  `knowledge-capability-contract.md`。
- 单一 protocol 的 relation grammar、identity ladder 与 transaction 留在 owning extension Unit TDD。
- 不用新增 generic metadata JSON、resource binding 或 media storage family 来绕开现有 graph/resolver boundary。
