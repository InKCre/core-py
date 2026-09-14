# CLI 实施记录

2026-09-14，Sir 在 a953676 完整 preflight/Impact Handshake 后明确授权开始。源码修改与验证在此授权内；
当时不自动授权新的提交、push、PR、合并或发布，也不进行跨 session 通信。
2026-09-14 Sir 后续明确授权提交、推送和创建 PR，禁止合并；当前交付状态由 [delivery.md](delivery.md) 记录。

## 工作位置

- Core：root worktree / feat/inkcre-cli，基线 main b3ccb00，加设计提交 a953676。
- ext-reg：../.worktrees/cli-sink-ext-reg / feat/cli-sink-runtime，基线 3fc4523。
- client-web：../.worktrees/cli-sink-client-web / feat/cli-sink-job-control，基线 54882ac。
- Hub：../.worktrees/cli-sink-docs / feat/cli-sink-contract，基线 528d735。

源码仓库 origin/main 在开始时重新 fetch，未漂移。旧 checkout、前一单元收尾与未跟踪 skill 保留不动。

## 进展

P1 源码与本地验证完成：ConfigContract、DeploymentConfig、Extension runtime 及其直接 typed 消费者。
ext-reg 按既有 Changie 工作流已在本地准备 runtime 0.1.3，静态检查、原生 bindings 检查和 wheel/sdist 构建通过。
尚未发布，Core 仍 pin 正式 0.1.2；候选 runtime 只进入隔离 Docker image，不覆盖根环境的 site-packages。

P2 已接入 Core/client-web 的停止意图观察、执行句柄、清理后关闭和 shutdown 顺序。Mail 持有同一次阻塞
调用直到结束，再释放锁/断连；新增 explicit rumination Job。候选 migration 为 d41cc84db0c5，只添加
jobs.abort_requested，已通过 migration integrity 检查。生成候选时发现既有 Mako 模板的两空格缩进与
Alembic 原生四空格片段冲突，已修正模板及未发布候选；未修改已发布 revision、未升级共享开发库。
双 Core 和真实浏览器 worker 的停止验收均已通过。client-web 数据库类型从隔离候选数据库生成；除新列外，
也自然补齐前一 MCP migration 的 sinks/sink_types，未手改生成物。真实 PostgreSQL 暴露 pending abort 的
CASE enum/VARCHAR 不兼容，已在条件写中显式使用现有列的 enum 类型，原地修复后通过重跑。

P3 已接入并实际执行：Source/Cron/Agent 管理、AI/profile 发现、Job REST、deployment config 目录与 schema keys，
以及实体、Resolver、graph、recall、Peer 和 Extension 普通 REST。OpenAPI 已从实际 router 生成。
新提交的嵌套 Source 参数由 Source handler 复用 catalog 校验；app/validation.py 只补原生错误路径，
不重复校验。普通管理 GET 不加载业务 schema。明确记录写入的 FK/CHECK 冲突在 route 映射为 409，
不预查引用、不复制数据库约束。既有 MCP SDK 和指定 Peer 的检索路径均已回归。

P4 的独立 CLI project、完整命令组、动态 schema 和文件交付已实现，独立 lock/lint/typecheck
通过。有界观察使用很小的 asyncio.timeout + HTTPX AsyncClient 作用域，确保整个预算包含慢请求；其它请求
保持同步 HTTPX。没有留下 to_thread 请求或新增异步 CLI framework。wheel 在 checkout 外的干净 consumer
环境运行，不可导入 app/FastAPI/SQLAlchemy/PDM；本地四条旅程的具体证据见 [local-acceptance.md](local-acceptance.md)。

P5 发布脚本、CI 静态构建、Towncrier 独立 CLI project、文档已接入。另核实 aiohttp 已是 Core 直接运行依赖，早期草案将它称为传递依赖已过时；不重复
新增依赖。Root gate 明确排除独立 cli/ 与非产品 .agents/，CLI 使用自己的静态配置。
真实 release prepare 在隔离文件副本中只修改 CLI，从 0.0.0 准备到 0.1.0，实际 index 不变。
production Extension publisher 现在复用 Toolkit finalize；七个候选 wheel 的本地构建/finalize/校验通过。

P6 本地候选验证完成，尚未完成交付验收。Core `pdm run check` 为 14 passed / 53 skipped；跳过的 opt-in
数据库套件不声称执行。CLI/ext-reg 静态检查与构建、client-web core 和 app 类型检查与构建均通过。
未增加自动化测试，仅修正一处既有测试 mock，使其符合实际 typed 返回合同。

本次独立验收的八个容器、数据库卷与网络已删除，共享 Core readyz 保持 200。命令与文件证据保留在 ignored
目录。Pydantic 指南已进入本 Spoke 的 business-pipeline-and-authority，并由 app/schemas/AGENTS.md 引用；
原有未跟踪的 python-backend-code skill 未整份混入本 unit 交付。

## 后续交付顺序

1. 按已获授权提交 ext-reg runtime 0.1.3 并创建 PR；等待 Sir 合并和原生发布，再更新 Core dependency pin/lock。
2. Hub 的 Job/校验合同单独发布，再做 Spoke shared-ref bump。Spoke REST/CLI/Job 变更不与 ref bump 混提交。
3. Core/client-web 候选 PR/Preview 跑交付回归；Mail 下一正式版本需实际 Registry 安装/启用。
4. Core 新 REST 与两端 worker 交付后，Release PR 准备 CLI 0.1.0；配置 PyPI Trusted Publisher 并正式发布。
5. 在 checkout 外从正式 PyPI 安装复跑，补真实平台冷启动证据，随后才关闭 unit。

CLI 不是完整 Peer；这些步骤不新增 CLI 数据库访问、内部 runtime 替身或发布版本绕过。提交/PR 进度见
delivery.md；不能把本地通过或 PR 创建标为整个单元完成。
