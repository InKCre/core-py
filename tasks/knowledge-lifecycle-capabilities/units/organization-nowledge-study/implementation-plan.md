# Organization Nowledge Vertical — Implementation Plan

> **状态**：D-526 accepted Implementation Plan。本文冻结依赖顺序、源码落点、验证与交付边界；不授权源码 mutation。
> Preflight 与 Impact Handshake 已由 D-527 关闭；Sir 已明确授权开始实施。

## 实施目标

把 D-493–D-525 已关闭的整组 Product、Technical 与 best-effort Acceptance 设计实现成一个完整 vertical：

```text
普通 Block / Relation / provenance 输入
  -> 七条独立 automatic Jobs
     -> 七个 concrete BehaviorResolvers 各自选 seed、理解证据、执行 SOP
        -> purpose-built Agent 可继续 retrieve / resolve / navigate
           -> behavior-specific exact mutation Tool
              -> 普通 Block / Relation graph authority
                 -> current/history、basis、referent、duplicate-component 等 later-use read
                    -> credentialed black-box whole-run review
```

这是一组功能的一次实施，不再切 delivery slice。下文编号只表达必须遵守的依赖顺序和检查点；任一中间状态都不作为
部分 Product、独立验收或提前发布单元。

## 预计源码形状

现有 `app/business/organization.py` 已同时承载 rumination orchestration、Agent Tools、Peer 调用与 media facade。继续把
六个模型塞进该文件会重新形成 monolith。实施时把同一 import address 迁为 package；`app.business.organization` 的公开
import 通过 `__init__.py` 保持兼容：

```text
app/business/organization/
  __init__.py                  # 稳定 re-export；不承担运行策略
  contracts.py                 # proposal/result、结构型 BehaviorResolver capability
  _shared.py                   # 仅 descriptor/candidate 与 configured-Agent 两组已重复 mechanics
  rumination.py                # RuminationBehaviorResolver
  supersession.py              # token、exact command、lineage read、automatic operation
  refinement.py                # token、exact command、automatic operation
  evidence_stance.py           # tokens、exact command、automatic operation
  synthesis.py                 # token、exact command、basis/reapplication、automatic operation
  referent_anchoring.py        # tokens、selected-text path、automatic operation
  duplicate_assertion.py       # token、exact command、automatic operation
  tools.py                     # shared meta-tools、candidate Tool、七种 behavior-specific write Tools
  jobs.py                      # 七个薄 JobHandlers
```

七个 concrete classes 都直接继承现有 `Resolver`；不增加 `OrganizationBehavior` table、runtime entity、Manager、dispatcher、
`ExecutionAdapter` 或 Agent-backed base class。`_shared.py` 只提取已经在七处重复、且没有模型语义的机制：

- 按 exact Resolver type 惰性 fetchsert 空 content descriptor，并在同一 caller-owned transaction 写 `candidate for`；
- 读取该 behavior 的 `core.organization.<behavior>` config，检查/运行完整 Agent definition 并等待 Turn。

候选规律、SOP、初始上下文、关系 token、proposal 验证、精确图修改、读取规律和日志 reason 仍留在各自 behavior module。
Agent/Thread imports 只出现在 orchestration method 的局部运行路径或 `tools.py`；exact mutation/read methods 的 import 和调用
不要求 Agent、AI provider、Job、Thread 或 Tool registry 存在。

新的非数据库 Pydantic contracts 放入 `app/schemas/organization_behavior.py`；现有
`app/schemas/organization.py` 继续拥有 rumination HTTP form 与 media interpretation contracts，避免为文件整齐而迁移无关
media 代码。数据库表、column、index 与 migration 都不变。

## 依赖顺序 1 — 把共享读取能力放回真实 owner

### Resolver typed read capability

将当前 `app/business/sink/projection.py` 中的 `ResolverMethodContract`、public `get_*` / `read_*` discovery、参数 schema 生成与
typed invocation 移到 `ResolverManager` 的管理能力；不增加到 `Resolver` base。实现文件可以在
`app/business/info_base/resolver/` 内保持小型分离，但 caller 通过 `ResolverManager` 取得 method contracts 并执行 validated
invocation。Manager 返回原始 typed value；MCP Sink 继续拥有 inline/Resource/transport projection，Organization Tool 只做
Agent JSON result 适配。

这次移动不扩大 MCP Sink 的公开接口，必须保留现有 method eligibility、逐 call 独立结果和 Resource 行为。它是本 unit 与
并行 MCP Sink unit 的唯一已知源码重叠；preflight 必须先核对对方 current edge 和未合并 diff，再冻结移动顺序，不能在
Organization 下复制 reflection authority。

### Graph Navigation capability

在 `GraphNavigationRetrievalManager` 增加已接受的：

```python
get_connected_components(
  seed_block_ids,
  *,
  contents,
  max_explored_blocks=1_000,
  max_explored_relations=10_000,
  db_session=None,
) -> ConnectedComponentsResult
```

相应 immutable schemas 放在 `app/schemas/graph_navigation_retrieval.py`。实现使用 caller-owned session、普通 BFS、
`RelationManager.get_endpoint_page()` 分页和 spanning proof；`contents` 必须非空，missing seeds 与 truncation 显式返回。
不增加 recursive SQL、component table、duplicate-specific index 或持久并查集。

Graph Navigation owner 同时提供其 public typed query method 的 discovery/invocation mechanics。它省略 `db_session` 这类运行
依赖，不把每个 query 拆成 Agent Tool，也不把 Relation meaning 或 Organization policy 引入 Graph Navigation。

retrieval 不新增 Manager：Organization adapter 直接组合现有 `LexicalRetrievalManager` 与
`SemanticRetrievalManager`。

## 依赖顺序 2 — 注册三个读取元工具

`app/business/organization/tools.py` 在现有 `AgentManager` registry 注册三个已接受的 Tool IDs：

```text
retrieve
resolver
graph_retrieval
```

- `retrieve` 接收一次 query 与 `lexical | semantic | hybrid` mode；`hybrid` 并行调用两个现有 Manager，原样保留两个
  native result 分支和分支内错误，不融合分数、排序或 identity。
- `resolver` 用 `describe | invoke` discriminated input 到达 Resolver owner 的 typed read capability；一次 call 失败不取消
  同批其它 call。`record_*`、`create_*`、`anchor_*` 等修改方法不属于这个读取元工具。
- `graph_retrieval` 用 `describe | invoke` 到达 Graph Navigation 的 public typed queries，包括 connected components；
  result 保留原 Pydantic outcome，不把 `limit_reached` 改写成 `not_found`。

元工具 adapter 只负责 Pydantic input、JSON 序列化和 Agent 可理解的逐项错误。它不增加 `Information` wrapper、
`OrganizationContext`、MCP dependency 或另一套 retrieval/query facade。每个 Agent definition 仍自由选择实际需要的 Tool
子集；初始 seeds 不是 Agent 的可见范围上限。

## 依赖顺序 3 — 建立七个 exact BehaviorResolver 载体

Core 通过一个显式 `register_core_organization_behaviors()` bootstrap import 注册七个 exact Resolver types：

```text
core.organization.behavior.rumination.v1
core.organization.behavior.supersession.v1
core.organization.behavior.refinement.v1
core.organization.behavior.evidence-stance.v1
core.organization.behavior.synthesis.v1
core.organization.behavior.existing-referent-anchoring.v1
core.organization.behavior.duplicate-assertion.v1
```

它与 `register_core_resolvers()` 并列由 runtime bootstrap 调用，不让 ResolverManager import Organization。每个 class definition
仍复用 `Resolver.__init_subclass__()` 的现有自注册；显式 bootstrap 只保证模块被加载，不做数据库写入或 descriptor sync。
Extensions 在自身启动时注册的 compatible BehaviorResolver 会被下一次 candidate Tool binding 看到。

每个 descriptor 使用 exact Resolver type + `content=""`，`get_text()` / `get_label()` 返回 code-owned 稳定说明。只有以下
真实 graph use 才在 caller-owned transaction 内惰性物化 descriptor：

- `record_organization_candidate(information_id, behavior)` 需要 target endpoint；
- exact behavior 读取自己的 incoming `candidate for` seeds。

Organization owner 定义最小结构型 capability，用于从现有 Resolver registry 识别可作为 candidate target 的 classes；它不
创建第二套 registry，也不要求所有 Resolver 获得 Organization methods。`record_organization_candidate` 始终只有一个动态
Tool；schema enum 来自本次 Agent definition 绑定时已经注册的 exact behavior types，执行时再次解析同一 capability。

七个 config keys 沿用：

```text
core.organization.rumination
core.organization.supersession
core.organization.refinement
core.organization.evidence_stance
core.organization.synthesis
core.organization.existing_referent_anchoring
core.organization.duplicate_assertion
```

每个 versioned schema 的值只有 `{"agent": <AgentID>}`。可以复用一个不可变 Pydantic value model，但 schema ID 与 key
一一对应（例如 `core.organization.supersession.config.v1`）；Agent definition 和 SOP 各自独立。config 不复制 model、
prompt、Tools 或 budget，不进入 descriptor Block。

### Agent definitions 是部署前置事实，不是 Core catalog

当前代码只有 persisted `agents` authority 和 `AgentManager`，没有 built-in Agent definition catalog；而 definition 又必须引用
deployment-local AI model ID，因此 Core 不能物化一个在所有部署都有效的默认 Agent ID。首版不新增 prompt template registry
或 startup sync：

- BehaviorResolver 固定自己需要表达的 request/context 和 exact Tool contracts；
- deployment 通过现有 shared database/config authority 创建七个 purpose-built definitions，并把各自 ID 写入上述 config；
- Acceptance setup 显式创建 exact definitions，记录 prompt/model/Tool identities，但这些测试 IDs 不成为生产默认值；
- 配置完成前 `can_run_automatic()` 返回 false，Job 保持 pending。

Preflight 已确认现有 operator path：purpose-built Agent definitions 通过 authenticated PostgREST `agents` authority 维护，
behavior configs 通过现有 Core `/configs/{key}` API 或同一 PostgREST authority 维护。因此本 unit 不增加 Agent catalog、
definition API 或额外 provisioning abstraction。是否需要新的长期管理 API 属于 Agent/Deployment owner 的另一个需求，
不由本 unit 推导。

## 依赖顺序 4 — 实现精确图修改与读取

各 exact method 按已接受的 operation contract 实现，不用一个 generic graph command 取代：

| BehaviorResolver | relation token authority | Agent-neutral method | 关键机械边界 |
| --- | --- | --- | --- |
| supersession | `supersedes` | `record_supersession()`、`read_lineage()` | 两端存在且不同；当前事务可见有向 cycle check；exact fetchsert；异常 cycle 的读取不声称 current frontier |
| refinement | `refines` | `record_refinement()` | 两端存在且不同；当前事务可见有向 cycle check；exact fetchsert |
| evidence stance | `supports` / `challenges` | `record_evidence_stance()` | evidence/assertion 不同；同 pair 的 opposite stance 拒绝；不做 DAG 限制 |
| synthesis | `synthesis`，复用 `edited` | `create_synthesis()` | 普通 text Block；至少两个不同来源；replay key 为 text + exact incoming basis；changed reapplication append 新 Block |
| referent anchoring | `has mention` / `refers to` | `anchor_existing_referent()` | source/target 存在且不同；occurrence-local selected-text Block；同 source/text/referent 两跳路径收敛 |
| duplicate assertion | `duplicates assertion` | `record_duplicate_assertion()` | whole-Block 等价判断已在上层完成；较小 ID 指向较大 ID；不删除、merge 或建 closure |

Rumination 继续使用其现有 `get_draft_graph_schema`、`draft_graph`、`submit_graph` 开放图 authoring；这三项只属于
rumination-capable Agent definitions，不扩散给其它 exact behaviors。

新的写入 Tool IDs 固定为：

```text
record_supersession
record_refinement
record_evidence_stance
create_synthesis
anchor_existing_referent
record_duplicate_assertion
record_organization_candidate
```

前六个分别调用同名 BehaviorResolver exact method；最后一个按动态 behavior type 调用 target Resolver 的 candidate
method。Agent 不提交 Relation content 或任意 GraphForm。

所有多写 method 遵循现有 Manager session convention：传入 session 时 caller 拥有 transaction 且 method 不 commit；未传
session 时 method 建立单次 transaction 并在全部验证和写入成功后 commit。失败不留下半个 synthesis、孤立 selected-text
fragment 或部分 basis。Relation token 是 behavior module 的公开 `Final` constant；producer 与 non-trivial reader 都 import
该 constant，generic InfoBase/Graph Navigation 不认识 vocabulary。未来 token rename 仍需要显式 data migration，改 Python
constant 不会伪装成迁移。

这里只在同一 behavior module 内抽取小型 relation fetchsert/cycle/replay helper。D-514 已确认当前只有 changed synthesis
是 `edited` 的真实直接调用者；不提前增加公共 `append_block_edit()`。

## 依赖顺序 5 — 实现七种自动 operation 与七条薄 Job

每个 BehaviorResolver 实现自己的：

```python
can_run_automatic() -> bool
run_automatic(max_seeds: int) -> None
```

`can_run_automatic()` 只做便宜、无副作用的本地 availability 检查。`run_automatic()` 才按模型选择：incoming
`candidate for`、模型特有 recent/incident signal 与少量 random fallback；每类有位置且 persistent candidate bucket 不永久
固定在同一页。一次 seed 触发一次 purpose-built Agent Turn；Agent 可以使用三个读取元工具继续探索，并只能通过 definition
声明的 exact mutation Tool 或单一 candidate Tool 产出图修改。

首版七种 judge 都可采用 LLM-driven Agent，但这个选择停留在 concrete operation：Graph/InfoBase/Resolver base、精确图命令、
读取方法和 Job runtime 都不依赖 Agent。未来某一 behavior 换成 deterministic 或 direct-AI implementation 时不改变其图
contract、Job type 或调用者。

`app/business/organization/jobs.py` 注册七个 independent Job types；共同参数只有：

```python
max_seeds: int = Field(default=10, ge=3, le=100)
```

Exact Job type IDs 为：

```text
core.organization.rumination.automatic.v1
core.organization.supersession.automatic.v1
core.organization.refinement.automatic.v1
core.organization.evidence-stance.automatic.v1
core.organization.synthesis.automatic.v1
core.organization.existing-referent-anchoring.automatic.v1
core.organization.duplicate-assertion.automatic.v1
```

Handler 的 `can_handle()` / `handle()` 分别薄调用 concrete Resolver 的两个方法；不读 config、不 import Agent/Thread、
不认识 Tool IDs、不写 successful `Job.state`。`app/database_contract/profile.py` 增加七个 checked-in Job profiles，`run.py`
在 `JobManager.sync_job_types()` 前显式 import handlers 和 Tool registrations。该 unit 不自动创建 Cron/schedule；部署者通过
现有 Cron/Job authority 决定运行频率。

每个 seed 的可恢复失败记录后继续；使整个 batch 无法继续的异常交给现有 Job lifecycle 标记 failed/timed-out。日志沿用
`job.<id>` trace，并只保存所选 IDs、bounds、outcome 与 behavior-owned reason code，不保存完整 content、prompt、模型响应或
chain-of-thought。exact mutation Tool 的 result 与完成后的 Thread Tool history 足以观察 mutated/replayed；没有持久修改时不
从自由文本臆测究竟是 no-op 还是 unresolved，而诚实记录 `no_persisted_effect`。不为补齐诊断分类增加 BehaviorReport、
或 completion Tool。

## 依赖顺序 6 — 迁移 rumination，而不重塑无关 Organization 路径

`RuminationBehaviorResolver` 接管现有 focal `ruminate()`、local evidence assembly、configured Agent run 与 automatic seed
path。`app/routes/organization.py` 的现有 HTTP/Peer contract、请求体和 `core.organization.rumination.v1` capability ID 保持
不变，只把 local call 从 `OrganizationManager.ruminate_local()` 改到 Resolver operation。

现有 `get_draft_graph_schema`、`draft_graph`、`submit_graph` Tool IDs 和 graph semantics 保持兼容；原有 rumination integration
journey 应继续通过。`OrganizationManager` 不再承载 rumination。`organization_media.py`、media interpretation Job/type/config
不属于本次 placement correction；只移除它们对 `OrganizationManager` facade 的不必要依赖，行为与 report contract 不变。

## 依赖顺序 7 — 黑盒验收语料与运行入口

首版默认采用 Sir 建议的独立 fixture 文件，因为两个 information worlds 已经足够大，且文件化直接改善审阅、来源维护与
以后复用；它仍不是 Acceptance gate，也不是通用框架：

```text
tests/organization/acceptance/
  corpus.py
  corpus/
    README.md
    manifest.json
    regional-service/
    incident-review/
  test_black_box.py
```

- 一个 source artifact 一个文件；manifest 只保存 world、artifact、普通 ingestion/provenance facts 与 readback alias。
- 不写 expected relations、target behavior、pair/source-set、selected text、focal hint 或 graph score。
- authored Git fixture 不重复维护 digest；外部 pinned artifact 才保存 URL、retrieved-at 与 digest。
- `corpus.py` 只做 manifest validation、artifact load 和 alias -> 实际 Block ID readback，不形成 shared corpus API。
- 第二个真实维护 owner 出现前，不上移到 top-level corpus、不增加 base class、registry 或 fixture generator。

`test_black_box.py` 标记为 explicit credentialed `integration` + `acceptance`，从普通 info-base 写入、真实 provider、Agent
definitions、deployment configs 和七种 automatic Jobs 开始；不调用 BehaviorResolver exact methods，不植入 candidate edges
或 focal IDs。两轮运行之间只加入设计规定的 observable upstream edit/graph change，再通过普通 Resolver/retrieval/Graph
Navigation readback 保存 before/after/use evidence。

该运行由 Human 对整组效果作 best-effort disposition。它不进入默认 `pdm run check`，也不因一次通过而声明概率可靠性、
完整覆盖或固定 relation 数量。实施时可以给它一个独立 PDM command；不改写现有 semantic-retrieval acceptance command 的
含义。

## 验证策略

### 实施过程中保留的窄验证

只为静态检查不能证明、且错误会改变可观察语义的边界增加 targeted tests：

1. 一个真实 PostgreSQL graph journey 覆盖 connected-component 的外部成员补全、missing seed、双 bounds 与 spanning
   proof；不镜像 BFS private steps。
2. 一个 exact-operation integration journey 组合 evolution、evidence、synthesis、anchoring 与 duplicate facts，验证事务
   rollback、cycle/opposite-stance rejection、basis/path replay 和 append-only changed synthesis；不为每个 token/字段复制
   一项 test。
3. 现有 focal rumination HTTP/Peer journey 在 Resolver 迁移后保持 observable behavior；不测试 `OrganizationManager` 的
   消失本身。
4. MCP Sink 原有 Resolver discovery/invocation journey在 authority 抽取后保持同一外部 result，防止跨 unit 回归。
5. 一个测试 Extension Resolver 通过同一 registration mechanics 成为 candidate target，并可提供 typed read；不为注册表、
   config mapping、Job profile 或 Tool enum literal 各写一项机械测试。

其它事实优先由 import、type、schema、lint、数据库 metadata 和 code review 静态覆盖。实施完成后运行受影响的窄 suite，
再运行 `pdm run check`；credentialed Organization Acceptance 独立运行并保留 residual。没有“覆盖率增加”或“一项合同一项
测试”的目标。

### Black-box evidence

运行证据记录 exact commit、corpus revision/digest、Agent definition/model/Tool identities、config keys、Job outcomes、
before/after graph、later-use readback 与 Human disposition。credential、provider 原始响应、临时数据库和 chain-of-thought
不进入 task packet 或 info-base authority。

material false authority 需要修复后重跑完整 two-world journey；reasonable abstention、miss、模型漂移、其它语言/领域、
外部 Storage pointer 静默变化和小语料无法估计的概率质量作为 residual 明示，不能不通过挑一次好结果消除。

## Durable truth 与交付顺序

实现证据成立后更新本地 `docs/30-unit-tdd/business-pipeline-and-authority.md`，把旧
`OrganizationManager -> Agent -> submit_graph` 单一路径改为 exact BehaviorResolver / Jobs / Tools / graph result topology；
若实现形成足够深的独立 Unit truth，再增加一个 local Organization Unit TDD，而不把 task packet 原样复制进去。

Product language、Organization/Resolver/Graph Navigation cross-unit contracts、Extension influence 与 shared claim matrix 的
durable owner 在 Hub `docs` repository。core-py context 不直接修改 `docs/_shared/**`：

```text
proved implementation
  -> 使用 edit-svc-shared-docs workflow 更新 Hub owner
  -> Hub 独立 commit / push
  -> core-py 独立 bump docs/_shared ref
  -> local Unit TDD / code delivery
```

Hub mutation、shared-ref bump 与 core-py code 不混在一个 commit。哪些 accepted task facts 达到 durable promotion 门槛由
实现与 Acceptance evidence 决定；“本 unit 很重要”或“未来可扩展”不自动证明所有研究材料都应提升为 shared truth。

## 已知分支与退化规律

1. **behavior config / Agent/provider 不可用**：Job 不 claim；不是 semantic no-op，也不 materialize descriptor。
2. **某个 seed 无法 resolve 或一次 judge 失败**：记录局部 outcome 后继续；共享 DB/retrieval/config 失效才结束 batch。
3. **初始 candidate 不足**：Agent 可继续 retrieve/resolve/navigate；没有证据时 abstain，不制造 graph authority。
4. **descriptor 并发首次物化**：首版只承诺顺序 fetchsert 收敛；无唯一约束下的罕见并发重复是明确 residual，不为理论
   完整性增加 table/global sync。
5. **generic Relation writer 绕过 exact command**：exact command 不主动制造已知 cycle/矛盾，但不宣称 database-level
   vocabulary enforcement；读取投影诚实暴露异常 topology。
6. **相同 synthesis text、不同 basis**：创建不同 Block；相同 text + exact basis 才 replay。相似措辞的语义重复仍由
   Agent 判断或 duplicate relation 表达。
7. **上游 observable edit**：沿 `edited` / `synthesis` basis 召回重新综合；结果 append 新版本。外部 pointer 静默变字节
   保留为 best-effort 缺陷。
8. **duplicate component 截断**：consumer 只能使用已观察 connectivity，不能把 provisional components 当作已证明独立。
9. **Extension behavior**：可以注册 exact Resolver，并按需提供自己的 config/Agent、direct-AI/deterministic operation 和
   Job；Core 不为它维护中心映射或隐式 schedule。
10. **一轮无图修改**：Job 可以正常 finished；这不证明全图已经整理，也不自动重试或写 evaluated state。

## Preflight evidence gates

进入 Impact Handshake 前完成以下只读或 disposable 检查：

1. 读取并对齐 MCP Sink unit 的 current branch/diff，确认 Resolver reflection authority 的单次移动、review owner 与不破坏
   transport projection 的顺序；若对方仍在同一代码上修改，先直接 reconcile actual overlap。
2. 枚举 current core 与测试 Extension 的 Resolver `get_*` / `read_*` signatures 和返回 shapes，验证 owner-level contract 能
   排除 `db_session`/variadic/untyped methods，同时保留 structured typed reads。
3. 用 disposable import spike 验证 `organization.py -> organization/` package migration、route import、Tool registration、
   Resolver registration 和 Job sync 没有 circular/import-order dependency。
4. 对现有 Graph Navigation endpoint paging 做数据库 probe，确认 connected-component 双向分页能同时执行 Block/Relation
   bounds，不需要新 index 或 recursive SQL。
5. 检查 exact operation 的 transaction addresses、`edited` constant owner、current graph query 能力与 Block identity；如果
   任一合同实际需要 schema/migration，返回 Technical review，不在实现中临时补表。
6. 使用现有 Thread message history 验证 mutation/replay 可观测；确认无持久效果时只记录诚实的
   `no_persisted_effect`，不解析自由文本、不新增 BehaviorReport/completion Tool。
7. 冻结两个 corpus worlds 的具体 artifact wording、provenance、distractors、outside-initial-neighborhood evidence 与 ordinary
   ingestion path；确认它们自然承载需求，而不是为 relation 清单拼句子。
8. 枚举 `app.business.organization` 当前 callers/tests、media interpretation boundary、Job profiles、run bootstrap 和 durable
   docs addresses，形成 Impact Handshake 的完整 `From -> To` 清单。
9. 核实现有部署维护 `agents` rows 和 `core.organization.*` configs 的真实入口；冻结本 unit 只需要部署前置步骤，还是存在
   一个会阻断首次启用的最小 operator-path 缺口。
10. 在冻结执行 branch/worktree 后重新运行 `svc status . --json`、相关 narrow checks 与 baseline `pdm run check`；区分当前
   task artifacts、其它 unit work 和本 unit 将修改的 exact files。

任一 gate 若推翻 accepted Product/Technical contract，就带具体证据退回相应设计层。否则形成 Impact Handshake，列出 exact
objects、`From -> To`、side effects、blast radius、invariants、verification 与 uncertainty，并等待 Sir 明确“开始”。

## 明确不实施

- Nowledge-branded type、Job、schema、Agent 或产品语言；
- Evolution Job、generic Organization dispatcher/manager/base class、behavior table/registry/report/ledger；
- Entity model、ontology/domain-vocabulary subsystem、Crystal lifecycle 或 Human synthesis approval state；
- graph-change event stream、cascade engine、通用 force payload、candidate completion/delete state；
- relation-content registry、JSON payload/version token、Relation Resolver 或 database vocabulary enforcement；
- SQL/Cypher Agent Tool、Neo4j、第二个 retrieval engine 或 MCP Sink dependency；
- generic `append_block_edit()`、全局 append-only enforcement、Storage content snapshot/version monitor；
- 自动创建 schedules、固定 use consumer、truth/confidence score 或 corpus completeness/reliability SLO；
- 为 fixture 复用预建的 shared corpus framework。
