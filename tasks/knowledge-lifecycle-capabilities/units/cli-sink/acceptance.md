# CLI sink 验收设计

状态：2026-09-13 按 [D-601](../../decisions/D601-D610.md) 确认。接口基线已确认至 D-600；本页不表示技术预演、实施或验收已经完成，
也不授权 commit、push、发布或操作真实用户数据。当前阶段只由 [unit packet](packet.md) 维护。

## 要证明什么

验收对象是独立安装后的 inkcre-cli：调用者能从公开 help/schema 找到能力，经普通 Core REST 完成读取与管理，
并准确理解返回值、部分成果和后台执行。既有 retrieval/organization 的算法质量不是本轮重新优化的目标；
但接口不能丢失它们的有效内容或把错误执行描述成成功。

主路径是实际 CLI 进程 → 真实 HTTP → Core → 真实持久化/执行端。准备数据、对照外部内容和核查实际效果的
控制脚本可以使用已有设施；不能用 Manager 直调用替代某一步正在验收的 CLI 操作。脚本不安装成 CLI runtime，
不进入普通 CI 自动执行，不新增 test-only endpoint、Resolver、Source 或生产条件分支。

静态检查负责依赖、类型、schema、生成 OpenAPI、迁移完整性和构建。手工/脚本负责真实交互与状态效果。
不按 endpoint 数量建立自动化测试矩阵，不重复验证成熟库，不扩展泛化负路径或安全审计。

## 环境和材料

从 CLI wheel 在独立 Python 环境安装，工作目录移出 Core checkout；不给 CLI 配置数据库连接或安装 Core。
CLI 只配置 REST 地址与已确认的 JWT secret。离线 help、本机 connection 管理不依赖远端上线；正式运行使用
实际构建版本和明确的 preview/development runtime，不以 import 成功代替可用性。

连接旅程包含命名连接选择、connection check、peer get self/list，以及对已知 HTTP 入口的有界 wake。
分别记录已经 ready 的正常返回和一次平台实际冷启动；冷启动证据使用已配置的可休眠部署及平台日志，
不从过期 lease 猜测休眠，不为测试关闭用户机器或构建新的唤醒协议。具体可用实例在 preflight 核验。

主要读写旅程优先在隔离 preview 上执行；双进程执行、受控 Job 停止和真实 IMAP 服务可用本机声明的开发
设施。开发数据库遵循 AGENTS.local.md 的 SVC/远程 Docker 入口，不假定本机 Docker 或 Dovecot 可用。
预演必须确认具体拓扑和网络可达性，不能把 loopback 的测试服务直接写成云端 Core 可访问的地址。

材料选择以真实信息为主：已有 SQLite architecture 原文、Python asyncio 文档、Anthropic 的 Agent tools
文章，及既有 NASA 多模态材料。保留实际 URL/采集版本；不为命中某个词而编造全文或直接插入 lexical/embedding
records。图引用从真实写入回执取得，验收用的本地别名不进入产品模型、数据匹配或排序逻辑。

Collection 选择已有 Extension 的真实协议路径。优先复用 Mail 的真实 IMAP/Dovecot 验收设施，使用已有邮件
材料覆盖 ordinary/backfill 与 MIME 内容；这些是明确的验收邮件，不冒充用户真实通信。RSS 的公开 feed 可
补充不需账号的动态发现与采集路径，但不以 RSS 的重复快照代替 Mail backfill。无需为本 CLI 建新外部协议库。

既有 PostgreSQL binary / HTTP Storage 和媒体 Block 可由验收准备步骤建立，随后只通过 CLI 读取。准备所需
AI Provider、模型与 storage 不属于新增 CLI CRUD；不能因为准备材料方便而扩大产品范围。

## Journey 1 — 从线索取得可用信息

给当前 Agent 一个真实目标，例如“为后台任务取消接口整理参考依据”，仅通过安装包用法、help、动态 schema
和 CLI 实际输出完成信息取用。不规定工具调用顺序、不植入目标 Block ID、不规定最终摘要措辞或最少调用数。
当前 session 已参与设计，因此记录为实际使用轨迹，不声称是独立、无先验的盲测，也不另开 session 通信。

覆盖 lexical/semantic 独立及组合结果、实体记录、图邻域/路径/连通分量、Resolver 方法发现与调用。允许为
覆盖某个已批准命令另做小的脚本补充，不强迫 Agent 为一次问题执行所有命令。检查它是否能使用引用继续
获取证据，是否因为名称、schema、输出遗漏而猜测参数或不得不读源码；发现缺陷时修接口，不只加提示词。

同一 storage-backed Block 对照 raw pointer、hydrated bytes、Resolver solved result。使用既有
get_raw_content 的纯 bytes 返回与 ImageSolvedContent 的嵌套 bytes，验证原生二进制及 multipart 传输后
文件可读取、内容与原材料一致。超长正文与 graph 输出应可继续读取完整文件；JSON 保持紧凑完整，导出目录
整体移动后，入口 JSON 生成的相对文件引用仍可使用。不新增读取会话，也不重复调用 Resolver 取得后一段。

## Journey 2 — 配置来源并真正收集

通过 CLI 安装一个实际发布的 Extension、读取/修改配置、启用到指定 Peer，发现其 Source type/schema，
创建和编辑 Source。使用 ordinary collect 与有明确范围的 backfill 创建 Jobs，观察完成后经 CLI 获取收集
所得 graph 和 Resolver 内容。检查创建 Source 本身没有偷偷启动 collection。

再创建 collection Cron，修改模板、启用，观察一次真实到期派发；disable 后也能显式 cron run，并能观察
那次独立 Job。使用与运行窗口匹配的短 schedule，只等待一个自然 occurrence，不设置测试专用调度时钟或
把 run_now 当作 scheduler 的证明。具体时区和窗口在 preflight 固定。

使用两个 core-py 进程共享同一数据库：REST 接入 A，目标 Extension 在 B 启用。A 从未加载该 Extension 的
Source class，仍能根据持久目录保存 Source 和受理 Job；B 执行。不能通过“在 A 中先加载再 disable”假装
移除了其单调注册的类型。CLI 不查执行端数据库、不使用 Peer inbound；指定 Extension 启用目标的普通 REST
委托路径在这里一并覆盖。

结束时通过 CLI 删除本次 Cron、Source，禁用并卸载本次安装的 Extension；验证已经收集的信息仍能以基础
记录读取。不要求已卸载的实现继续提供 Resolver 能力，也不把暂存类型的进程行为当作永久可用性保证。
若复用已有 Extension，不卸载别人的安装，改用隔离部署完成完整生命周期。

## Journey 3 — 配置整理并保留执行控制

经 ai models、agent tools 与 config schemas 找到实际合同，创建/修改一份 Agent definition，通过 deployment
config 选择它。对测试材料发起 organization ruminate，得到 Job 后用限时 wait 观察，再继续同一 Job。
至少完成一次实际 Agent 调用及其可观察执行结果；图无变化可能是正常结果，不规定 LLM 必须写某种关系。
如果有写入，核查其确由本次输入/配置产生，不以 Job finished 宣称语义质量已全部通过。

为 Organization 配置 Cron 并从其模板派发，确认参数能被实际 owner 消费。Cron 的自然调度已在 Journey 2
验证，这里无需为每个 behavior 重跑一个调度矩阵。definition/config 的更新与清理均通过 CLI；共享 behavior
config 若预先存在则恢复原值，不把清理写成删除整个 deployment 配置。

Job 控制分别观察 pending 停止、running 请求与终态、重复停止，以及观察预算结束后 Job 继续运行。用真实
可合作取消的工作取得 running 窗口；请求受理不是终止证据，必须看到执行端结束工作后的结果。若工作先
自然完成，记录实际结果，不能声称该次证明了 running 取消。停止不回滚已产生的 graph，不等待外部副作用
被撤回；不增加新的回滚、重领或 retry。接入 A/执行 B 的链路必须覆盖一次真实停止。

client-web 的 worker 与 AbortSignal 配套修正单独用真实浏览器、真实数据库和公开注册入口做有限脚本验证。
当前仓库只发现通用 Source handlers，未发现实际 SourceImplementation 注册，不能声称现成 Mail/Twitter
collect 可用于浏览器验收。若仍没有可用业务执行体，可在外部验收脚本通过公开 Job handler 注册接口提供
最小的可取消异步执行体，只检查实际 worker 收到数据库停止意图并传递 AbortSignal；不修改产品代码，不把
这个组件边界证据冒充完整浏览器 collection journey，不为验收新增产品 Source。

## Journey 4 — 修改信息并进行可靠的脚本组合

用 GraphForm 通过 CLI 创建一组互相关联的 Blocks/Relations；记录实际 ID，随后原地编辑 Block 和 Relation、
重新读取、逐项删除。只提交要改变的字段；尤其验证修改 Block.content 没有把省略的 storage 清空。这里的
图用于验证 producer/record 合同，不要求 retrieval 返回某条偶然选中的同长最短路径。

清单使用小 limit 跨页读取，覆盖持久清单、动态目录与已有图邻域。JSON 自带下一页位置；默认可读也不隐藏
它。再读取一个含长字段的对象，确认分页没有代替正文完整交付。schema 的精确选择不能因为目录分页而找不到
实际存在的方法；可信 REST 返回不被 CLI 自己的模型丢字段或再次拒绝。

在一个显式 ID 批次中包含实际存在的对象与确定不存在的引用，检查逐项成功/错误同时保留、stdout 可消费，
整体退出码反映部分失败。另用一个可定位的输入错误检查诊断指向用户提交的 JSON 位置。这些是已确认公共
合同的最小压力，不扩为所有输入或所有 endpoint 的负路径矩阵。CLI 中断 wait 不替调用者发送 abort。

同类校验边界修正用写入/读回/实际使用闭环检查嵌套 Mail config、Agent/AI 类型与动态配置。代码评审逐项
确认验证仍留在输入边界、类型转换未丢失，不为证明“validator 没运行”加入 mock 计数或旁路数据库坏数据。

## 静态与交付完成条件

Core 使用既有 pdm run check、生成合同和 migration 检查；CLI 使用独立 PDM project 的 lock、lint、typecheck、
wheel/sdist 构建，client-web 使用其声明的相关检查。仅变更适用的 gate，不复制 helper/schema 自动化测试。
release 准备在隔离副本中演练，确认 CLI 独立 version/changelog，Core/Extension 未被无关提升。

候选版本的 preview 必须正常初始化数据库并可用。CLI 的真实 REST 旅程不是只对 mock 或本机 ASGI client
通过；已有 MCP/Peer inbound 选择实际 consumer 做小范围回归，不重新验收 ChatGPT 全链路或 UI 全部功能。

按 D-599，首次交付先使 Core 新 REST 在生产可用，再发布 CLI 0.1.0；PyPI 首发成功后，在另一个干净环境
通过 pip 安装该正式版本，重复连接、信息读取和一个有真实结果的管理/Job 操作。精确版本、source SHA、
发布 run 和实际环境进入证据。正式包尚未可安装或 Core deployment 失败时，不关闭本 unit。

验收材料放在本 unit 的 acceptance/ 下，脚本按需产生，不预建测试框架；大型运行产物放 ignored 目录。
保留请求/响应、stdout/stderr、退出码、必要执行日志、实际图引用和清理结果。只清理本次创建并核验过的
资源；不 reset 共享数据库，不批量删除已有业务图。操作预览/发布仍需相应授权，设计确认不替代它。

## 实施前准备的状态

2026-09-14 上述准备已完成，证据见 [preflight](preflight.md)，下一步等待实施授权。原先重点是：共享 Extension runtime 的真实源码 owner
与发布顺序；两端 Job 取消和子任务清理；嵌套持久表示的无重复校验转换；独立 CLI 依赖与 multipart 实际链路；
真实 Extension 版本、IMAP/双 Peer 环境、AI 配置、HTTP 冷启动与 PyPI publisher 权限。不能把这些留到实施
时才第一次调查，或在未具备环境时将旅程标记通过。已有单次 bytes 实验只作为局部依据，不替代本页验收。

材料依据：[SQLite architecture](https://www.sqlite.org/arch.html)、
[Python asyncio tasks](https://docs.python.org/3.12/library/asyncio-task.html)、
[Anthropic Agent tools](https://www.anthropic.com/engineering/writing-tools-for-agents)。前者已有本仓库原文副本，
其它材料于本轮核对公开页面；实际采集版本仍随运行记录。行为边界依据组织 TESTING.md 与本 task decisions，
不能因为其它 unit 留有 automated acceptance 就推定可以增加本轮自动化。
