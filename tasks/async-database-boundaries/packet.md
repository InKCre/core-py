# 数据库异步 I/O 与事务边界

## 目标与授权

Sir 已授权全量数据库迁移及长期治理，并允许本任务自由提交、推送、创建 PR 和修改 ext-reg；明确禁止合并 PR。正式 SDK release 依赖上游 main 的既有自动流程，不能通过从任务分支发布绕过该边界。

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

当前步骤 05 已获跨仓授权，在 ext-reg 的 `feat/runtime-async-persistence` worktree 实现 Runtime SDK 0.1.4 additive async capability。发现 publication 内 Source catalog 同样需要 async capability；已纳入 SDK 改动，Core 采用时先提供对应 catalog adapter，不等待步骤 06 才修补调用链。

当前阻塞是实际 artifact 交付，而非提交／跨仓权限：ext-reg `.github/workflows/packages-release.yml` 只从 main 发布；Sir 禁止本 Agent 合并，所以完成上游 PR 后等待外部合并及正式 artifact。Core 仍锁定 0.1.3，不采用本地 wheel URL，不跳到 06。SDK 的独立 packet 仅拥有此上游 slice 的实现证据，父任务顺序仍由本计划拥有。

Core 步骤 01–04 将提交并创建 draft PR，清楚标注整体未完成。后续长期治理与旧 API 删除属于步骤 10，目前 import lint 只约束已迁移范围。

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
