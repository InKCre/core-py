# 数据库异步 I/O 与事务边界

## 目标与授权

Sir 已授权全量数据库迁移及长期治理，并允许本任务自由提交、推送、创建 PR 和修改 ext-reg；此前禁止合并 PR；2026-09-18 单独批准合并 ext-reg #38，Core #105 仍不得合并。正式 SDK release 依赖上游 main 的既有自动流程，不能通过从任务分支发布绕过该边界。

分支 `refactor/async-database-boundaries` 从 fetch 后 `origin/main`（`66ce59f`）建立，目录 `/Volumes/WorkSSD/Development/InKCre/.worktrees/core-py-async-database`。原 checkout 的其他任务修改未动。

## 范围澄清

Sir 明确先只涉及数据库相关工作。两条主线是：（1）database session 生命周期及事务边界；（2）数据库操作异步化与性能优化。全量运行时范围及长期治理意向保留，但不据此扩展为日志系统、健康检查机制或通用异步框架重构。日志和 readiness 仅其数据库访问部分列入清单；不把是否允许同步适配器作为当前需要 Human 先回答的前置问题。

## 当前认识

45 个运行时 Python 文件直接引用 SessionLocal／SQLModel Session；163 个 SessionLocal(...) 文本匹配含工厂定义及 dependency 内部调用，88 个 commit(...) 文本匹配。该统计只是查找基线，未覆盖注入 factory 与直接 psycopg 等所有路径，不能当作完整调用图。

已确认 graph 逐项 flush/refresh、async Resolver/Storage/Job/检索路径同步 SQL、optional-session 双事务语义。还找到独立 PostgreSQL 日志 engine、已通过 worker 隔离的 readiness，以及 SDK `0.1.3` 的同步 state/config 持久化接口；全量目标需要覆盖这些边界。

Sir 已确认“短数据库工作作用域 + 用例事务 + session-bound repository”的边界方案；不把整个 request/job 绑定成一个长事务。保持 graph signed-ID、exact identity、source checkpoint、Job/Cron 原子性与外部 partial effects。SQLModel 本身不作为消灭目标。

## 设计与下一步

设计阶段已关闭。[设计基线](design.md) 记录已确认原则；[线性实现计划与预演](plan.md) 唯一维护 01 → 11 的执行顺序。[迁移清单](inventory.md) 记录已迁移路径、过渡消费者和 SDK 证据。

步骤 01–04 的当前范围已实现并验证：Graph async 基础、配置／AI／Agent／Peer，以及 info_base HTTP／Resolver／Storage 的新路径。旧同步 CRUD、Stars 和 Storage caller-session API 仍供后续 Source／扩展／检索／organization 消费；它们不是完成状态，整体任务不得关闭或发布。

上游 SDK PR 为 https://github.com/InKCre/ext-reg/pull/38（实现提交 `5fc4ad7`）。当前步骤 05 已获跨仓授权，在 ext-reg 的 `feat/runtime-async-persistence` worktree 实现 Runtime SDK 0.1.4 additive async capability。发现 publication 内 Source catalog 同样需要 async capability；已纳入 SDK 改动，Core 采用时先提供对应 catalog adapter，不等待步骤 06 才修补调用链。

ext-reg #38 已按新授权 squash 合并为 `09b6c84cc197bd7b92c959887d9b546ebec49eda`，
正式发布 run 为 https://github.com/InKCre/ext-reg/actions/runs/35357534102。
发布已成功，正式 runtime-core-py-v0.1.4 wheel/sdist 均指向上述 main SHA，
artifact 阻塞已解除；Core 已采用正式 0.1.4，并实现步骤 05 的 Host/Store/active model 异步调用链。
SDK 的独立 packet 仅拥有此上游 slice 的实现证据，父任务顺序仍由本计划拥有。

Sir 对已迁移切片的复核发现两项实际结构问题：repository 混入 business，entities route
直接访问 UoW 内的 repository。已迁移到 app/persistence，并由 business 的
get_entity_records 拥有批量查询作用域。Ruff 根配置目前不属于实际 monolith，但提前将
数据库规则和迁移覆盖清单移入 ruff.database.toml，避免继续扩大逐文件命令和根配置。
这些是步骤 05 前对 02–04 的纠偏，不是新的并行计划或全量迁移完成声明。

Core 步骤 01–04 已提交为 `282f110` 并推送，draft PR 为 https://github.com/InKCre/core-py/pull/105，清楚标注整体未完成。后续长期治理与旧 API 删除属于步骤 10，目前 import lint 只约束已迁移范围。

## 验证与环境状态

Sir 要求避免过度验证：全面性能测量不作为迁移前置条件或完成门槛，后续优化由实际问题驱动。保留事务正确性、完整异步调用和资源释放所需的适度验证。若现有 preview 等完整环境与工具适合，鼓励建设可复用、按需运行的 benchmark；优先 Graph 提交和批量读取，报告吞吐、延迟与错误率，不默认加入性能 CI 门禁。现已授权创建 PR；其既有 preview workflow 可能自动运行，不等于授权生产发布。

设计阶段证据来自最新 main 源码、安装的 SDK 0.1.3、SQLAlchemy 官方文档与组织治理政策；实现验证见本 packet 的逐步状态；尚无性能测量结论。

此前已启动新 worktree 的 `svc dev ensure database`，用于隔离 PostgreSQL 基线准备；其 provider 是原机器声明的 SSH Docker，实例 `cdf5b0ff179b59f1`。实现前已定位为 SSH control socket 路径过长，用本实例专属短路径恢复转发；数据库 readiness 为 ok。未执行 reset/删除数据库命令。后续状态应检查此实例，不使用其他工作区数据库。只读共享文档已初始化到仓库固定 submodule ref，未修改 Hub 内容或引用。

## 本阶段验证结果（2026-09-17）

- `pdm run check` 通过：foundation、lock/migration integrity、format、lint、数据库 import 边界、typecheck；默认测试 14 passed / 58 skipped（需要显式数据库或外部环境的 suites 未在默认 gate 执行）。
- 使用本任务隔离 PostgreSQL，Graph、DeploymentConfig、AI、Agent、Peer 五个集成文件共 13 passed。包含 flat graph ID 映射、失败／取消回滚、Stars／GitHub 精确身份、blob/graph 原子性、hydration 与 HTTP CRUD。
- OpenAPI 重新生成后无 diff；仅原有 dict default schema warning。`git diff --check` 通过。
- Config 的旧测试断言与 main 现有合同不一致（PUT 新建 201、DELETE 204、raw read 不依赖已加载 schema）；本轮按原 route 实现修正断言，没有据此改变 HTTP 合同。
- 本阶段未做性能 benchmark、preview 部署或 SDK/wheel 发布。默认 suite 的 skips 和以上局部集成通过都不代表剩余 runtime 已迁移。

## PR 检查反馈

SDK PR #38 在 `887232a` 的完整 Registry CI 与 dependency review 已通过。Core PR 的 release-intent
检查指出 Core/GitHub fragments 缺失，已在 `830ea06` 补齐并本地通过 base-aware release check。

Portable runtime 验收暴露异步启动竞态：/livez 已 200、/readyz 暂为 503，随后日志显示 bootstrap
完成。旧脚本只等待 liveness 后立即断言 readiness；现改为对 readiness 使用 30 秒的有界 retry，
保持原有 readyz 响应和应用启动合同，不改成 liveness 即 ready。CI 使用真实镜像与 PostgreSQL 验证。


## 2026-09-18 复核修正验证

`pdm run check` 通过（14 passed、58 skipped）；本任务隔离 PostgreSQL 上五个既有集成文件
13 passed；OpenAPI 无差异。Ruff 的 `--show-files` 确认独立配置仍覆盖全部八个原有目标，
没有因目录迁移丢失检查范围。repository/UoW 为迁移文件和 import 更新，SQL 与事务 framing
没有改写；entities 的两类批量查询仍在一个 scope 内完成，hydration 在其外。


## 步骤 05 的采用与验收（2026-09-18）

Core 锁定正式 SDK 0.1.4 wheel，hash 与 main release asset 一致。ExtensionStateService 拥有短事务
和配置／状态规则，app/persistence/extension 拥有 session-bound SQL 与工厂。Host/route 全部 await，
Registry origin 的数据库读取结束后才进入 worker 执行既有 Registry HTTP 和 artifact 获取。
Source catalog 先提供 async batch upsert；完整 Source 用例仍属步骤 06。Twitter 的 state/config
消费者、启动前 reconciliation 和 Mail 默认配置读取已随接口适配，其他采集 SQL 仍属步骤 07。

已提前落实约定的 Host 0.2 窗口：app/version.py 为 0.2.0，七个 first-party producer 约束
>=0.2.0 <0.3.0，各自提供 breaking release intent；不直接修改 immutable release version。
旧 wheel 不会以放宽旧 metadata 的方式进入新 Host。正式 Core/Extension 发布仍须全量任务完成。

真实隔离 PostgreSQL 的 extension_probe.py 验证八个并发 state mutation 无丢失更新、
config/state transform 失败回滚、enabled RPC、启停路由、disable 持久化失败后的重启、
startup schema await 取消后 claim/route 清理和重新启用。另发现并修正 disable 的补偿范围：
RPC 已提交后的 Peer refresh 失败保持 disabled，不重启成与 durable intent 冲突的 runtime。

既有 SDK public callback 缺陷在实际采用阶段成为阻塞。ext-reg #39
https://github.com/InKCre/ext-reg/pull/39 已提交最小修复，完整 CI 通过，并用独立标准安装的
SDK 0.1.5 wheel 在 FastAPI 0.139.2 验证；源码 FastAPI 0.141.1 也通过。修复使用官方
iter_route_contexts，不遍历私有结构，维持 exact method/path 和 withdraw 语义。
Sir 已被请求单独授权合并 #39；此前授权仅限 #38。Core 仍采用正式 0.1.4，不用本地 wheel。
按唯一线性计划，必须待 0.1.5 正式交付、完成 callback 启用验收，才进入步骤 06。

本地完整 pdm check 通过（14 passed / 58 skipped），既有五个 PostgreSQL 文件 13 passed，
OpenAPI 无差异，release intent 检查通过。本轮没有宣称 #105 可合并。


## 步骤 05 完成与当前步骤（2026-09-18）

Sir 已授权合并 ext-reg PR，不再限于 #38；Core #105 仍只推进到可合并状态。
#39 已合并为 c7b529839e86cc3168c6c26ca991e4b476aa94a0，正式发布 run
35361700563 成功。Core 锁定 SDK 0.1.5，wheel hash
12d73c2757cc97a4137b6f326ee66ea6b289478f9d49e7a8244f736de124c71e 与 release 一致。
Host PostgreSQL probe 已加入真实公开 route 声明并通过启停、取消、重启。
步骤 05 的 artifact 阻塞解除，当前步骤为 06：Source → Sink → Job → Cron/scheduler。

### 步骤 06 验收进展

Source／Sink／Job／Cron 已采用异步 persistence。CronUnitOfWork 同时拥有 Job、Source 与 Cron repositories；
Job 创建和 occurrence 推进同事务。Job Handler 的 eligibility 接口及 Source／AI／Agent／Organization／
Semantic 的实际读取链一并 await；provider、handler、Sink lifecycle 均在短事务外执行。
隔离 PostgreSQL 的 job_probe.py 已通过并发 claim、取消收尾、八个并发 Cron occurrence 仅创建一个 Job、
Cron flush 后注入失败时 Job/occurrence 一起回滚。类型检查和数据库边界 lint 通过。

现有 RSS 测试的非法参数预期与当前 admission contract 不一致，改为验证提交拒绝；lexical 清理移除
并无必要的 RESTART IDENTITY，以现有 core runtime 权限执行，不扩大数据库权限。

步骤 06 已完成：完整 pdm run check 为 14 passed／58 skipped；隔离 PostgreSQL 的 lexical/RSS 五项验收全部通过，Job/Cron probe 通过。当前进入步骤 07，按 GitHub → RSS → Mail → Telegram → Twitter → Memos 迁移。

### 步骤 07 验收进展

GitHub、RSS、Mail 的 graph coordination 更名为 Reconciler，通过已绑定的 Core repositories 工作，
不再直接持有 Session；扩展应用入口决定 scope。Telegram 的 graph/update cursor 同事务，Twitter
修复先写 cursor 再提交 graph 的顺序，改为同一 SourceUnitOfWork，Job state 交回统一 close 持久化。
Memos 的 MemoGraph/AttachmentGraph 保留 graph grammar，用例通过必需的 GraphUnitOfWork 组合，
维持 primary delete 后独占资源 best-effort cleanup；异步并发归属检查使用有序附件行锁。

RSS 两项真实 PostgreSQL 验收、Mail graph/checkpoint probe、Telegram/Twitter checkpoint probe 已通过。
Memos 原有 13 项真实 PostgreSQL 验收通过，并补充单附件并发 owner 验证。本地缺 Dovecot distribution，
未把 Mail graph 验证冒充 IMAP 端到端验证；后续采用现有 Linux/preview 环境验证实际协议。

步骤 07 完成：全仓 gate 14 passed／59 skipped；Memos 13 项原有 PostgreSQL 验收与新增并发
附件归属案例通过，RSS 两项通过；GitHub snapshot/replay/list-removal/account-binding probe 通过，
Mail、Telegram/Twitter probes 通过。扩展 lint 覆盖除 GitHub legacy identity override 之外的全部
已迁移 producer，该 override 仅由旧 Stars 消费，随步骤 10 清零。当前进入步骤 08。

### 步骤 08 完成（2026-09-19）

Lexical／Semantic 的 SQL 已移入所属 persistence，维护按 batch upsert；Resolver／embedding
计算在事务外，原有 ranking、freshness 和 cutoff 保持。Graph navigation 的 HTTP、MCP、Agent
调用链原生 await；组织行为公开命令各自拥有事务，内部 helper 必需 GraphUnitOfWork。
媒体解释与 Rumination 的邻居改为批量查询；多实体 Tool 复用既有 get_entity_records。

隔离 PostgreSQL：Lexical 三项、Semantic 一项通过；Organization 原有五项与新增合成中途
写失败回滚一项通过。navigation_probe 验证方向、hop limit、cursor 和 endpoint closure。
全仓 gate 为 14 passed／60 skipped，lint、数据库边界、typecheck 全通过。
旧同步测试 setup 及少量旧业务兼容方法按步骤 10 清零；当前进入 09，不宣称 #105 可合并。

### 步骤 09 完成（2026-09-19）

PostgreSQL handler 不再自行建同步 engine/session；lifespan 启动单 writer，有界 1024 队列，
每批最多 100 条在独立 async transaction 写入，关闭最多五秒排空后再 dispose。
readiness 保留既有 worker 内独立 psycopg connection，CLI 与 HTTP 共用完整 contract 检查；
这是明确的隔离同步 adapter，不计作业务异步路径，也不宣称运行时零同步驱动。

查阅当前 APScheduler 实现确认 shutdown(wait=True) 不等待 async cleanup，因此复用现有
with_trace_id 包装跟踪调度回调，暂停 admission 后取消并等待，再关闭 Job/Sink/Extension。
runtime_probe 已用隔离 PostgreSQL 验证日志独立于业务回滚、线程 trace、调度取消收尾。
全仓 check 14 passed／60 skipped；PostgreSQL backend 下 import-only OpenAPI 成功且无差异。
当前进入步骤 10：迁移测试 setup、移除过渡 API、收敛长期治理和总体验收。
