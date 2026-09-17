# 线性实现计划与预演

## 状态与执行规则

Sir 已要求关闭设计阶段，转入实现计划及预演。本文件是唯一实现顺序；`design.md` 拥有已确认原则和设计理由，`packet.md` 只投影当前状态。Sir 已批准实现，设计与计划已提交为 `b379894`。Sir 随后明确允许提交、推送、创建 PR 和修改 ext-reg，禁止本 Agent 合并。正式 artifact 由已有 main 发布流程交付。

按 01 → 11 顺序执行，一次只有一个当前步骤；不另开并行 track 或重复计划。每步完成其当前范围的代码、调用方适配、必要文档和针对性验证后再推进。一个接口变为 async 时，在同一步适配它实际影响的所有调用点；文件目录不能切断调用链。后续步骤拥有业务内部迁移，前序步骤允许对这些文件做必要的接口适配。

前序切换可以保留未迁移路径使用的旧实现，但不得把新旧 session 拼接成一次事务，不引入同步阻塞等待 async 的包装，不把兼容层当作终态。每个临时入口记录具体消费者和删除步骤。阶段结果不自动成为可独立发布的版本；发布需满足 SDK／wheel／Core 兼容屏障。

验证按用户要求收敛：每步只做相称的静态检查与代表性行为验证；最终运行完整仓库 gate。复用已有真实数据库验收，只为具体事务、并发或取消风险补充必要案例。性能测量不是前置条件。

## 01 固定迁移清单和可执行前提

从当前 branch、origin/main 差异及工作区状态恢复基线；如 main 已变化，先评估本任务依赖变化，不自动丢弃现有 packet。按“入口 → 应用用例 → 查询／写入 → session/connection owner”补齐清单，覆盖 app、extensions、日志数据库 sink、database_contract、run.py，以及导入应用 session 工厂的 scripts/tests。记录每个原子集合、同步消费者、锁／RETURNING／触发器字段与替换步骤。

核对 ext-reg 实际源码版本、SDK 0.1.3 同步 state/config 与 lifecycle 消费者、已发布 wheel 对 Core Python import 的依赖，确定最小可兼容 async capability 及采用窗口。该步骤只把已确认的 ownership 转换为具体接口和交付依赖；如发现必须改变产品合同，则返回设计作一次有边界的修订。

恢复或选择一个隔离 PostgreSQL 验证环境；先诊断现有 SVC 实例缺 runtime.json 的失败，不重置其他实例。若本地不可用，核对现有 preview 是否能提供所需证据；不能把 preview 中的共享数据库当成允许销毁角色／schema 的测试库。

**返回条件：** 每个数据库入口都有归属和迁移步骤；同步工具与业务 runtime 可区分；SDK 的真实 source/release owner 和兼容屏障明确；正确性验证具备可用数据库或明确外部阻塞。已有 preview workflow 只是部署能力证据，不代表本任务已有运行实例。

## 02 建立 async 基础设施，交付 Graph 提交第一条完整路径

在现有 engine authority 内引入 AsyncEngine/session factory 和资源释放；使用原生 SQLAlchemy framing 实现窄 UoW。新增 session-bound Block/Relation persistence 与事务内 graph 操作，用应用入口拥有事务，首先接通 `/graph`。保留尚未迁移调用者的旧入口，名称与消费者明确，不能在同一 API 用可选 session 切换事务政策。

Blocks 批量写入 → flush 获得 IDs → 映射 → Relations 批量写入。只投影 producer 字段，避免把 graph 的负 local ID 写入数据库。返回提交后可安全读取的结果。核对调用方是否依赖逐项 refresh 的默认字段，不改变正 ID 引用检查与失败语义。

同时建立第一批能力边界限制，覆盖已迁移模块：repository 不创建 session／提交，业务不传 raw session。同步新增的实现说明进入现有 Unit TDD，清楚标注迁移状态，不宣称全仓完成。

**返回条件：** 新 Graph 提交路径真实 async；正确映射及关系失败回滚通过代表性 PostgreSQL 验证；资源可关闭；旧消费者仍有明确有效入口。除相关检查外不进行全量性能压测。

## 03 迁移基础配置、AI／Agent 与 Peer 数据库访问

依次处理 DeploymentConfig → AI 配置读取／catalog 写入 → Agent 定义读取写入 → Peer 记录／lease／outbound 数据访问。外部 AI 和 Peer 网络调用在短数据库作用域外执行；普通内存配置访问保持普通函数。更新直接调用方的 await 和 scheduler/route 签名，避免只改底层返回 coroutine。

Peer 的内存 capability 注册与数据库持久化分开辨认，不把所有同步注册机械改成 async。SDK lifecycle 若仍调用被替换的接口，保留精确兼容入口到 05，不能用缓存 deployment state 隐藏数据库访问。

**返回条件：** Resolver materialization 和 Extension Host 后续所需的配置／Peer 数据能力可原生 await；同一 session 未跨 AI/网络等待；受影响入口与 import-only 启动可用。

## 04 完成 info_base、Resolver 与 Storage 的全部数据库路径

依次迁移 Block/Relation CRUD 与查询 → Storage catalog/blob → hydration／Resolver 查询 → exact identity reconciliation／materialization。统一图提交、查询在 HTTP、Peer、Tool 中的使用，Relation endpoint 批量读取，按字段需要删除冗余 refresh。

检查 `BlockModel.get_hydrated_content()`、Resolver `get_relations/get_transfer_url/get_existing` 的间接 SQL。读取 storage 配置与下载实际 bytes 分开；materialization 不持有跨 AI 调用的事务。Stars reconciliation 保留不同 Resolver 的 exact identity 规则，GitHub override 与消费者在同一步适配。纯身份规则归其 owner，SQL 归 persistence adapter。

触及尚未内部迁移的扩展时，先完成接口兼容适配并记录剩余项；不通过统一 `Session | AsyncSession` 或随意 run_sync 抹平差异。旧路径只能独立使用旧作用域，不能参加新用例的事务组合。

**返回条件：** info_base 的对外业务路径及其 Resolver/Storage 数据依赖闭合；flat graph 与 Stars 语义均保留；外部 I/O 不持有数据库事务；所有旧接口消费者有显式记录。

## 05 完成 Runtime SDK 依赖交付，再迁移 Extension Host

按 01 确认的上游接口与兼容方案执行：在 ext-reg owner 中实现并验证最小 async 持久化能力 → 通过其治理流程交付可采用 artifact → Core 采用锁定版本 → 迁移 ExtensionStore／ActiveModel／Host 数据调用 → 适配内置扩展 state/config 消费者。只有需要数据库等待的接口异步化，纯 transform 保持同步且无外部 I/O。

上游 artifact 未可用、跨仓修改或发布未获授权时，本步骤明确等待，不把依赖替换成私有 fork、临时 sys.path 或未发布链接。若 async lifecycle 涉及共享合同，按 Hub 工作流先交付真实 owner，再单独 bump Spoke ref。

**返回条件：** Core 在声明支持的 SDK/wheel 组合下可安装、启用、读取／修改状态并关闭；事务、锁行和 enabled RPC 原义不变。依赖 delivery owner、Core 采用、扩展兼容分别有证据，不能凭单一源码检查跨越发布屏障。

### 步骤 05 的具体变更（已获跨仓授权）

对象为 ext-reg 的 `runtimes/core-py/src/inkcre_extension_runtime_core_py/base.py`、所属 SDK 验证与
`docs/30-unit-tdd/core-python-runtime.md`。从仅同步持久化接口，改为新增
`update_config_async/get_state_async/mutate_state_async/mutate_config_and_state_async` 及
`on_start_async`；Host model 提供对应 awaitable persistence capability。旧同步 API 保留供旧 Core，
不能让新 Core async Store 被旧入口调用。transform 本身保持同步，在 Host 持锁事务内执行；SDK
不持有 SQLAlchemy session。`get_config` 的普通模型读取不机械改成 async。

on_start 的 public effects 继续由原 publication 机制拥有。异步 schema 写入失败或取消必须撤销
已经发布的 routes/inbounds/claims；不复制一套 publication engine。Core facade 迁移后仍维护其
config 投影，新 Host 只调用 async lifecycle。验证聚焦 typed state/config 变更、awaited Host
调用和失败／取消后的 publication 清理，并构建 wheel 验证标准安装与导入。

影响范围为 Runtime SDK、Core Host adapter 和七个受支持的 first-party wheel；不扩展 Registry
服务或其他产品。SDK 的 additive artifact 可采用下一个可用补丁版本（目前候选 0.1.4，提交前复核
上游）；Core 删除旧同步公开接口则以新的 Host minor window 隔离（候选 0.2.x），相应 wheels
必须发布新 immutable version 并声明新 Host 约束，不能放宽旧 wheel 范围伪造兼容。

已在独立 origin/main worktree 实现 SDK 0.1.4，提交和 PR 已获授权。publication 的 Source catalog
同步也被确认是数据库 I/O；async startup 改用 SourceManager.sync_source_types_async，Core 采用时
必须先交付对应 catalog 能力，再迁移 Host，其余 Source 内部工作仍按 06 执行。

SDK 发布工作流只在 main 执行；Agent 不得合并 PR。完成上游 PR 后等待外部合并及正式 artifact，
Core 的正式依赖只采用已交付 artifact，不改成临时本地 wheel URL，不跳过本步骤继续 06。

## 06 迁移 Source／Sink 与 Job／Cron 事务组合

顺序为 Source 配置和持久化能力 → Sink 持久化能力 → Job 创建／校验／claim／close → Source JobHandler → Cron occurrence → scheduler 注册。Handler 及其他 Job 类型涉及 DB 的 normalize/can_handle 接口与调用方同一步适配；无数据库 I/O 的校验仍保持同步。

Cron 的事务同时持有 Job repository，Job 创建使用事务内操作，不调用独立提交入口。Job handler 执行不继承 claim session；取消／超时后的 terminal close 使用独立短作用域，并依据实际取消语义进行有限收尾。Source catalog/instance 与 graph anchor 的组合保持一个用例的事务。

**返回条件：** Cron occurrence 与 Job 同事务；claim、执行和 close 分离；async scheduler callback 实际被 await；代表性执行、失败及取消行为正确。此步不改 Source 外部协议，也不重建调度系统。

## 07 迁移扩展采集／协议持久化

依次完成 GitHub → RSS → Mail → Telegram → Twitter → Memos 的数据库路径；01 若发现其他受支持扩展，追加到此步骤的单一顺序。按协议 owner 把现有 repository 内自建 session／commit 移到应用用例，repository 构造时接收 session；使用已迁移 Graph、Storage、Source 能力。

外部采集／下载先完成，再进入需要的短事务；内容、关系、blob、source state/checkpoint 按原子集合提交。Memos 的附件和图编辑遵循已有 partial-effect/cleanup 合同，不能以全局原子性替代现有协议行为。保持 identity、行锁与并发 reconciliation 的既有保证，不额外发明去重策略。

**返回条件：** 内置及声明支持的扩展不再传 raw session 穿透领域层，不自建业务 session；代表性采集／保存／更新行为保持。发布 wheel 的 metadata/运行时版本约束与 05 的采用屏障一致。

## 08 迁移检索与 organization 应用用例

依次处理 lexical → semantic → graph navigation retrieval → organization 各行为及 media interpretation、Tool 入口。直接数据库查询落在所属 persistence adapter；图写入通过事务内能力组合或独立应用入口。并发 ToolCall 不共享 UoW。

读取候选后释放数据库作用域，Resolver/AI 计算后使用新的写事务。保留 freshness、cutoff、ranking 和既有 partial effects。优先处理明确的循环查询／逐项写入，不以本轮迁移名义改动 ranking 或引入缓存系统。

**返回条件：** 三类检索和 organization 的数据库调用链闭合；AI 等外部等待不持有 session；直接调用与 Agent Tool 的事务语义一致。

## 09 收敛 bootstrap、数据库日志与 readiness 适配

复核 `run.py` 的初始化、重试、heartbeat/lease、scheduler、关闭顺序，确保所有 runtime 数据库入口使用正确执行方式。停止接收工作并 drain 任务后再释放其数据库资源，不能提前 dispose；导入式 OpenAPI 生成不连接数据库。

PostgreSQL logging 仅调整数据库写入：独立作用域、不阻塞事件循环、不借用业务事务。同步 logging API 需要的最小异步桥接应支持已有 worker 来源；若引入后台 writer，必须管理有界积压和退出，不能新增通用日志框架或无界 fire-and-forget task。

Readiness 保持已有验证规则与响应，复核它的直接 psycopg connection 已在 worker 内创建和关闭的边界；如迁移为 native async，复用纯规则而非复制判断。如果最终保留现有隔离同步 tooling adapter，明确记录为受治理边界及理由，不声称运行时零同步驱动。具体 adapter 选择依据实现证据，不扩大为健康检查重构。

**返回条件：** 运行时入口清单全部闭合，日志/readiness 数据库路径有明确归属及非阻塞执行；任何最终同步适配边界明确可审阅，尚未接受时不能标记全量目标完成。

## 10 删除过渡入口，完成长期治理与整体正确性验收

先迁移 tests/scripts 对旧业务 SessionLocal 的依赖：测试数据准备可使用明确独立的同步测试 adapter，不能迫使 runtime 保留兼容工厂。Alembic／离线 tooling 保持其合理同步边界。清单无消费者后删除旧业务 factory、optional-session 双模式与临时 bridges，并关闭迁移豁免。

把 02 起逐步加入的治理覆盖到最终范围，接入 `pdm run check`。优先现有 lint 和类型检查，必要结构规则按具体能力检查；用合法／违规小样例确认约束有效，不能只禁止 `commit` 字符串。完成 Unit TDD、Deployment 和最近指南的协调更新，清除旧的模糊 session 指引；共享协议改动由实际 owner 先交付。

运行完整 `pdm run check`、受影响现有集成／验收和 OpenAPI 差异审查。只补足真实的事务组合、回滚、并发 claim 或取消资源风险，不扩展验证矩阵。没有 schema 需求时不产生 schema migration；发现必要 schema 变更先说明具体原因和影响。

**返回条件：** 必须实现目标全部闭合，治理可持续执行，已接受的边界与部署兼容清楚。此前 benchmark 未运行不阻塞该返回。

## 11 评估可复用 benchmark，然后交付总结

在 10 的正确版本上评估现有 preview 或隔离环境是否有完整应用、可控制测试数据与明确资源规格。条件合适时使用现有工具建设按需 benchmark，只覆盖 Graph 提交／批量读取、数据规模／并发参数及吞吐／p50/p95／错误率，记录版本和环境。成功及失败运行均追踪本次专属数据以清理，不删除其他任务数据。

没有可比旧版时报告当前结果，不伪造提升；没有合适环境或成本明显不合算时记录不建设的理由，直接交付主线。不能为了 benchmark 自动触发未授权 PR／部署／发布。无性能阈值 CI 门禁，不新增监控平台。

**返回条件：** 交付源码变更、治理、必要验证和兼容／残余说明；benchmark 有结果或清晰的未建设理由。提交、PR、发布仍遵守 Human 授权。父任务实际关闭前保留 packet。

## 已完成的静态预演

本节是基于源码调用关系的顺序和失败路径推演，不代表代码已实现、测试已执行或性能已验证。

| 推演场景 | 原顺序／直觉的风险 | 纳入计划的处理 |
| --- | --- | --- |
| 先完成 Resolver，最后才迁 AI | materialization await 到 AI 时，其配置读取仍为同步 DB；完整路径不成立 | 03 先提供 AI 数据能力，04 再关闭 Resolver 路径 |
| 只改 Block/Relation | hydration、storage catalog、get_transfer_url/get_existing 继续隐藏 SQL | 04 覆盖 schema method、Resolver 间接访问及 GitHub override |
| Core 直接把 Store 改 async | SDK 0.1.3 同步 model 接口收到 coroutine；状态语义或生命周期失效 | 01 固定能力与兼容窗口，05 先上游 artifact 再下游采用；停在真实依赖屏障 |
| 采集用例调用独立 submit_graph | Graph 提前提交，checkpoint 失败仍留下部分原子集合 | 02 提供事务内 graph 操作，06/07 组合 repositories，不调用自提交入口 |
| 大 Graph 的批量 INSERT | local IDs 错写、RETURNING 映射错误、分批被误作分批提交 | 02 投影 producer 字段、映射验证、保持同一事务；flush 不计作固定一次往返 |
| UPDATE 后直接删 refresh | 数据库触发器字段陈旧，API 返回不同时间戳 | 01 列出数据库生成字段，04 按字段返回需求保留或改用明确 RETURNING |
| Cron await 独立 Job.create | Job 和 occurrence 变成两个事务，可出现重复或进度不一致 | 06 同一 UoW 内创建 Job，保留锁和数据库时间 |
| Job 被取消后 await close | 新取消点可能打断收尾，或过早 dispose 阻断写入 | 06 有限收尾，09 drain 顺序及连接生命周期一并核对 |
| async engine 被多个 asyncio.run 复用 | 现有集成测试多次建 event loop，连接池可能跨 loop 使用 | 10 调整测试运行边界／显式 engine 生命周期，不为测试把生产 pool 改为 NullPool |
| 删除 SessionLocal 后“业务迁移完成” | tests、scripts、bootstrap、scheduler 仍导入或同步调用旧接口 | 01 纳入清单，09 runtime 入口收敛，10 消费者清零才删除 |
| 为日志 await 数据库 | logging.emit 是同步接口；逐条 create_task 无界且退出可能丢任务 | 09 只做必要桥接，独立事务及可管理生命周期；具体方案不能由普通 repository 偷担 |
| 把 preview workflow 当可用基线 | 本任务没有 PR/实例；资源和版本也未确认 | 11 明确先检查运行环境；允许无对照或暂不建设，不阻塞主线 |
| 治理留到最后 | 迁移途中新增路径继续复制旧模式，最终删除成本增大 | 02 开始限制新路径，逐步扩大覆盖，10 移除临时豁免 |

## 预演结论与待执行事实

已消除计划层面的依赖倒置：Graph 基础能力先于 Source 组合，AI 数据能力先于 Resolver 完整迁移，SDK artifact 先于 Host 切换，调用方先于旧工厂删除。整条计划无并行依赖环；每步只消费已交付能力或明确保留的旧独立路径。

仍需执行时证实的事实为：SDK 上游的实际源码位置与可兼容版本、支持 wheel 集合、隔离数据库可用性、日志/readiness 最小适配的具体代价、preview 的实例和规格。这些不改变已关闭的主体设计；若证据要求改变已确认合同或最终边界，明确回到该局部设计决定，不能用“实现细节”掩盖。
