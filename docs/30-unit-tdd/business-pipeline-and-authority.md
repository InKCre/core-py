# Business Pipeline And Authority

## Purpose

本文件记录 `core-py` 内部一条慢变量结构：

`extension -> source/protocol + resolver/storage -> info_base -> application/sink`

它不是局部目录 hazard，而是跨多个 business subtree 的 unit-local architecture。

## 何时阅读

在以下情况先读这里：

- 修改 `app/business/extension/`
- 修改 `app/business/source/`
- 修改 `app/business/info_base/`
- 修改 `app/business/sink/`
- 修改这些子树之间的 ownership / dependency / authority

## Structure

### 1. Extension Is The Runtime Expansion Entry

- extension 是 runtime 扩展入口。
- extension startup 会发布 extension-owned API route set，并初始化其 source、resolver 或其他
  runtime capability；close/disable 会先撤销该 route set，失败时保留 runtime entry 以便重试。
- extension API 默认继承 core peer JWT dependency；需要 public 或 external-protocol auth 的
  extension 通过 `api_dependencies()` 显式使用 auth-neutral root，再在自己的 child routers 上组合
  public / self-auth dependencies。
- extension config update 的顺序是 merge complete next value → typed validation → durable write →
  live assignment。disabled extension 也可先保存有效配置，下一次 enable 时加载。
- installed extension 的 persisted block decoder 不随 enable/disable 消失；运行 API/source 和读取
  已持久信息是不同 lifetime。
- extension 自己不拥有 core graph persistence，也不拥有 sink retrieval semantics。

### 2. Source And Protocol Adapters Produce Collection Commands

- source 负责从外部世界采集或记录输入。
- extension-owned protocol adapter 也可以接收 external client input；Memos backend 是首个已验证
  例子，它不是 `SourceBase` instance，也不因此获得单独的 memo object store。
- source 或 protocol adapter 负责 native shape 与 extension-owned canonical command 之间的映射，
  但不是 persistence owner。

### 3. Info-Base Owns Graph Persistence

- `InfoBaseManager` 是 block / relation / subgraph 持久化协调者。
- producer 可以提出 `SubGraphForm`，但 recursive insert / block fetchsert / relation fetchsert 由 info-base 协调。
- 需要协调多个 graph mutation 的 application service 可以给 `BlockManager` / `RelationManager`
  传入 caller-owned session；manager 不能擅自提交该 session。
- persistence helper 的 transaction 边界不自动成为产品级 graph-completeness guarantee；具体 command
  的 primary effect、partial result 与 cleanup 语义由 owning unit 声明。

### 4. Resolver And Storage Form The Interpretation Boundary

- block hydration 负责隐藏 inline content / opaque storage pointer 分支。
- resolver 负责把 hydrated content 与所需 local relations 联合解释成 solved/use-facing value。
- storage 只负责由 pointer 取得 actual bytes；`WritableStorage` 还可以拥有 pointer serialization 与
  byte create/update/delete lifecycle，但不解释 MIME 或信息含义。
- resolver contract version 由 exact resolver ID 选择。extension 即使 disabled，已安装 decoder 仍需
  能读取其 persisted blocks；unknown version 明确失败。
- solved value 是 derived runtime projection，不是与 blocks/relations 并列的 durable authority。

### 5. Application And Sink Own Retrieval Support

- sink 负责 retrieval、rerank、RAG 输出，以及 embedding lifecycle。
- info-base 当前可以在 block 写入时触发 embedding upsert。
- 但 “谁拥有 embedding” 这个问题，答案仍然是 sink，不是 info-base。

## Cross-Subtree Constraints

### Allowed Direction

当前允许的结构性方向可以理解为：

- extension 扩展 source / resolver
- source 或 extension-owned protocol adapter 把 canonical collection command 交给 info-base persistence
- info-base 通过 resolver / storage 解释内容
- sink 从 info-base / resolver 路径消费内容并维护 retrieval view

### Important Asymmetry

- `info_base/block.py` 调用 `sink/embedding.py` 做 upsert，是当前允许的结构性耦合。
- 这不表示 sink 可以反过来接管 persistence，也不表示 info-base 成为 embedding owner。
- 若要重构这条耦合，必须把它当成 unit-level architecture change，而不是某个目录的局部重排。

## Non-Goals

本文件不承接以下内容：

- source 调度实现细节
- 某个 extension 的 native API、relation grammar 或 canonical schema
- storage 的 built-in ID、表或 migration 约定
- sink 某个 retrieve mode 的算法细节
- deployment / scheduler / runtime topology

这些要么属于 local `AGENTS.md`，要么属于 `docs/40-deployment/`。
Memos 的已验证实现合同由 [memos-extension.md](memos-extension.md) 负责。
RSS/Atom source vertical 由 [rss-extension.md](rss-extension.md) 负责。
