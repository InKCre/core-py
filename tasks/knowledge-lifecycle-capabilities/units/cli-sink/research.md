# CLI 首轮研究与现状

2026-09-13。本文记录设计依据与候选方向，不拥有批准状态；当前阶段和复核面见 [unit packet](packet.md)。
读取了 parent 的 design-taste、collaboration 和 common-patterns/agent-tools。未联系其它 session。

## xiaoland/svc 的直接经验

读取本地 `/Volumes/WorkSSD/Development/svc`，origin 是 `https://github.com/xiaoland/svc.git`：

- `tasks/agent-friendly-protocol/research.md` 的 Approved Common Contract、Primary Research Evidence；
- `tasks/agent-friendly-protocol/lookup-review.md` 的默认输出、结构化输出和自足 help 设计；
- `tasks/agent-friendly-protocol/interface-topology-review.md` 的命令准入与职责分析；
- `USER_MANUAL.md`、`docs/product-tdd/agent-analysis.md`、`svc_cli/src/svc_cli/cli.py`；
- 实际运行 `svc status .`、`svc lookup --path index.md`、`svc analysis --help` 和 `svc analysis query --schema`。

最有价值的经验不是指定一种序列化格式，而是先决定信息选择，再决定呈现；两者共同受内容语义、Agent 的消费
方式和调用目的影响。Exact Markdown 读取可以直接返回 Markdown，可比较的候选需要保留完整引用，脚本计算
适合稳定 JSON，大内容需要可继续读取的位置。呈现影响调用者能否识别关系，不能当成装饰。

SVC 的普通命令把默认文本定位为 Agent/Human 的阅读界面，把 `--json` 定位为脚本/CI 的显式选择；analysis
query/read 则使用结构化请求与 JSON-first 返回。当前实现验证了按能力选择形式，而非所有命令共享一种包装。
其 CLI help 自足，不要求先加载 Corpus 或另装 Skill 才能理解命令；schema 按命令查询。命令树按用户意图、
不同结果与生命周期组织，表面整齐和顶层数量都不是目标。

这些是 SVC 场景中的经验，不照搬其 next-command 提示、exit code 表、schema version、无 Skill 选择或测试体系。
InKCre 已有的 Agent Tool 模式仍约束本任务，尤其不能为了引导而增加 `next_request` 或固定工具调用 SOP。

## 公开资料及证据限度

| 一手材料 | 可迁移的依据 | 限度 |
| --- | --- | --- |
| [GitHub CLI formatting](https://cli.github.com/manual/gh_help_formatting) | 普通文本与显式 JSON 共存；结构化结果可交给后续程序 | 不意味着 InKCre 要复制内嵌 jq 或模板引擎 |
| [GitHub CLI api](https://cli.github.com/manual/gh_api) | 领域命令之外仍可提供 HTTP 入口；`--input` 支持文件与 stdin，query 和 body 分开 | 不是把整个 REST API 自动展开为领域命令的证据 |
| [Justin Poehnelt：Rewrite Your CLI for AI Agents](https://justin.poehnelt.com/posts/rewrite-your-cli-for-ai-agents/) | 复杂输入保留 JSON 结构、运行时 schema 发现、控制返回体积 | 作者经验，不是所有 Agent 的对照实验；不引入其整套安全、Skill 和 dry-run 设计 |
| [Zbigniew Sobiecki：Building Agent-Friendly CLIs](https://zbigniew.me/writing/building-agent-friendly-clis/) | 可组合结果、真实 ID、stdout/stderr 分工、暴露截断，减少重复查询和猜测 | JSON 偏好与统一 envelope 是其选择；分页需服从具体 domain，不给所有 retrieval 强加分页 |
| [Reddit：Designing an agent-friendly CLI](https://www.reddit.com/r/AI_Agents/comments/1v2gjax/designing_an_agentfriendly_cli_what_am_i_missing/) | 实践者讨论 help、schema、文档与组合路径的使用困难 | 自报告与意见用于发现压力，不能当作标准或定量有效性证明 |
| [EACL 2026：How Good Are LLMs at Processing Tool Outputs?](https://aclanthology.org/2026.eacl-long.134/) | 对 15 个模型的研究表明复杂 JSON 的处理效果依赖内容、大小和推理任务 | 不证明简洁文本普遍优于 JSON，也不是 InKCre CLI 的验收结果 |

## 对本 unit 的候选推论

1. **能力发现有层次。** 根 help 帮助选领域，子命令 help 说明意图、输入、效果和结果；动态 Resolver 方法按需
   发现。合同来自运行中的能力 owner，不在 CLI 维护 Extension 方法清单。
2. **结构与阅读各得其所。** 原文保留自然文本；异构实体、引用和批次结果适合结构化形式。提供可脚本消费的
   稳定输出，但不因调用者是 Agent 就强制 JSON，也不因 stdout 非 TTY 就推断其只想读 JSON。
3. **嵌套输入不需要独创语法。** 简单选择用普通 argv；GraphForm 和 Resolver 参数保留 JSON，文件/stdin 避免
   层层 shell escaping。是否需要额外 input schema 查询由实际复杂度决定。
4. **有限输出仍应可取回完整内容。** 检索候选不冒充完整 Block；大文本/bytes 有明确读取或下载路径。保留领域
   原有的截断/未命中语义，不把一页、上限或未知状态写成“全部”。
5. **呈现不歪曲执行。** 非交互调用可完成，诊断与数据流区分；创建 Job 只确认已创建，完成状态从 Job 查询。
   失败保留有用原因，批次独立项按已有合同处理；不自动重试整批写入或制造 CLI 自己的业务完成状态。

评价这些推论要看真实 Agent 能否完成任务及如何恢复参数错误，不能以少几个字符、少一个命令或更多 schema
证明改进。命令名、模式、exit codes、认证和文件输出细节仍待产品范围明确后设计。

## core-py 当前 API 证据

基线 `b3ccb00ca2e235bfcc9b9f4f4cc17948c59ef54a`。实际检查了 `run.py` 的 router 组合与 `app/routes/*.py`，
没有依据 `docs/openapi.json` 推断已存在未挂载的业务能力。

| 能力 | 当前 REST 证据与缺口 |
| --- | --- |
| 词法、语义检索 | `app/routes/lexical_retrieval.py`、`semantic_retrieval.py` 已有 POST 入口；也是对应 Peer inbound 的物理承载 |
| Graph 导航 | `app/business/graph_navigation_retrieval/main.py` 已有领域能力，普通 REST 路由尚未挂载 neighborhood/find_path |
| 基础实体与写入 | `block.py` 有 recent/get/create/patch；`relation.py` 有 create/by_block；`info_base.py` 有 GraphForm 提交。不是完整对称 CRUD |
| Resolver 读取 | MCP `app/business/sink/mcp.py` 已实现读取和动态方法发现/调用；普通 REST 无等价完整入口，CLI 不能直接 import MCP runtime 来获得这些能力 |
| Source / Organization | `source.py` 创建 collect/backfill Job；`organization.py` 的 ruminate 是 Peer inbound，不是 CLI 的任务受理接口。其它已实现 Organization 行为需要按真实 owner 核对，不能以这个旧路由枚举全部能力 |
| Job | Core 有 Job domain；当前 router 组合没有通用 Job 查询路由，CLI 不能在创建后通过数据库自行轮询 |
| 管理 | `extension.py`、`sink.py` 有管理接口；`deployment_config.py` 有按 key get/put/patch。可用接口不等于本 unit 全部纳入 |
| 接入 | `run.py` 的 Core router 使用 `require_peer_jwt`。D-581 确认 CLI 用 JWT secret 自签；验证不要求 peers 登记，不因此把 CLI 当作完整 Peer |

Sir 已允许重整普通 REST，以 CLI 为首个普通消费者。已核实的现有交点是 client-web 的
`packages/core/src/semantic-retrieval/main.ts`、`lexical-retrieval/main.ts`、`organization/main.ts` 调用
`PeerManager.delegate`；对应 core-py routes 声明 `PEER_INBOUND`。这些是 Peer 协议消费者，而非本 unit 所说
的外部 REST CLI。接口设计须覆盖这个真实交点，不把全部旧 REST 当作不可改变的基线。

这是设计准备，不是完整 preflight。CLI package 的物理位置、依赖与最低 Python、安装命令、Core 接口兼容、
认证、内容传输、PyPI 名称/发布权限和各旅程的实际入口，仍需在相应设计阶段核验。

## 管理范围扩展后的核验

同日依据 D-573 检查 `app/business/peer/main.py`、`app/schemas/peer/main.py`、`app/business/extension/` 的
局部指南与 Host、`app/business/source/main.py`、`app/business/cron.py`、`app/business/job.py` 及对应 schema，
并读取最新 `docs/30-unit-tdd/organization.md`。

- PeerManager 已有 get/get_all、自身 publication/lease 与 delegation，无 wake 方法；CorePeerConfig 已有
  `http_public_base_url`。Lease 不表示“休眠”；普通 row 更新也不会让进程启动。
- Extension Host 已实现部署安装记录与 Peer-local enable/disable；`app/routes/extension.py` 可作为 REST
  重整的现有实现依据，不将启用意图与 running 混为一谈。
- SourceManager 已有 create 与 type/schema 注册；编辑/删除/查询需要补齐对应 domain/REST 接口。
- CronManager 已有 create/update/run_now/check；CronModel 保存 schedule、job_type、job_parameters、timeout、
  enabled 和调度游标。Source 不保存 schedule。Deployment `core.cron` 的 timezone 默认为 UTC。
- 已实现 Organization 的七种自动行为分别拥有 exact Job handler 和配置；显式 rumination 的旧 REST 路由
  不代表这些现有能力全部已经公开。CLI 的实际支持从当前 behavior/Job 合同取得，不重建组织行为 registry。
  D-595 核验补充：已有 rumination automatic Job 的输入只有 max_seeds，不支持指定 Block；本轮需要补齐
  显式 Job type，不能以立即执行门面或 Peer inbound 代替 CLI 的 Job 受理语义。

`docs/40-deployment/render-neon-self-host.md` 已记录：先打开 Core `/readyz` 才能唤醒休眠服务，过期的数据库
lease 不会触发它启动；错过的 Cron 不补跑。[Render 官方说明](https://render.com/docs/free#spinning-down-on-idle)
确认 Free web service 空闲后停止，新的普通 HTTP 请求可触发恢复。这个事实支持 HTTP wake 的具体场景，
不证明任意 hosting platform 或关闭的 native Peer 均可通过 HTTP 启动。

## D-575 后的接口核验

- `app/schemas/info_base/block.py` 的 `BlockModel.get_hydrated_content()` 返回 inline str 或经 Storage 加载的
  bytes，不改持久 content。`get` 的 hydration 选项可沿用它；solved content 是 Resolver 的另一个 owner，
  由 `resolver invoke` 承接，不保留独立 `read` 命令。
- `app/schemas/agent.py` 的 `AgentDefinitionModel` 持久化于 `agents`；字段为 name、system_prompt、tools、
  tool_choice、model 和 max_model_calls_per_turn。`app/business/agent/main.py` 在 run 时绑定 Tool 并创建
  Thread 快照。当前无普通 Agent definition 管理 REST；此管理范围不等于增加 Agent 对话/Thread 管理。
- `app/business/organization/rumination.py` 等行为向 `DeploymentConfigManager` 注册 owner 的 Pydantic
  schema；`BehaviorAgentConfig` 保存 `agent`。媒体解释配置另有 image/audio/video Agent 选择，不能把所有
  behavior config 强制裁成同一形状。现有 `app/routes/deployment_config.py` 已有按 key get/put/patch，
  但 key/schema 发现及 definition 所引用 model/tools 的发现仍需补齐或核对，不在 CLI 复制目录。
- `app/schemas/job.py` 有 `ABORTED`；`app/business/job.py` 的 run/check 仅有执行、超时及失败收口，没有主动
  取消入口或跨执行端停止链路。源码检索 `ABORTED|aborted|abort_job|cancel_job` 也未找到其执行实现。主动停止
  是本 unit 的技术缺口，不是现成 endpoint 包装；限时 wait 本身仍可只观察同一 Job，不改执行期限和状态。

本轮 ponytail 用于核对以上技术复用边界；仅更新 packet，未变更源码或 durable docs。

## D-588 后：Agent 与配置的发现边界

2026-09-13 进一步核验：AgentManager 的 Tool registry 为 peer-local；AIModel 与 AgentDefinition 是共享持久
记录。不能把本机能否绑定、执行作为 definition 保存的前置条件。具体方案见
[Agent definition 管理](agent-management-rest.md)，后按 D-589 确认，模型发现归 ai 命令组。

DeploymentConfigManager.register_schema 仅登记 schema ID 与 ConfigContract，没有 config key 对应关系；
业务模块另持有 CONFIG_KEY 常量。GET /configs 只能发现已经存在的记录，不能解决首次配置一个行为时的 key
发现。后续方案需要让 owner 提供这个信息，不能从 schema 字符串裁剪推导、在 CLI 硬编码，或新建 organization
统一 dispatcher。后续 [配置 REST 提案](deployment-config-rest.md) 建议同一 schema 注册增加 keys 元数据，
不增加独立 registry；已按 D-590 确认。

另一个待收敛点是管理读取：DeploymentConfigManager.read 目前会验证并规范化记录，unknown schema 或非法
持久 value 会使 GET 返回 409。这不同于供业务消费的 typed get；CLI 管理需要能查看和修复实际保存的值。
源码调用核验后的初稿曾建议 typed get 继续校验；D-590 纠正了这一推论：typed 返回不意味着重复校验已经
持久化的数据。管理读取保留实际值，PATCH 校验合并后的完整候选；typed get 的表示转换与移除重复校验一起
进入实现预演，不把源码现状固化为设计。以上尚未实施。

Organization config 模型仍由行为 owner 提供；大多数行为为 {agent: int}，媒体解释为 image_agent、audio_agent、
video_agent。配置写入不经 AgentManager 或行为执行入口；本 unit 不为这些 JSON 引用增加 FK、删除联动或预执行。
