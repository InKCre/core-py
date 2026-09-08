# Organization Nowledge Vertical — Implementation Preflight

> **结论**：2026-09-08 preflight completed，**ready with environment residuals**。未发现推翻 D-526 Implementation Plan 的
> 代码事实；可以进入 Impact Handshake。源码 mutation 仍需 Sir 明确“开始”。

## 检查边界

本次 preflight 回答四个问题：计划中的 owner/地址是否真实、既有能力是否足以支撑设计、并行 MCP Sink 是否形成冲突、
当前环境能否提供实现与验收证据。它不是实现，也不以让环境看起来整洁为目标。

检查基线：

- repository HEAD：`9991b3a45ebabf121653fb6d18458d0dd1e85da4`；
- current branch：`feat/knowledge-lifecycle-task-packet-recovery`；
- 普通源码与 durable local docs 没有未提交修改；现有 dirty state 位于本 task packet 和未跟踪的本地 skill copy；
- `svc status . --json` 报告 corpus、config、integration current，database target 已声明。

## 1. Resolver capability 的真实 owner 与迁移地址

当前事实：

- `ResolverManager` 已拥有 exact Resolver class registry、实例解析和 draft capability discovery；
- `Resolver` base 只提供每个 Resolver 的实际信息读取方法，不拥有跨 class 的反射管理职责；
- `app/business/sink/projection.py` 当前独立实现 `ResolverMethodContract`、public `get_*` / `read_*` discovery、Pydantic
  argument schema 与 exact method lookup；MCP 调用者在 `app/business/sink/mcp.py`；
- 对九个已注册 Core Resolvers 的运行时探查显示，当前可投影方法稳定为 `get_label`、`get_raw_content`、
  `get_relations`、`get_solved_content`、`get_text`、`get_transfer_url`；`get_existing(db_session)` 因参数不能成为 Agent JSON
  schema 而自然排除；未发现 Extension 自定义的额外 `read_*` surface。

因此实施地址冻结为：

```text
app.business.sink.projection 里的 Resolver method reflection
  -> app.business.info_base.resolver 下由 ResolverManager 暴露的管理能力
  -> MCP Sink 保留 transport / Resource projection
  -> Organization resolver meta-tool 只做 Agent JSON result projection
```

`Resolver` base 不增加 reflection API。Manager invocation 返回原始 typed value；bytes、Resource URI 和 inline budget 仍由 MCP
拥有。Organization 对不可 JSON 投影的结果返回明确 unavailable/error，不复制 MCP Resource protocol。

### MCP 并行工作核对

- MCP Sink 源码已在 commit `711d3cc` 落地，当前 thread 已 archived；没有 live/unmerged source diff；
- MCP implementation evidence 已记录 Resolver discovery/invocation Journey D，但仓库没有对应自动化测试；
- 本 vertical 将做 owner correction，并以同一个 external MCP journey 的手工/一次性重放作为兼容证据，不虚构“既有自动化
  regression test”。

这消除了并行写冲突；剩余风险是移动时误改 MCP Resource projection，已列入 implementation verification。

## 2. Graph Navigation 与数据库形状

当前 `GraphNavigationRetrievalManager` 已有 bounded neighborhood/path 查询；`RelationManager.get_endpoint_page()` 支持按
`from` / `to`、relation contents、cursor 和 limit 分页。数据库已有：

- `(from_, id DESC)` endpoint index；
- `(to_, id DESC)` endpoint index；
- Block/Relation `updated_at` authority，可用于 recent-signal seed selection。

因此 `get_connected_components()` 可以用 caller-owned session、上述 endpoint pages 和普通 BFS 实现，并显式返回 missing
seeds、block/relation bounds、truncation 与 spanning proof。没有证据支持 recursive SQL、component table、duplicate-specific
index、持久并查集或新 migration。

真实 PostgreSQL 性能/边界 journey 当前无法运行，见环境残差；这项证据延期到实现验证，不改变技术方案。

## 3. Organization 源码拆分与真实 caller

当前 `app/business/organization.py` 同时包含 rumination Agent Tools、orchestration 和 media facade。已枚举的直接 caller 为：

- `app/routes/organization.py`：`RUMINATION_CAPABILITY`、`OrganizationManager.ruminate_local()`；
- `app/business/organization_job.py`：只借 Manager facade 调 media interpretation；
- rumination、media、semantic/lexical acceptance tests：稳定 Tool constants 和 `OrganizationManager`；
- `run.py`：当前只通过 media Job import 建立相关 registration side effect。

实施时迁为同 import address 的 package，并由 `__init__.py` re-export 既有 Tool constants，避免无理由破坏调用者。focal
rumination 调用迁到 `RuminationBehaviorResolver`；media Job 直接调用 `organization_media` owner，不把 media 纳入七种 behavior
重构。HTTP/Peer request shape 和 capability ID 不变。

此 caller map 也确认不需要新 HTTP Organization API。

## 4. Agent definition 与 config 的部署路径

`AgentDefinitionModel` 已持久化在 `agents` application table；authenticated database role 对 application tables/sequences 有
现有写权限。虽然没有 Agent CRUD HTTP route，authenticated PostgREST database protocol 已是可用 operator path。

Deployment config 已有 `/configs/{key}` PUT/PATCH/GET route，也可经同一 PostgREST authority 维护。因此：

- 七个 purpose-built Agent definitions 是部署前置事实；
- 七个 `core.organization.<behavior>` configs 只引用各自 Agent ID；
- Acceptance setup 可创建 exact definitions/configs；
- 不新增 Core Agent catalog、prompt registry、startup sync、definition API 或中间 adapter。

## 5. Migration、dependency 与 bootstrap 结论

- database schema/table/index 无变化；不创建 Alembic migration；
- 现有 Python dependencies 足够；不增加 package；
- `Resolver.__init_subclass__()` 继续是 class registration mechanics；新的显式 bootstrap 只 import 七个 modules；
- `run.py` 必须在 `JobManager.sync_job_types()` 之前加载 behavior resolvers、Tools 和 Jobs；bootstrap 不 materialize descriptor；
- descriptor 只在 candidate edge 真实需要 endpoint 时于 caller-owned transaction 惰性 fetchsert；
- 不创建默认 Cron，频率继续由部署 owner 决定。

## 6. 代码地址清单

| 现有地址 | 实施后的 owner / 地址 | 变更性质 |
| --- | --- | --- |
| `app/business/sink/projection.py` Resolver reflection | `ResolverManager` 管理面；MCP adapter 调用它 | authority move，保留 MCP external outcome |
| `app/business/organization.py` | `app/business/organization/` package | 同 import address 拆分、稳定 re-export |
| `OrganizationManager.ruminate*` | `RuminationBehaviorResolver` | behavior carrier correction |
| `OrganizationManager` media facade | `organization_media` 直接 caller | 删除不必要间接层，不改变 media contract |
| Graph Navigation current typed queries | 同 Manager 增加 `get_connected_components()` 与 query discovery | 深化现有 owner |
| 无 behavior schemas | `app/schemas/organization_behavior.py` | 非数据库 Pydantic contracts |
| 无七 behavior modules | package 内七个 concrete Resolver modules | exact semantics / orchestration / relation token owner |
| 无 Organization meta-tools | package `tools.py` | 三读 meta-tools、六 exact writes、一个 candidate Tool |
| 无七 automatic Jobs | package `jobs.py` + database profile + bootstrap | 七条独立薄调度载体 |
| inline/分散验收输入 | `tests/organization/acceptance/corpus/**` | 可选但默认采用的独立 fixtures |

## 7. 基线验证

已运行：

- `pdm run check:foundation`：通过；
- 对 `app extensions libs migrations scripts tests run.py` 的 Ruff lint：通过；
- `pdm run typecheck`：0 diagnostics；
- `pdm run check`：未全绿，第一处阻塞为未跟踪本地 skill copy
  `.agents/skills/python-backend-code/scripts/audit.py` 的格式，不属于产品源码；
- 单独 `pdm run test`：`10 passed, 40 skipped, 10 errors`；十个 errors 均来自 Homebrew `libpq` 的 `initdb` 找不到同目录
  `postgres` binary，集中在既有 migration PostgreSQL fixture，而非测试断言失败。

## 8. 环境残差与处置

`svc dev status database` 显示现有 runtime 来自旧 descriptor/provider。`svc dev ensure database` 尝试重建时，远端 Docker
host `172.16.249.14:122` 在 SSH key exchange 阶段 reset；direct provider retry 又要求先 stop 旧 runtime。`stop` 会删除当前
worktree dev volume，preflight 没有为只读探查执行该破坏性动作。

这形成两个 execution-time evidence gates，而不是设计阻塞：

1. 实现中的真实 PostgreSQL graph journey 需要可用 database target 或完整本地 PostgreSQL binaries；
2. credentialed black-box Acceptance 还需要真实 provider、purpose-built Agent definitions 与 configs。

如果执行期环境仍不可用，静态/无数据库门禁可以继续，但不能声称相关 journey 已通过；交付时必须如实保留 residual。

## Preflight disposition

没有发现需要退回 Product、Technical、Acceptance 或 Implementation Plan 的矛盾。当前实现范围没有 schema migration、外部
dependency 或新公共 HTTP interface；最大变更面是 Organization package 化、ResolverManager authority move 和七种 graph
producer。该范围进入 Impact Handshake。
