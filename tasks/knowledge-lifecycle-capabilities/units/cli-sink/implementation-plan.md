# 实现计划

状态：2026-09-14，依据 D-571–D-603 和完整 preflight 收敛。产品、接口与验收已确认；
执行入口见 [Impact Handshake](impact-handshake.md)。本页本身不授权源码实施或发布。

## 依赖与改动 owner

```text
P0 基线与环境核验
 ├─ P1 持久表示与校验边界 → ext-reg runtime 发布 → Core dependency pin
 ├─ P2 Job 控制协议 → Core worker + client-web worker
 └─ P3 Core 普通 REST / schema / 内容传输
                          ↓
                  P4 独立 CLI 与命令
                          ↓
                  P5 文档与发布接合
                          ↓
                  P6 四条黑盒旅程与交付
```

P1、P2、P3 是可分别推进的代码责任面，不要求等待前一批全部完成才写下一批；它们在真实 REST 验收前
汇合。P4 的连接、输入输出骨架可以在 P3 的协议确定后推进。这里的并行仅描述依赖，不授权跨 session
通信或另启 Agent；当前由本 session 顺序实施与集成。

| Owner | 必要改动 | 不随之扩大的范围 |
| --- | --- | --- |
| core-py | 领域管理缺口、Job 协议、普通 REST、独立 cli/ 项目、发布编排 | CLI 不导入 Core；普通 REST 不变成 Peer protocol |
| ext-reg Python runtime | Extension config/state 的既有重复校验路径 | 不改 Extension 生命周期、注册、发布协议，不编辑安装包副本 |
| client-web packages/core | Job 记录与运行控制、对应参数读取路径 | 不新增管理 UI，也不承诺浏览器完整 collection |
| Hub | 经实现证据确认的共享边界与 Job 合同增量 | CLI 命令、具体 Extension 行为不提升为 Hub capability |

## P0：准备可执行基线

Core 已在 `feat/inkcre-cli` / `b3ccb00`，保留当前 task-control 和前一单元收尾记录。实施前重新核对 main，
不把其他单元的 dirty 文件纳入本次提交。ext-reg 本地 main 有独立提交且落后远端，client-web 本地 main
也落后；后续采用从已核验远端 main 建立的独立 feature 工作位置，不重置已有 checkout。

完整证据见 [preflight](preflight.md)：运行时源、两端取消链路、嵌套表示转换、独立 PDM、发布接合和实际
验收拓扑均有具体落点。正式实现先核对 main 是否漂移；不能用 preflight 代替代码/部署后的整体验收。

## P1：修正既有校验边界

以 [调用链清单](validation-boundary-correction.md) 和 [逐 owner 预演](preflight-call-sites.md) 为交付清单。主要落点是 `app/configuration.py`、
`app/business/deployment_config.py`，Source/Storage/Sink/AI/Peer 的 config 加载入口、`app/schemas/` 中实际
读回 codec，以及 first-party Extensions 对同一配置的直接加载。Job 的对应修改并入 P2。

先区分输入校验、持久表示转换、使用时能力检查；删除额外的重复业务检查，保留真正需要的转换。
已有 typed 值尽量直接传递；不以浅层 `model_construct` 替换所有读取，也不新建通用递归模型解码框架。
按 D-602，复杂类型恢复接受一次原生 Pydantic 构造及附带约束；普通读取和已有 typed 对象传递不重验。
不能以“读回可信”掩盖 SecretStr、嵌套模型或 discriminated union 的需要。

共享部分落在 ext-reg `runtimes/core-py/src/inkcre_extension_runtime_core_py/base.py` 及实际调用链。
runtime 的发行与 Core 的 dependency pin 分开交付；先验证本地候选，再按 owner 发布并更新 Core lock。
验收用真实 Mail 嵌套参数、Provider 配置及 Extension config/state 使用证明行为，不统计 validator 调用次数。

## P2：Job 停止与显式整理命令

在 `app/schemas/job.py` 和增量 migration 加入默认 false 的 `abort_requested`，同步实际受影响的 database
contract、生成 schema/DTO 与 client-web Job 表示；不引入执行 Peer 指针、取消队列或 Peer delegation capability。

`app/business/job.py` 集中持有本进程执行句柄并批量观察取消意图。pending 通过条件写关闭；running 先记录意图，
实际执行退出后才关闭；终态不回退。完成、超时和主动取消共用现有条件关闭边界，不能把 timeout 和 abort
都映射为同一原因。client-web `packages/core/src/job/manager.ts` 以 AbortController 实现相同协议。

检查 `run.py`/scheduler 的生命周期及 Agent turn、Source blocking adapter 的取消传播。只在实际 owner
补齐必要清理，不把 polling 注入每个 handler，也不承诺已经发出的外部操作可撤回。
[预演](preflight-runtime.md) 已复现 Mail adapter 在取消 to_thread 后锁提前释放的问题；预计修改
`extensions/mail/adapter.py` 的调用完成/清理顺序与网络超时，包含 Mail fragment，不只修改 Core JobManager。

在 Organization owning Job 模块添加已确认的 explicit rumination handler，复用
`RuminationBehaviorResolver.ruminate_local`；同步 builtin Job catalog，不把 Extension
类型塞进 builtin。Source ordinary/backfill 与 Cron 仍调用既有 Job 创建入口。

本批出口是双 Core 跨 Peer 请求停止和浏览器 worker 的真实闭合证据。旧 worker 不认识新字段，故两端更新
是完整交付的一部分；migration 可先落地，但单有新列不算取消能力通过。

## P3：Core 普通 REST 与必要领域接口

按依赖分成三组，复用既有 manager，不把 SQL、安装流程或 Job 业务塞进 routes。

1. 先补 `app/business/` 的管理缺口：Source CRUD/目录 schema、Cron 管理、Agent definition、config schema
   发现、Peer 查询与 Extension config PATCH。Source 类型未加载时仍可使用持久 catalog 接收合法输入；
   执行资格与保存成功分离。按设计保留各 owner 的事务，不构造通用表 CRUD 服务。
2. 接实体与使用：在 `app/routes/info_base.py` 及对应领域 router 提供批量 get、GraphForm POST、Block/Relation
   PATCH/DELETE、图查询、词法/语义查询和 Resolver 方法发现/调用。Block PATCH 使用真实 update form 的
   省略字段语义，不能继续由完整 BlockModel 的默认值清空 storage。Resolver reflection 复用
   `app/business/info_base/resolver/main.py`，不从 MCP Tool 反向调用领域能力。
3. 接控制面：Job/Cron、Source、Agent/AI/profile、config、Peer、Extension 的普通 REST。Job 创建先持久化并
   返回受理，best-effort 本地触发不阻塞响应。原有 client-web 消费的 Peer inbound 路径与 local execution seam
   保留；普通 REST 可选择领域 facade，而不是把两个协议的 handler 机械合并。

列表按 D-600 统一续读：自然标识 cursor、可选 limit、`next_cursor`，Job history 默认有限页；不为 bounded
path/components 查询虚构分页。错误保留 FastAPI/Pydantic 正常 detail，已确认批量操作保留逐项结果。

在 HTTP 边界实现一份 JSON / 原生 bytes / multipart 内容投影，使用 aiohttp MIME writer，不改 Resolver
返回值，也不创建内容缓存或下载会话。更新 `run.py` router 注册与 OpenAPI；动态 schema 仍归各领域 owner，
OpenAPI 不替代运行时 Extension 发现。确认新增路由没有覆盖已有精确或参数化路径。

## P4：独立 inkcre-cli

在 `cli/` 建独立 PDM project、lock、src-layout 与 `inkcre-cli` entry point。按 D-598 使用 Click、Pydantic、
同步 HTTPX、PyJWT；不依赖根项目环境来证明依赖完整。

先实现本机 connection、CLI 输入、单次调用的 CoreRESTClient、JSON/MIME 解码与结果/文件呈现，再接具体
命令组。共同选项使用普通 Click 组合；命令直接映射 REST，不为每个 endpoint 新增一层 forwarding service。
动态 `--schema` 来自实际 Core，offline help 不访问 Core。远端返回只转换，不建立响应验证模型。

命令覆盖以 [command-surface](command-surface.md) 和已确认 REST 页为清单，不能只完成 recall 后把管理命令
列为后续。先贯通 get/resolver/recall/graph，再接 Job 与 Source/Cron，最后汇合 Agent/config/AI/profile、
Extension、Peer；本机 connection 独立于远端 config。

Job wait 预算包含网络耗时，退出只结束本地观察；主动停止才发 abort 请求。compact JSON、stdout/stderr、
部分失败、文件输出和可选续读共用已确认呈现路径；不新增自动翻页、全局响应 envelope 或交互确认框。

## P5：文档、检查与发布接合

CLI 用法、安装和维护归 `cli/` 文档；Core REST 与 Job 的本地实现归现有 Unit TDD；共享原则经 owner 判定后
更新 Hub，再独立 bump Spoke ref。与实现一起更新，不等所有代码完成才补，也不在设计阶段提前改 durable truth。

依 [release-and-distribution](release-and-distribution.md) 修改 `scripts/release.py` 的显式项目发现、影响范围、
新项目 bootstrap 与 Release PR paths。CLI 加入同一个 Towncrier/`release/next`，但不进入 Extension matrix。
新增独立 CLI 检查和 main-only PyPI publisher，workflow 只组装既有 PDM 与仓库脚本，不承载长段业务逻辑。

预演发现 production Extension publisher 缺少 Preview 已有的 Toolkit wheel finalize，正式 Mail 0.2.0
因此不能被 runtime 启用。P5 将两条 build path 接到同一现成 finalization 步骤，并在发布工具环境提供
既有 Toolkit；不改 runtime 的 installed-record 合同，不覆盖旧包。本轮 Mail adapter 的既定 fragment
自然产生下一版本，正式验收需从 Registry 安装并启用该新版本。详情和候选验证见
[环境证据](preflight-environment.md)。此修正是 CLI Extension 管理旅程的真实前置，不扩展为 release framework 重写。

根 Core gate、CLI 独立 lint/type/lock/build 与 client-web 受影响 package gate 分别运行。核对根格式化/类型检查
和 Docker context 的边界，避免嵌套项目被误装进 Core。Feature PR 仅带各自 fragments，不提前 prepare 正式版本。

## P6：验收与 owner 分离交付

按 D-601 的 [四条旅程](acceptance.md) 执行手工或脚本黑盒验收；脚本复用既有语料与环境，不升级为自动化套件。
先完成 preview/隔离运行时的联合证据，再进入获授权的 PR/发布流程。共享 runtime 若发生修正，应先发布并由
Core pin；Core migration/REST 与 client-web worker 均交付后，才宣称完整控制能力可用。

CLI 正式 PyPI 发布前确认 Core production 已有新 REST；发布后在 checkout 外干净 pip 安装复跑读取与管理
关键路径。runtime、Core、client-web、CLI 都记录实际 SHA/version，不以某一个 green check 替代整体旅程。
不把多个项目发布做成原子事务；失败在实际 owner 修复并重跑，不引入跨项目回滚编排。

最后清理本轮明确创建的验收资源、记录剩余限制并整理 packet。只有这些交付证据齐备才关闭 unit；本页所列
提交、PR、发布均等待其各自明确授权，不能从验收方案获批推导现在可执行。
