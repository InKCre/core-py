# 数据库运行时迁移设计基线

Sir 已确认关闭设计阶段。本文是本任务已确认的设计基线；实现顺序及静态预演由 [线性实现计划](plan.md) 唯一维护。本轮仅完成设计复审和计划，不构成立即实施、提交或发布授权。具体 SDK 版本与数据库适配机制由实施前提验证确定；涉及已确认合同的变化必须显式返回局部设计。

## 已确认：session 生命周期与事务边界

Sir 已明确同意以下原则：

1. 可复用的应用用例决定原子业务操作的事务边界，HTTP、Peer、Agent Tool 复用同一入口。
2. 应用用例决定作用域的开始与结束；UoW 绑定同一 session 上所需的 repositories，并复用 SQLAlchemy 原生提交、回滚和关闭机制。
3. 独立应用入口拥有事务；事务内操作依赖必填的窄 UoW/repository。消除 optional-session 双重事务语义，组合操作不得调用会自行提交的独立入口。
4. Repository 持有 session，只负责查询、锁、写入及必要 flush/refresh；不能自建 session 或 commit/rollback。flush 不等于业务提交。
5. 作用域短且不跨并发任务共享。外部工作通常在数据库作用域之外执行，后续写事务重新校验必要条件。
6. 用真实数据库验证回滚、跨 repository 原子组合、无隐藏提交及异常／取消后的资源释放。

长期治理是本任务的必要交付，不因本次代码通过验收就视为完成。以下治理落点是落实提案，具体规则和工具应随实现边界验证，不把静态检查无法证明的性质承诺为 lint 保证。

## 目标边界

Sir 后续澄清本任务先只涉及数据库：主线是 session／事务边界，以及数据库操作异步化与性能优化。下面的日志和 readiness 分析只涉及其数据库访问，不能解释为授权改造日志系统或健康检查机制。是否保留某个隔离同步 adapter 不是设计主线的前置 Human 决策；先明确数据库职责、实际问题和迁移代价。

建议把目标表达为：每个并发执行分支独立取得数据库工作作用域；应用用例拥有短事务；持久化适配器持有 session；领域逻辑、Resolver 和协议处理不管理 session 生命周期。跨数据库与外部系统的流程显式拆成读取、外部工作、重新校验后的写入。

“AsyncSession per request/job/task”不能理解为整个请求或 Job 必须共享一个 session。SQLAlchemy 会在第一次数据库操作后 autobegin；即使尚未写入，跨 HTTP/AI await 持有 session 也可能保持事务和连接。一个请求可以顺序经历多个作用域，一个 Job 的 claim、domain effect、close 必须是不同的事务。并发 ToolCall 各自使用作用域，不共享父级 UoW。

应用用例拥有事务，不要求所有 HTTP handler 都直接 begin。HTTP、Peer、Agent Tool、Source 和 Scheduler 调用同一个应用入口；业务多步原子性在这个入口保持，避免各 transport 各写一份事务政策。需要组成一个事务的内部操作接收必填的窄 UoW/repository；独立应用入口不接受可选 session。不得保留“漏传参数就独立 commit”的双重合同。

## 结构建议

| 层 | 责任与允许的依赖 | 禁止或需要解释的行为 |
| --- | --- | --- |
| `app/engine.py` 和 lifespan | engine/session factory 的唯一应用入口；创建、关闭、dispose；明确同步工具与异步运行时资源 | 新建第二份全局 engine/settings 权威、导入时连接数据库 |
| 应用用例 | 打开数据库作用域、组合 repositories、声明原子提交范围、处理外部副作用顺序 | 在 HTTP/Peer/Tool 中复制同一流程，跨网络等待保持事务 |
| UoW | 把本用例需要的 repositories 绑定到同一个 session；复用 SQLAlchemy 原生 begin/commit/rollback 语义 | 全项目 service locator、公开 raw session、多个并行 task 共享实例 |
| 持久化适配器 | 查询、锁、映射、批量写、必要的 flush/refresh；构造时接收必填 session | 自建 session、自行 commit/rollback、可选 session |
| 领域／Resolver／协议处理 | 纯规则、解析及窄查询／命令能力；身份规则由其语义 owner 定义 | SQLAlchemy session 逐层传递、隐式 lazy load、创建事务 |

Repository 按责任聚合，不能为每张表机械生成 CRUD 套壳。Graph 是合理起点；Source reconciliation 必须可在同一用例中组合 graph、blob、Source state。不能用“一类 repository 一次 transaction”拆断现有原子性。也不需要为每个用例创建一个新 UoW 类；只有不同能力集合或不变量有实际收益时才拆分。

SQLModel 当前同时承担 persistence model 与 transport schema。第一轮不为消除所有 SQLModel import 而复制整套 DTO。要消除的是 session 生命周期泄漏和隐式 I/O：作用域退出前读取所需值；结果使用已加载值或现有 schema 投影；不把 session-bound mutable object 传给并发任务。`expire_on_commit=False` 降低提交后隐式加载，但不是结果独立性和并发安全的证明。

## 需要保持的具体事务

| 用例 | 当前证据／建议事务范围 | 迁移不变量 |
| --- | --- | --- |
| flat `submit_graph` | 一次 graph command 中先 batch Blocks，再映射 local IDs，再 batch Relations | 不去重；正 ID 引用由数据库验证；失败时本次命令整体回滚；结果顺序与局部 ID 映射不变 |
| Stars reconciliation | 根据 Resolver exact identity 查找／重用，逐级形成关系 | 不能直接替换成 flat blind insert；默认 resolver+content 与 GitHub node_id 规则不同 |
| Source reconciliation | 外部 snapshot 先获得，再短事务写 graph／附件／Source state | Source cursor/checkpoint 不能先于对应内容提交；保留 source lock 与各协议 partial effects |
| RSS derivation | 先读，释放 session，HTTP／解析，再锁 subject 并复查后写 | 已有 read→external→locked-write 结构应保留；async 化不放大事务 |
| Cron occurrence | 锁 Cron → 验证 occurrence → 创建 Job → 更新 Cron progress → 提交 | Job 与 occurrence 同事务；保留 skip-locked、数据库时间和 last-job 判定 |
| Job | claim 短事务 → 无数据库事务的 handler 执行 → close 短事务 | 原子 claim、abort/timeout/close 的条件更新、停机 drain；不承诺外部副作用回滚 |
| 检索 records | 读取候选 → 释放事务 → Resolver/AI projection → 短事务批量 upsert | 不把 provider 调用包进事务；保留 timestamp freshness、cutoff 与重建语义 |
| Extension 配置／状态 | 窄应用操作内部锁行、运行纯 transform、提交 | transform 不 await 外部 I/O；配置和状态需共同变更时维持一事务；enabled RPC 和生命周期补偿不变 |

取消行为需要单独验证：async 引入了新的取消点。普通用例取消后 rollback/close；Job 取消后的 terminal-state 收尾需要有限时、受保护的执行边界。不能简单把原先同步 `_close()` 改成 await 后，默认它一定完成。也不能捕获数据库错误后在失败 session 上继续写；需要回滚或明确 savepoint 语义。

## 性能路径

Sir 明确不要求以全面性能测量作为迁移前置条件或完成门槛。先完成原生异步调用链和已确认的低效数据库操作改进；进一步调优留给实际问题驱动。预期 async 改善并发等待，但不在未经测量时声称所有请求延迟都下降。

`submit_graph` 复用 batch 能力消除逐项 flush/refresh；大批次可能由 SQLAlchemy 分页，不能宣称一次 flush 就一次网络往返。对 empty graph、仅关系、循环、自环、正负 ID 混用和中途 FK 错误保持既有合同。

`flush + refresh` 按原因处理：INSERT 主键及 server defaults 优先使用 RETURNING；UPDATE 的数据库触发器时间戳需要核对映射及返回路径，不能全仓删除 refresh。Relation endpoints 可用一次 IN 查询读取。Stars dedup、source identity、retrieval upsert 按具体语义分析，不把普通 batch insert 套到所有写入；不要求逐路径建立独立性能实验。

不在本次性能修复中发明全局 dedup unique key。当前查询后插入不自动具备并发幂等性；如果要提升保证，必须由对应身份语义 owner 明确范围，并另行评价 schema/lock 方案。

不提前增大连接池。迁移并存期必须核算同步池、异步池、日志池以及各进程的总连接预算；最终观察 checkout wait、transaction duration、query latency、pool saturation 再决定配置。不能把异常池等待简单转换成无界重试。

## 全量迁移的两个边界与一处既有隔离

### Extension Runtime 是独立交付依赖

锁定依赖为 `inkcre-extension-runtime-core-py 0.1.3`，由 ext-reg 发布。已读安装包 `base.py`：`update_config/get_state/mutate_state/mutate_config_and_state` 是同步调用 Core rich model 的接口；`get_config` 本身读取绑定 model 的内存字段，不能把所有配置读取一概当作 SQL。

Core `_ActiveExtensionModel` 与 `ExtensionStore` 也是同步接口。Runtime 的 lifecycle 还直接调用 Core 的 Peer/publication 能力。unsupported gap 是 runtime SDK 缺少可 await 的持久化接口及相应 lifecycle 协议，不是 psycopg 缺少异步驱动。不得在 Core 私自复制 SDK、在事件循环中阻塞等候协程或永久缓存 deployment state 来伪装兼容。

建议先在上游交付可兼容采用的 async capability，再迁移 Core 与内置／发布扩展，最后移除同步入口。准确的 capability 名称、版本范围、旧 wheel 拒绝或兼容窗口，需核对 ext-reg 的源码和发布政策后决定。Core Python import 合同的变化虽不一定改变 HTTP schema，仍是扩展作者可见的兼容变化。此处需要跨仓设计与交付，不意味着当前已获得跨仓源码修改或发布授权。

### 写入 PostgreSQL 的日志

这里仅指 `libs/obsrv/log_handler_postgresql.py`，不包括控制台日志或外部日志服务。配置 PostgreSQL backend 且 ENABLE_LOG_BACKEND 打开时，`emit()` 通过自己的 engine 创建同步 session，写入一条日志并提交。它属于数据库访问清单；若从 event loop 线程调用，会发生同步数据库等待。日志应有独立持久化作用域，不加入业务事务，也不与业务共享 session。

具体异步适配方式尚未确定。此前提出的队列／writer 是可选机制分析，不能直接升级成日志系统重构范围。先核对这个数据库 sink 的真实调用和资源生命周期，再选择满足边界与非阻塞目标的最小适配。

### Readiness 的数据库查询

这里指启动等待及 `/readyz` 中调用的 `check_database_readiness()`。它用 `app/database_contract/connection.py` 的同步 psycopg connection 查询 migration head、contract state、角色／权限及 catalog 等数据库合同，没有使用业务 ORM Session。当前 `run.py` 已用 `await asyncio.to_thread(check_database_readiness)` 整体执行，connection 在 worker 内创建和关闭，因此已隔离直接 event-loop 阻塞。

它仍列入数据库迁移清单，但不能把它误报为已确认的 loop blocking 缺陷。本任务只评价查询执行、连接／事务生命周期及性能，不重写健康检查的判断规则、响应合同和启动状态机。工具与运行时的适配方案待主线设计明确后决定，避免重复数据库验证逻辑。

## 实现与终止条件

[线性实现计划](plan.md) 是唯一执行顺序，包含前置条件、各步完成标准及调用链预演。本文件不保留第二套阶段列表。分步迁移不缩小最终范围；info_base 试点、async factory 或单条 endpoint 完成均不能关闭父任务。最终必须覆盖全部列入范围的运行时数据库路径，清除过渡入口，并交付长期治理。Benchmark 为条件合适时的可复用增强，不是完成门槛。

## 长期治理落实方案（要求已确认，具体机制待落实）

持久设计更新现有 `docs/30-unit-tdd/business-pipeline-and-authority.md`，runtime 资源、池预算、日志和排障更新 deployment 文档；跨仓 Python contract／能力演化回到 Hub 或 ext-reg owner。最近的 AGENTS 只保留反复发生的局部危险，不复制完整设计。没有 owner 理由时不新增另一份数据库架构说明。

机械约束应围绕能力边界，不检查方法名字：session/engine 构造只允许在声明的 infrastructure/tooling adapter；transaction framing 只在应用 UoW；仓储不 commit；业务及 Resolver 不接收 raw session；不再引入 Session|None。可先使用已有 Ruff 的 import restriction 和类型检查，只有其无法覆盖且实际存在的规则才增加轻量结构检查。任何临时 allowlist 必须精确到对象、说明 owner、消费者迁移状态和删除条件；不能把整个 business/extensions 目录永久豁免。

治理按四种证据分工：

| 载体 | 要持续维护的内容 | 完成证据 |
| --- | --- | --- |
| 权威设计文档 | 应用用例、UoW、repository 的职责；独立入口与事务内操作的组合规则；外部 I/O 与事务的关系 | 更新已有 owner 文档，能据此评审新增用例，不依赖本 task packet |
| 最近的开发指南 | 新增入口、repository 和跨库表用例时应遵守的局部规则；指向权威设计 | 移除旧 optional-session 指引的歧义，不复制另一套架构说明 |
| lint／类型／必要的结构检查 | session/factory 依赖位置、仓储事务控制、optional-session API 等可可靠判定的违规 | 接入现有 `pdm run check`；用小型违规样例确认确实失败，合法用法通过；不把文本匹配当作完整语义分析 |
| 真实数据库行为验证与评审 | 跨 repository 原子性、失败回滚、并发作用域和取消清理；外部工作期间的事务持有 | 少量有回归价值的行为验收与明确评审关注点；不以静态通过替代运行语义 |

迁移中的例外与最终保留的适配边界必须区分。临时例外在 packet 记录删除条件；最终例外必须有持久 owner、必要性及验证，并在关闭父任务前明确接受，不能通过宽泛 allowlist 自动转正。具体目录和类名尚未确定，规则应跟随职责边界，不提前用目录名固化尚未验证的结构。

静态约束不能证明调用链不阻塞，也不能单靠禁止 imports 证明 ORM 不泄漏。用真实 PostgreSQL 验证核心原子性和回归；围绕实际风险验证并发与取消后的正确性及资源释放。性能测量不扩展成另一套必跑验收矩阵。保留有实际回归价值的少量自动化，不新增 mock wiring 测试矩阵或全框架自测。

## 必要验收范围

- 图提交：IDs/defaults 与关系方向正确；FK 失败不残留本次 blocks/relations；调用方组合作用域无隐藏 commit。
- source/blob：内容、关系、存储与 checkpoint 的指定原子集合保持一致；外部 I/O 故障遵守原 owner partial effects。
- Job/Cron：确定性并发认领／occurrence、取消／超时收尾，不共享 session，不保持跨 handler 长事务。
- Resolver/storage：typed outcomes、hydration cache 与 exact identity 不变；完整 get_entities/invoke/materialize 路径不执行阻塞 DB。
- SDK/扩展：支持版本的 wheel 实际安装、启动、配置/state 变更与重启恢复；未支持版本明确拒绝或按已接受窗口兼容。
- 性能：不设置提升百分比或完整性能矩阵作为交付门槛。若建设 benchmark，按下节要求提供可复用的按需测量；无环境或比较条件不足时明确其限制，不阻塞主线。
- 生命周期：重复启动/停止、任务取消、连接异常后连接释放；若数据库日志适配引入后台写入，补充其资源与退出行为验证。
- 仓库：完整 `pdm run check`、相关真实集成/验收与无非预期 OpenAPI/schema 变化；运行时数据库清单及过渡项闭合。

## 可复用 benchmark（条件合适时建设）

Sir 鼓励在具备完整验证环境时，把性能评估做成可复用 benchmark，而非一次性复杂验证。此项不构成开始实施或部署的授权，也不作为数据库迁移的前置条件。优先评估现有 preview deployment；尚未确认本任务可用 preview、数据库规格或可比基线，不宣称已经具备测量环境。

建议最小范围只覆盖 Graph 提交与实体批量读取两类代表性 HTTP 操作，不调用外部 AI/采集服务。入口接收目标环境、数据规模及少量并发档位，生成并清理本次运行专属数据；报告版本、环境规格、工作负载、吞吐、p50/p95 和错误率。先复用现有工具与 runtime，不自研压测平台，不为 benchmark 增加完整监控系统。

如果比较旧版和新版，应使用同等规格、相同数据及负载、相同客户端位置和预热方式；记录实际部署版本。Preview 可以证明真实部署下的表现，但共享资源及网络波动意味着不能直接把差值全部归因于 async。没有可比旧版时仅报告当前结果。SQL 数、loop lag、pool wait 仅在已有采集能力或实际诊断需要时追加。

Benchmark 按需运行，保留使用说明和机器可读结果格式，不默认进入每个 PR 的耗时阈值门禁。其维护和运行成本明显超过收益时，允许暂不建设；必要的事务、异步调用及资源释放正确性验证仍须完成。

## 已核对的原生能力

SQLAlchemy 原生 async_sessionmaker.begin 已提供提交／回滚／关闭 framing，不自研事务管理器。psycopg dialect 支持同一 URL 的 async engine，无需新增 asyncpg；async session 不能跨 concurrent task 共享。参考 [Async ORM](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) 与 [psycopg dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg)。`run_sync` 只适用于受支持的同步 SQLAlchemy 调用桥接，不会使任意同步 SDK／网络调用自动非阻塞，不作为最终边界替代品。
