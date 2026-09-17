# 数据库异步 I/O 与事务边界

## 目标与授权

Sir 倾向本任务完成全部运行时数据库调用迁移，并建立长期治理。Sir 已关闭设计阶段，本轮要求线性实现计划与预演，尚未授权进入源码实施；不得把 info_base 试点当作父任务完成。可以调查、隔离实验、编辑本 packet。未授权 commit、push、部署或跨仓源码修改。

分支 `refactor/async-database-boundaries` 从 fetch 后 `origin/main`（`66ce59f`）建立，目录 `/Volumes/WorkSSD/Development/InKCre/.worktrees/core-py-async-database`。原 checkout 的其他任务修改未动。曾提前修改的三处 batch 相关源码已经准确撤回，`git diff` 为空。

## 范围澄清

Sir 明确先只涉及数据库相关工作。两条主线是：（1）database session 生命周期及事务边界；（2）数据库操作异步化与性能优化。全量运行时范围及长期治理意向保留，但不据此扩展为日志系统、健康检查机制或通用异步框架重构。日志和 readiness 仅其数据库访问部分列入清单；不把是否允许同步适配器作为当前需要 Human 先回答的前置问题。

## 当前认识

45 个运行时 Python 文件直接引用 SessionLocal／SQLModel Session；163 个 SessionLocal(...) 文本匹配含工厂定义及 dependency 内部调用，88 个 commit(...) 文本匹配。该统计只是查找基线，未覆盖注入 factory 与直接 psycopg 等所有路径，不能当作完整调用图。

已确认 graph 逐项 flush/refresh、async Resolver/Storage/Job/检索路径同步 SQL、optional-session 双事务语义。还找到独立 PostgreSQL 日志 engine、已通过 worker 隔离的 readiness，以及 SDK `0.1.3` 的同步 state/config 持久化接口；全量目标需要覆盖这些边界。

Sir 已确认“短数据库工作作用域 + 用例事务 + session-bound repository”的边界方案；不把整个 request/job 绑定成一个长事务。保持 graph signed-ID、exact identity、source checkpoint、Job/Cron 原子性与外部 partial effects。SQLModel 本身不作为消灭目标。

## 设计与下一步

设计阶段已按 Sir 指示关闭。[设计基线](design.md) 记录已确认的 session／事务边界、数据库异步化和优化、长期治理及适度验证原则；[线性实现计划与预演](plan.md) 唯一维护 01 → 11 的执行顺序、前置条件与完成标准。本轮只编辑 packet，产品源码仍无差异。

静态预演已修正 AI 数据访问／Resolver、SDK／Host、Graph／Source 事务组合及旧工厂／tests/scripts 的顺序；它不是运行验证。下一步是按 Human 的实施指示从 01 开始，当前不自动进入源码修改。

已知实施前提包括 SDK 上游源码／可兼容 artifact 和支持 wheel 清单、隔离数据库可用性；日志/readiness 仅落实数据库适配，preview benchmark 有条件建设。遇到需要跨仓修改或发布的步骤，在真实交付屏障处理授权，不默认扩大本轮范围。

## 验证与环境状态

Sir 要求避免过度验证：全面性能测量不作为迁移前置条件或完成门槛，后续优化由实际问题驱动。保留事务正确性、完整异步调用和资源释放所需的适度验证。若现有 preview 等完整环境与工具适合，鼓励建设可复用、按需运行的 benchmark；优先 Graph 提交和批量读取，报告吞吐、延迟与错误率，不默认加入性能 CI 门禁。该鼓励不改变本轮仅计划与预演的授权状态。

设计阶段证据来自最新 main 源码、安装的 SDK 0.1.3、SQLAlchemy 官方文档与组织治理政策；尚无性能测量或实现验证结论。

此前已启动新 worktree 的 `svc dev ensure database`，用于隔离 PostgreSQL 基线准备；其 provider 是原机器声明的 SSH Docker，实例 `cdf5b0ff179b59f1`。启动命令已失败退出，最终 probe 报告缺少 runtime.json，未获得可用基线；设计阶段暂不进一步修复环境。未执行 reset/删除数据库命令。后续状态应检查此实例，不使用其他工作区数据库。只读共享文档已初始化到仓库固定 submodule ref，未修改 Hub 内容或引用。
