# Business Pipeline And Authority

Shared Product and cross-unit contracts are owned by `../_shared/10-prd/` and
`../_shared/20-product-tdd/`. This document owns only core-py's internal unit boundaries and
implementation direction; it must not redefine Peer wire behavior or shared capability semantics.

## Purpose

本文件记录 `core-py` 内部一条慢变量结构：

`extension -> source/protocol + resolver/storage -> info_base -> application/use`

它不是局部目录 hazard，而是跨多个 business subtree 的 unit-local architecture。

## 何时阅读

在以下情况先读这里：

- 修改 `app/business/extension/`
- 修改 `app/business/source/`
- 修改 `app/business/info_base/`
- 修改 `app/business/ai/` 或 application/use capability
- 修改这些子树之间的 ownership / dependency / authority

## Structure

### 1. Extension Is The Runtime Expansion Entry

- extension 是 runtime 扩展入口。
- extension startup 会发布 extension-owned API route、Peer inbound、public claim，并登记其 source、resolver、sink
  等 Python capability types。close/disable 只撤销 exact active effects；已 import 的 type registration 在当前进程
  单调保留，exact package version replacement 以 restart 为边界。
- extension API 默认继承 core peer JWT dependency；需要 public 或 external-protocol auth 的
  extension 通过 `api_dependencies()` 显式使用 auth-neutral root，再在自己的 child routers 上组合
  public / self-auth dependencies。
- extension config update 的顺序是 merge complete next value → typed validation → durable write →
  live assignment。disabled extension 也可先保存有效配置，下一次 enable 时加载。
- installed extension 的 persisted block decoder 不随 enable/disable 消失；运行 API/source 和读取
  已持久信息是不同 lifetime。
- extension 自己不拥有 core graph persistence，也不自动拥有 retrieval semantics。

### 2. Source And Protocol Adapters Produce Collection Commands

- source 负责从外部世界采集或记录输入。
- extension-owned protocol adapter 也可以接收 external client input；Memos backend 是首个已验证
  例子，它不是 `SourceBase` instance，也不因此获得单独的 memo object store。
- source 或 protocol adapter 负责 native shape 与 extension-owned canonical command 之间的映射，
  但不是 persistence owner。

### 3. Info-Base Owns Graph Persistence

- `InfoBaseManager` 是 block / relation / graph command 持久化协调者。
- producer 可以提出 recursive `StarsGraphForm` 或 flat signed-ID `GraphForm`；normalization、block/relation insert 与
  database-managed identity 由 info-base 协调。
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

### 5. Application Owns Retrieval Support；AI Execution Is Graph-Blind

- application/use capability 负责 graph projection、derived retrieval-record lifecycle、ranking 与结果合同。
- `AIManager` 只把 typed embedding/chat 请求路由到 AIModel → AIProvider → dialect adapter；它不理解
  Block、Relation、Resolver、organization 或 retrieval policy。
- `AgentManager` 把一个 persisted Agent definition（system prompt、model、Tool set、nullable tool choice、per-turn
  model-call budget）绑定为可复用的 Thread runtime。它依赖 graph-blind AIManager，但 Tool handler 的领域能力由
  调用方模块提供；Agent domain 本身不取得 organization、Resolver 或 graph authority。
- Agent Tool input 由 Agent runtime 根据 handler 的 Pydantic model 只校验一次。一个 Turn 是消息历史的唯一
  writer；并发 ToolCalls 只返回结果，完整 Assistant ToolCall + ToolResult batch 才原子追加到 Thread history。
- Thread persistence backend 拥有完整 Thread snapshot。当前只有 process-local in-memory backend；不存在独立的
  Turn、ToolCall、ToolResult、Message 持久化关系，也不承诺 checkpoint、resume 或 Agent-level exactly-once。
- `SemanticRetrievalManager` 是 projection/profile/record/ranking owner。Block semantic input 只来自 Resolver
  `get_text()`；Relation semantic input 由 RelationManager 组合 from-label、exact relation content 与 to-label，保留
  `to is from's property` 的方向语义。AIManager 只接收最终 typed text batch。
- semantic `maintain` 只扫描 missing/stale records，并越过 unavailable entity；`rebuild` 以调用开始时间为 cutoff。
  Manager method 不创建 job/dirty/lease/retry lifecycle，且 projection/provider work 不持有数据库 transaction；完整
  有效 batch 才短事务 upsert。Exact typed Job Handler 可调用同一 method 并把 bounded report 写入 Job state。
- `retrieve` 只比较 timestamp-fresh、dimension-compatible、non-zero records，返回一个全局排序的真实
  Block/Relation 列表；它不隐式维护 records，也不生成答案。
- Block/Relation 写入不隐式生成或删除 embedding records。Profile-scoped records 是 derived support，freshness 由
  owning use capability 根据 database-owned timestamps 判断。
- `LexicalRetrievalManager` 只为 Block 建立 `label + optional text` record。`context="lexical"` 是 non-recursive
  Block-local Resolver projection；parent 不复制完整 child text。literal/substring/`simple` term ranking 返回真实 Blocks
  与 bounded evidence，不生成 transient search entities。
- lexical maintain 允许 Resolver 在 exact capability 内 materialize missing faithful text child，但 record owner 不取得
  OCR/ASR、Storage 或 graph-write ownership。media description/summary 属于 Organization interpretation；Organization
  只改变 graph，后续 lexical maintain 才更新 derived records。
- semantic 与 lexical maintain/rebuild 都有 exact typed Job Handler。Manager method 本身仍不创建 Job；Cron 只通过
  generic Job template 产生 occurrence。

### 6. Organization Improves The Existing Info-Base Explicitly

- organization 是为后续 use 改善既有 info-base 的能力，不是 collection lifecycle 或信息状态。Block CRUD、source
  collection 和 extension protocol ingestion 都不会隐式触发 organization。
- 当前 explicit focal approach 是 `OrganizationManager.ruminate(block_id)`。它从 focal Resolver `get_text()` 与全部 direct
  Relations 构造 bounded context；other endpoint 只投影正数 Block reference、resolver ID 与 `get_label()`，不递归读取。
- deployment config `core.organization.rumination` 通过 schema `core.organization.rumination.config.v1` 选择一个 persisted
  Agent。缺少 config 与悬空 Agent reference 在 use 时分别失败；config relation 不取得 Agent 生命周期所有权。
- draft-capable Resolver 显式拥有简短 description、Pydantic input model 与 `create_graph(input) -> StarsGraphForm`。
  Agent run 只在 Tool schema 中看到当前 exact Resolver IDs；具体 input schema 通过 `get_draft_graph_schema` 按需读取。
- Agent runtime 对 `draft_graph` 的通用 payload 与 selected Resolver input 完成同一轮 Pydantic validation；Tool handler
  只调用 Resolver create，再交给 InfoBaseManager normalization。`submit_graph(GraphForm)` 是唯一 graph-write Tool。
- rumination 是一次显式、additive、best-effort attempt。不能理解或模型诚实 no-op 都浅层完成；model-call budget
  exhaustion 成为一个 organization-level failure，caller cancellation 传导到 Turn。没有 retry、rollback、run record、
  job、scheduler、freshness skip 或自动 deduplication。
- `OrganizationManager.interpret_missing_media()` 是独立 system-driven approach。它扫描尚无 `interpretation` relation 的
  image/audio/video Blocks，按 modality 选择 deployment-owned Agent，把 solved media 作为 canonical AI content part 交给
  Agent，并只接受现有 graph Tool 的 additive result。它不写 lexical records，也不是 Resolver faithful materialization。

### 7. Peer Discovery Routes Heterogeneous Runtime Capabilities

- Peers share database authority but may have different runtime abilities。`PeerManager` owns local inbound/outbound
  registries、full-snapshot publication、database-time liveness filtering and one-shot delegation；it does not understand
  capability payloads。
- Business owners retain typed codecs and non-delegating local seams。Current exact inbounds are
  `core.semantic_retrieval.v1`、`core.feature_retrieval.lexical.v1`、`core.organization.rumination.v1` and exact-target
  `core.extension.management.v1`。
- `core.peer.protocol.http.v1` owns normalized query/headers/body envelopes、Peer JWT and HTTP response projection。
  Generic failover occurs only after pre-dispatch failure or exact `InkCre-Peer-Execution: not-executed`；a normal domain
  response or outcome-unknown stops。
- `route_to_peer` is caller-local routing policy。It never enters the capability payload/advertisement and an exact target
  is never substituted。There is no generic invoke route、generic delegation job or readiness advertisement。

### 8. Sink Projects Info-Base Use Into External Work

- `SinkManager` 拥有 exact Sink type registry、persisted instance config 与 Peer-scoped enable intent；`SinkBase` 拥有一个
  running instance 的 active resources。Registration 不创建或自动运行实例。
- Sink 是 application/use 的下游 projection，不取得 Block、Relation、Resolver、Storage 或 retrieval authority。
  一个 Extension 可以交付 Sink type，但 Extension enable 不等于 Sink instance enable。
- `core.mcp.v1` 是首个实现：它把现有 retrieval、graph navigation 与 Resolver read behavior 投影为 MCP actions；
  oversized/binary content 通过 live Resource URI 重新读取当前 authority，不产生 Resource table 或缓存 authority。
- MCP 的 read-only boundary 排除 Agent-intended mutation command；Resolver `get_*` / `read_*` 仍可按其既有 contract
  lazy materialize missing derivation，因此相关 Tool 不虚假声明绝对无副作用。

## Cross-Subtree Constraints

### Allowed Direction

当前允许的结构性方向可以理解为：

- extension 扩展 source / resolver
- source 或 extension-owned protocol adapter 把 canonical collection command 交给 info-base persistence
- info-base 通过 resolver / storage 解释内容
- application/use capability 从 info-base / resolver 路径消费内容并维护 derived retrieval view
- application 只把 typed AI input 交给 graph-blind AIManager
- Semantic retrieval 通过 DeploymentConfigManager 解析 deployment default Profile，但 config manager 不取得
  profile existence、maintenance 或 ranking 语义
- organization/application 可以把准备好的初始 Message 与 caller-owned Tools 交给 AgentManager；Agent Tool
  handler 再显式调用自己的领域 owner
- Resolver-native graph draft 先保持 StarsGraphForm authoring，再由 InfoBaseManager 分配 signed local IDs；ResolverManager
  不持久化 graph，AgentManager 也不取得 Resolver/InfoBase ownership
- business capability facade may call its own local implementation or encode a Peer protocol envelope；provider inbound
  always calls the explicit non-delegating local path，preventing delegation loops

### Important Asymmetry

- Resolver 的 `get_text()` 是通用 Block interpretation，不是 embedding-specific hook。
- AI capability declarations/model routing 不反向进入 Resolver；retrieval owner 负责两者之间的 projection。
- Shared AI Provider credentials/config 可以持久化在数据库；peer-local adapter availability 仍是 runtime fact。
- Agent definition 是 shared database fact；Thread state、bound Tool handlers 与正在执行的 Turn 是 peer-local
  runtime fact。Agent definition 更新不会改写已经创建的 Thread snapshot。

## Non-Goals

本文件不承接以下内容：

- source 调度实现细节
- 某个 extension 的 native API、relation grammar 或 canonical schema
- storage 的 built-in ID、表或 migration 约定
- application 某个 retrieve mode 的算法细节
- deployment / scheduler / runtime topology

这些要么属于 local `AGENTS.md`，要么属于 `docs/40-deployment/`。
Memos 的已验证实现合同由 [memos-extension.md](memos-extension.md) 负责。
RSS/Atom source vertical 由 [rss-extension.md](rss-extension.md) 负责。
Semantic retrieval、embedding records 与 rumination 的内部合同由
[semantic-retrieval.md](semantic-retrieval.md) 负责。
Lexical feature retrieval、media textualization/interpretation boundary 与 lexical records 由
[lexical-retrieval.md](lexical-retrieval.md) 负责。
