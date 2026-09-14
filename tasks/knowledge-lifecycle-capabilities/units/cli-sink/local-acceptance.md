# CLI 本地候选验收

2026-09-14，源码基线 a953676 加本 unit 未提交修改。四条旅程使用已安装 wheel 的实际 CLI 进程，经真实 HTTP
进入 Core；准备数据允许使用数据库/协议控制工具，不用 Manager 调用替代正在验收的 CLI 操作。
本页不是 Preview、Registry 正式发行或 PyPI 通过声明，也不将这些脚本加入 CI。

## 环境与证据位置

CoreA、CoreB、PostgREST、PostgreSQL、Dovecot 和只读候选 Registry 位于远程 Docker 的独立网络
`inkcre-cli-acceptance-bylnlu_default`。全新数据库迁移至 d41cc84db0c5；共享 SVC 数据库保持原版本和状态。
Core A/B 的 Peer ID 分别为 `00000000-0000-4000-8000-000000000002` / `...0003`。
CLI wheel 0.0.0 安装在 `.runtime/cli-acceptance.bYlNlu/consumer`，执行 cwd 是 `/Volumes/WorkSSD`。
其中没有 Core、FastAPI、SQLAlchemy、PDM。runtime 修改以独立本地 wheel 注入候选 image；不是已发布依赖。

原始命令、退出码、完整 stdout/stderr、材料与导出文件保存在 ignored 的
`.runtime/cli-acceptance.bYlNlu/`。主要记录是 `records-evidence/`、`collection-evidence.json`、
`running-abort-evidence.json`、`media-ai-evidence.json`、`ai-remaining-evidence.json`、
`browser-worker.json`、`final-roundtrip-evidence.json`、`mcp-regression-evidence.json`。
脚本和临时材料不安装为产品，也不声明是独立盲测。

## 实际结果

| 旅程 | 已观察到的结果 |
| --- | --- |
| 信息取用 | 真实 Python asyncio、SQLite architecture、Anthropic Agent tools 原文入图；lexical / semantic / 两模式独立组合、实体记录、邻域续页、路径、分量和动态 Resolver 方法可用。超长正文保留完整文件，缺失实体保留其它成果并退出 1。 |
| 采集与调度 | CLI 安装并配置候选 Mail，仅 B 启用；A 创建 Source、普通/历史 Job 后由 B 真实 IMAP 执行。自然 Cron 与显式 run 均完成；图可继续导航至 Email，在 B 读取 solved 内容。删除 Source/Cron、禁用/卸载 Extension 后原 Email 与 Source anchor 仍可读。 |
| 整理与 AI 管理 | CLI 创建/编辑 Agent、选择 deployment config；实际 Qwen rumination 完成。实际 text-embedding-v4 生成 256 维，维护 Job 报告 embedded=15、failed=0、unavailable=19，semantic recall 返回结果。删除配置/Agent/Cron 后清理管理对象。 |
| 执行控制与安装 | pending Job 可原子停止；跨 Core running Mail Job 接受停止意图，等待真实 I/O 清理后 aborted。实际浏览器 JobManager 经 PostgREST claim，处理停止意图与 stopWorker 后均先清理再终结。CLI 自身不处理 Job。 |

最后补充执行 relation PATCH（包括反转端点）、Block/Relation DELETE、图第二页与普通 REST 指定 Peer 检索。
关系记录在这些普通 endpoint 一致使用 from_block_id/to_block_id；既有 Peer wire 没有随之改变。
使用真实 MCP SDK 对现有 MCP Sink 执行方法发现、open、read 成功，临时 Sink 随后禁用并删除。

### 材料与文件完整性

原文来源是 `https://docs.python.org/3.12/library/asyncio-task.html`、`https://www.sqlite.org/arch.html`、
`https://www.anthropic.com/engineering/writing-tools-for-agents`，保存的是运行时取得的完整 HTML。
引用取自创建回执；本地别名没有进入实现。

沿用既有 NASA 图片、音频和视频材料，经 PostgreSQL binary storage 读取。实际 bytes 大小分别为
53,569 / 2,741,982 / 3,670,265。raw pointer、hydrated bytes、Resolver 纯 bytes 与图片 solved 嵌套 bytes
之间的层次保持；导出目录搬移后相对文件引用仍有效。对应 SHA-256：

- 图片：`e244038ef1ffbbe4fc20170e0c3d69db850afeb6805c505fc0847befe2c6512c`
- 音频：`2a577394996b525f36946034d6cce9dcdb270c24851fc2078c5db810065f8c7f`
- 视频：`03168dd86fe492fed362cb64d5ce3d29989b8573cd9dfdaebfed0e11512f7427`

### 没有掩盖的执行结果

一个实际 rumination Job 已 finished；经 Cron 再次调用时耗尽 Agent 三次模型调用预算，Job 保留 failed
和原始原因。CLI 读取该记录退出 0，表示读取成功，不假装业务成功，也没有为通过验收反复调用模型。

第一次 running abort 在执行端下一次观察前恢复 IMAP，Job 自然 finished，同时保留 abort_requested=true。
这是已确认的 best-effort 竞争。第二次保留真实 I/O 阻塞窗口，观察停止意图后恢复服务，最终 aborted；
两个结果都保留。没有额外线程强杀、内部重试或回滚。

PostgreSQL 的实际 CASE enum/VARCHAR 不兼容曾使 pending abort 返回 500；已修复 SQL 表达式类型并重跑。
另有验收脚本误认 SubmitGraphResult 返回 relations、误认 backfill report 和 SDK 属性名等，均仅修脚本，
没有反过来改变产品合同。AI 准备阶段把 output modality 填成 embedding，改为实际 vector 后正常运行；
没有在产品新增别名或兜底。

## 静态与发布准备

- Core `pdm run check`：14 passed、53 skipped；静态检查零诊断。跳过的 opt-in 套件未执行。
- CLI 独立 lock、Ruff、Pyrefly、sdist/wheel 构建通过；不引入 Core/path/database dependency。
- client-web core 与 app 类型检查/构建通过；真实 Chromium worker 脚本通过。构建保留既有依赖注解、动态
  import 与 chunk 大小警告，没有为压制警告改业务。
- ext-reg runtime 的 Ruff、Pyright、原生 bindings 检查与构建通过，Changie 本地准备 0.1.3，未发布。
- OpenAPI 从 import-only 入口生成，使用无效端口的占位数据库 URL，未连接数据库。既有 default=dict
  metadata 产生一条 Pydantic schema warning；生成成功，本轮不扩成全 schema 重写。
- CLI release prepare 在隔离副本中将 0.0.0 变为 0.1.0，仅修改 CLI 路径，真实 Git index 不变。
- 七个 Extension 候选 wheel 用成熟 Toolkit finalize 并验证。正式 Mail 0.2.0 的既有 artifact 未覆盖。

## 未完成的关闭条件

runtime 正式发布与 Core pin、Hub-first/ref bump、Core/client-web PR/Preview、正式 Mail 新版本安装、
Core production 接口交付、CLI Release PR / PyPI 发布和安装复跑仍未执行。真实平台冷启动的前期证据
保留在 preflight-environment.md，尚未用正式 CLI 消费候选云端冷启动。

本地验收完成时暂停于提交/PR/发布授权及首次 PyPI Trusted Publisher 配置。Sir 随后已授权提交/推送/PR、
明确禁止合并；当前交付进度见 [delivery.md](delivery.md)，本页不提前声明线上通过。

## 清理

最终 A image 实际安装 runtime 0.1.3，并再次通过 MCP SDK 回归。隔离数据库最终有 18 个 Job：
12 finished、5 aborted、1 failed，没有 pending/running。临时 Source/Cron 已经经 CLI 删除。
按精确名称和本次 label 核对后，八个独立验收容器、独立 PostgreSQL volume、独立 network 已删除；
该测试数据库没有备份，不可恢复，其中临时借用的 Provider 配置也随卷删除。共享 readyz 清理前后均为 200。
两个本次 SSH 转发进程也已停止。SVC probe 的 ready/converged 均为 true，但 source_matches=false：共享实例
仍刻意保留 b3ccb00 / migration 143c4f4adc85，不等于当前 CLI 候选；没有为消除此提示升级或重置共享库。

最终镜像 ID、逐源码文件 SHA-256、wheel 哈希及清理结果保存在
`.runtime/cli-acceptance.bYlNlu/cleanup-evidence.json`；未导出数据库或 Provider secret。
命令证据、原文、媒体导出、脚本与本地 wheel 保留供 review，不清理仍在进行中的 parent task。
