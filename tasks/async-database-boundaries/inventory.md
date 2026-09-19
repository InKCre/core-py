# 数据库迁移清单

清单以 `66ce59f` 为实现基线。下表列出直接 session/connection 引用文件；间接消费者随接口一起迁移，不将文本命中数当成调用图覆盖率。状态已更新到步骤 11 完成；原路径被删除或重命名时在表中说明。

| 对象 | 计划步骤 | 状态 |
| --- | --- | --- |
| `app/business/agent/main.py` | 03 | 已迁移 |
| `app/business/ai/main.py` | 03 | 已迁移 |
| `app/business/cron.py` | 06 | 已迁移 |
| `app/business/deployment_config.py` | 03 | 已迁移 |
| `app/business/extension/state.py` | 05 | 已迁移 |
| `app/business/graph_navigation_retrieval/main.py` | 08 | 已迁移 |
| `app/business/info_base/block.py` | 02 → 04 | 已删除，改由异步 service/repository 承接 |
| `app/business/info_base/main.py` | 02 → 04 | 已迁移 |
| `app/business/info_base/relation.py` | 02 → 04 | 已删除，改由异步 service/repository 承接 |
| `app/business/info_base/resolver/main.py` | 02 → 04 | 已迁移 |
| `app/business/info_base/storage/main.py` | 02 → 04 | 已迁移 |
| `app/business/info_base/storage/postgresql.py` | 02 → 04 | 已迁移 |
| `app/business/job.py` | 06 | 已迁移 |
| `app/business/lexical_retrieval/main.py` | 08 | 已迁移 |
| `app/business/organization/_shared.py` | 08 | 已迁移 |
| `app/business/organization/duplicate_assertion.py` | 08 | 已迁移 |
| `app/business/organization/evidence_stance.py` | 08 | 已迁移 |
| `app/business/organization/referent_anchoring.py` | 08 | 已迁移 |
| `app/business/organization/refinement.py` | 08 | 已迁移 |
| `app/business/organization/rumination.py` | 08 | 已迁移 |
| `app/business/organization/supersession.py` | 08 | 已迁移 |
| `app/business/organization/synthesis.py` | 08 | 已迁移 |
| `app/business/organization_media.py` | 08 | 已迁移 |
| `app/business/peer/main.py` | 03 | 已迁移 |
| `app/business/semantic_retrieval/main.py` | 08 | 已迁移 |
| `app/business/sink/main.py` | 06 | 已迁移 |
| `app/business/source/config.py` | 06 | 已迁移 |
| `app/business/source/job.py` | 06 | 已迁移 |
| `app/business/source/main.py` | 06 | 已迁移 |
| `app/database_contract/connection.py` | 09 | 已复核，保留 worker 内独立同步 adapter |
| `app/engine.py` | 02 → 10 | 已迁移 |
| `extensions/github/repository.py` | 07（04/05 先适配接口） | 已迁移并重命名 reconcile.py，SQL 归 Core persistence |
| `extensions/github/resolver.py` | 07（04/05 先适配接口） | 已迁移 |
| `extensions/github/stars.py` | 07（04/05 先适配接口） | 已迁移 |
| `extensions/mail/repository.py` | 07（04/05 先适配接口） | 已迁移并重命名 reconcile.py，SQL 归 Core persistence |
| `extensions/mail/resolver.py` | 07（04/05 先适配接口） | 已迁移 |
| `extensions/mail/source.py` | 07（04/05 先适配接口） | 已迁移 |
| `extensions/memos/family/attachment.py` | 07（04/05 先适配接口） | 已迁移 |
| `extensions/memos/family/graph.py` | 07（04/05 先适配接口） | 已迁移 |
| `extensions/memos/family/service.py` | 07（04/05 先适配接口） | 已迁移 |
| `extensions/rss/enrichment.py` | 07（04/05 先适配接口） | 已迁移 |
| `extensions/rss/repository.py` | 07（04/05 先适配接口） | 已迁移并重命名 reconcile.py，SQL 归 Core persistence |
| `extensions/telegram/resolver.py` | 07（04/05 先适配接口） | 已迁移 |
| `extensions/telegram/source.py` | 07（04/05 先适配接口） | 已迁移 |
| `extensions/twitter/bookmark.py` | 07（04/05 先适配接口） | 已迁移 |
| `libs/obsrv/log_handler_postgresql.py` | 09 | 已迁移 |

## 最终边界

运行时旧工厂和过渡 API 已全部删除，SDK 0.1.5 已正式采用。业务、HTTP、MCP、调度、扩展和日志均完成相应 async 调用链；测试同步 adapter 独立于运行时。readiness／CLI 是唯一明确保留的同步 contract adapter。下文是实现时的调查与阶段证据，其中旧版本及“待删除”描述仅代表当时状态；最终验收见 packet。

## 基线调查：入口、事务与间接消费者

- HTTP：`app/routes` 中的 graph、block/relation、entities、resolver；其余配置、Peer、Source/Sink、Job/Cron、检索和 organization 路由随 owner 迁移。提交错误在 `database_write` 边界映射，必须包含 commit 失败。
- Peer、Tool、JobHandler：`app/business/organization/tools.py`、各 owner 的 Peer inbound、`app/business/sink/mcp.py`、`source/job.py` 及 retrieval/organization jobs。变为 async 的调用不能留下未 await coroutine。
- schema 间接 I/O：`BlockModel.get_hydrated_content`；Resolver 的 `get_transfer_url/get_relations/get_existing`、materialization；GitHub 覆写身份规则。migration 后需逐项检查。
- 动态 session 工厂：`SQLExtensionStore._session_factory`；日志另有 `sqlmodel.Session(self.engine)`；readiness 直接 `psycopg.connect`。不能只统计 SessionLocal。
- 所有权：Graph 本次提交原子；Source 的 graph/blob/checkpoint 按协议用例组合；Cron occurrence+Job 同事务；Job claim/handler/close 分离；检索候选读取与外部投影、短写事务分离；Extension state transform 锁内无 I/O；日志独立事务；readiness worker 内独立 connection。
- 返回字段：Block INSERT 有 created_at/updated_at server defaults，Relation INSERT 有 updated_at；UPDATE 时间戳存在数据库管理，不能批量删除 refresh。Graph 仅返回 ID mapping。
- bootstrap/scheduler：`run.py` 的初始化、periodic callbacks 与关闭顺序；导入 OpenAPI 不得连接数据库。
- tooling/tests：步骤 10 扫描所有 `app.engine` 消费者。测试数据准备可以用独立同步 adapter，生产 async pool 不跨测试 event loop 重用。

## 基线调查：SDK 前提

已通过 GitHub main 源码核对 ext-reg owner：`runtimes/core-py/src/inkcre_extension_runtime_core_py/base.py` 与 `docs/30-unit-tdd/core-python-runtime.md`。当前依赖 0.1.3 的 update_config/get_state/mutate_state/mutate_config_and_state 以及 on_start 中 update_config_schema 为同步持久化接口。

步骤 05 优先上游 additive async capability，再采用并迁移内置扩展消费者；同步旧接口只服务声明的旧组合，不能调用新 async model。具体版本由上游 release owner 分配，不凭空指定版本或改用源码链接。Core 发布前应识别 artifact profile 中的受支持 wheel 集合，并确认兼容范围，无法确认的旧扩展不能默认为兼容。独立上游 artifact 尚未交付；它是步骤 05 的外部交付屏障，当前步骤 02–04 的独立路径不依赖它。

## 环境

实例 `cdf5b0ff179b59f1` 的 PostgreSQL 与应用已就绪。此前 SSH control socket 的 worktree 绝对路径 99 bytes，OpenSSH 创建临时后缀路径失败。已通过同一 provider API 建立本实例专属临时短路径 socket，并将路径记录在 runtime descriptor；未修改产品源码、未重置数据库。后续连接只从此 descriptor/credential 读取，不输出凭据。

## 历史阶段：已交付的过渡边界（步骤 03）

HTTP 配置 CRUD 使用 DeploymentConfigService；旧 DeploymentConfigManager 的 DB 方法仍供 Source、Cron、检索、组织及 Extension registry 配置消费，分别在 04／05／06／08 迁移后删除。schema 注册仍共用一个纯内存注册表。

AI get/list/chat/embed 与 bootstrap dialect 同步已使用异步 repository；sync_dialects 仅供既有测试／工具，can_execute 和其同步 target 读取留给步骤 06 的 JobHandler 与步骤 08 eligibility 迁移。Agent 定义 CRUD/run 已异步；同步 can_execute 同样由该顺序消除。

Peer 注册、发布、租约、发现、HTTP 与 delegation 已异步；内存 registry 保持同步。get/get_current_config 仅为 Extension registry 的同步配置解析暂留至步骤 05；对应 async 入口已提供。续租仍保持原来的发布事务后独立续租顺序。

## 历史阶段：步骤 04 的迁移状态

Block/Relation HTTP CRUD、entities batch read、Resolver invocation 与 relation/text、hydration、transfer URL、media 配置和 materialization 现在使用 native async 路径。GraphUnitOfWork 组合 Block、Relation、Storage repositories；flat graph 批量写入，Stars 按各 Resolver identity 协调，GitHub node_id override 已有 async capability。

旧 BlockManager／RelationManager／InfoBaseManager 的同步 CRUD、caller-session Stars 方法与 Resolver.get_existing(session) 仍供步骤 06 Source 和步骤 07/08 扩展／检索／organization 使用；新 HTTP/Resolver 路径不调用它们。Storage 的旧 get_storage(..., session)、create_raw_content/read_raw_content 等同理，具体消费者为 source/config、RSS enrichment、Memos attachment，以及 tests/scripts 的准备逻辑。最终在步骤 10 删除这些过渡入口，不把当前仓库当作可发布终态。

## 历史阶段：SDK 实际交付屏障

2026-09-17 检查 ext-reg 的 main `runtimes/core-py/src/inkcre_extension_runtime_core_py/base.py`，同步接口包括 update_config、get_state、mutate_state、mutate_config_and_state，以及 on_start 内 update_config_schema。get_config 只读取已绑定模型的 config，不直接访问数据库。GitHub release 列表最新 Runtime SDK 为 runtime-core-py-v0.1.3（2026-09-14）；Core 当前锁定该 wheel，尚无可采用的 async artifact。

Core 的 Extension Host 兼容版本由 `app/version.py` 的 CORE_VERSION=0.1.1 决定，不是 pyproject 中的 distribution 0.3.0。现有 producer metadata 全部限制 `<0.2.0`：GitHub 0.2.0、RSS 0.1.1、Mail 0.2.1、Telegram 0.2.0、Twitter 0.3.1、Memos 0.1.1、Learn English 0.1.0。前六者属于数据库采集迁移；Learn English 仍需纳入新的 Host 兼容与导入验证，不能因为没有直接 SQL 就漏掉。

SDK additive async API 与最终 Core async-only 导入接口的版本影响不同：前者可保留 SDK 旧方法供旧 Host，后者必须拒绝仍依赖旧同步 Core API 的 wheels。步骤 05 的具体接口、版本窗口和授权边界见唯一计划。

## 历史阶段：步骤 06 的迁移状态

Source catalog/config/state、Sink catalog/intent、Job admission/claim/close 与 Cron occurrence 已异步化。
AI/Agent can_execute、Organization configured_agent_available、Semantic profile eligibility 的读取链同步
迁移；旧 Source ensure_block 和 resolve_writable_storage 只留给步骤 07 的扩展 caller-session 路径。
SDK 0.1.5 已正式发布并采用，前述 artifact 屏障为历史记录，不再阻塞后续迁移。

## 历史阶段：步骤 07 的迁移状态

六个数据库 producer 的采集、Resolver、附件物化与对应 route 已使用异步用例/repositories。
GitHub/RSS/Mail 的 reconcile.py 拥有协调政策，SQL 仍归 Core persistence，不让业务持 raw session。
Source ensure_block/resolve_writable_storage 的 legacy 方法已无扩展消费者；GitHub Resolver 同步
get_existing override 仅为尚未清零的旧 Stars 路径保留。Memos 的同步测试准备仍通过旧 Manager，
随步骤 10 统一替换。
