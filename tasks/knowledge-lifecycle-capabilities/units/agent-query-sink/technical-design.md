# 技术方案（实施前历史基线）

本文保留实施前的设计与推演措辞；已由 [core-py#111](https://github.com/InKCre/core-py/pull/111) 实现。
当前状态见 [packet](packet.md)，实现合同见
[Agent Query Sink TDD](../../../../docs/30-unit-tdd/agent-query-sink.md)，验收结果见
[implementation-evidence](implementation-evidence.md)。下文的设计期状态不代表当前授权或交付状态。

产品范围、实例配置、启停与 REST 受理边界见 [D-611–D-620](../../decisions/D611-D620.md)，结果和实例 endpoint 见
[D-621–D-623](../../decisions/D621-D630.md)。

## 执行与配置的 owner

```text
CLI → Agent Query REST ─┐
通用 Job REST ──────────┴→ JobManager.create → jobs
                       ↓ claim
                  JobHandler
                       ↓
          AgentQuerySink instance ← SinkManager / sinks
                       │               config.agent
                       │                    ↓
                       │             Agent definition → AI model
                       ↓
                 AgentManager / Thread
                       ↓ 选定的读取工具
           原子 retrieval / info-base / Resolver

Agent Query 整理的结果 → Job state → 普通 Job REST → CLI
```

JobHandler 适配已领取的 Job，不把检索策略放进 JobManager。AgentQuerySink 拥有初始请求、所选 definition 的
使用与结果交付；Agent runtime 保持不知道 graph/query 业务。工具直接调用既有能力 owner，不让内部 Agent
通过 MCP/CLI 调用自身，也不使新 sink 依赖整个 Organization 的业务模块。读取工具复用位置还需逐项核验。

D-616 确认为 `sink.config = {"agent": 12}`，引用已有 Agent definition；通过 definition.model 选择 AI model。
model、system prompt、tools、tool choice、每 Turn 模型预算继续归 definition，不在 sink.config 复制完整定义
或增加同义 model override。多个 Sink 实例自然可以引用不同 Agent，无需另建配置档案或路由框架。

## Sink 实例与 Job 的接合

D-615 撤回此前不创建实例的建议。实现归 Sink domain，AgentQuerySink 继承 SinkBase；SinkManager 继续拥有
type 注册、实例持久化、config 与 Peer enable intent。无需为了接入它增加 generic deliver 或新的 lifecycle。

Job parameters 引用 Sink ID 与本次检索请求，不复制 Agent/模型配置。一个类型级 JobHandler 按通常方式注册，
不在每个实例 on_start 重复注册相同 Job type。can_handle 核对本地是否运行该 Sink 及是否具备 Agent 执行能力；
领取后交给对应实例执行。需要补的只是 SinkManager 本地运行实例的访问能力，不把 Job 业务移入 SinkManager。

D-616 确认 disable 阻止此 Peer 上的新领取，不隐含 abort 已取得实例并开始运行的 Job；停止一次工作仍由 Job
控制。已经启动的调用固定本次 Agent 引用，随后配置修改不改写已有 Thread。启停与 can_handle/claim 之间
沿用既有 best-effort 边界，不引入跨领域锁或重试；领取后实例已不可用时应明确失败，不绕过 enable 偷启实例。
资格/领取竞态的具体实现需继续预演；不改变已确认的启停与 Job 独立控制语义。

按 D-618，Agent Query 有自己的 REST 受理入口，背后调用 JobManager.create，而非在 HTTP request 内 await
完整 Agent 执行。通用 Job API 可直接提交同类型 Job；两条路径不各自实现校验、排队或执行。
D-619 确认受理成功返回 202、已创建的 Job 与指向既有 Job GET 的 Location，之后复用 Job 查询/停止及 CLI
有界等待；D-623 确认 endpoint path 与实例挂载方式，见下节。不把“由 Job 执行”当作取消业务 REST 的依据。
Sink 管理与 Agent definition 管理复用当前 REST；CLI 需要补足相关 Sink 管理，MCP/client-web 仍不在范围内。

针对 Sir 的 SinkBase 复核，D-617 确认保留注册、配置和实例管理，不把“拥有 HTTP endpoint”作为实例存在的
条件。两个 lifecycle hooks 提供默认 no-op，让没有自有常驻资源的 Sink 不必写空 override。
`on_start(app)` 目前服务真实的 Core FastAPI host，先保留显式参数，
不为消除未使用参数增加 RuntimeContext、HTTP Sink 子层或通用资源框架。MCP 仍覆盖 hooks 管理自身资源；
按 D-623，Agent Query 也覆盖 hooks 管理自己的 endpoint，不另起 worker，也不在 close 取消 Job。

## 检索结果合同

D-620 已提升产品定位，D-621 确认 answer + references；前者可用 Markdown 回应问题，后者沿用
`{type, id}` 表达支撑回答/明确交付材料的实体集合，而非全部访问记录。不另建结果实体或 citation ID。
正文在对应判断附近以 block:42 / relation:73 指明实体身份，让人能对上依据；具体呈现与引用处理在实现
计划中核对，不预设通用引用解析器或引用关系表。提交与保存方式由 D-622 确认。

```json
{
  "answer": "两次讨论的前提不同：前者面向固定能力（block:42），后者面向动态扩展（block:57）。据此判断，两者未必矛盾。",
  "references": [
    {"type": "block", "id": 42},
    {"type": "block", "id": 57}
  ]
}
```

上例是假设案例，不是实际数据或已验收事实。answer 可以是原文的简短指引、比较、解释、条件化判断或
信息缺口，不固定报告章节；不再强制逐实体 reason 和单独 summary，也不加自报 confidence/混合分数。
表达中区分原文与推论。完整内容继续通过实体与 Resolver 取得，不默认复制文件或多模态 bytes。

明确交付“本次未找到依据”不同于尚未交付任何结果；不能用空对象填补后者。Job 负责执行状态，结果负责
回应问题。提交与尽力保存路径由 D-622 确认；具体终止映射见 D-627 与下文。

## REST 与 CLI 调用

D-623 确认 AgentQuerySink 在 on_start 挂载自己实例的 `POST /sinks/{sink_id}/query`，on_close 撤下。
它不是任意 Sink 的 generic invoke，也不是由 SinkManager 按类型调用同名方法。
请求包含 `query: str` 与可选 `timeout_seconds`，
前者同时容纳问题、上下文与已知实体线索，暂不机械拆出 context/seeds 等字段；后者映射 Job 执行预算，
不是 HTTP 等待时长。路径决定 Sink，模型/prompt/tools 仍从该 Sink 的 Agent definition 取得。

route 经 Agent Query 的共同 admission 路径创建 Job，按 D-619 返回 202/Job/Location。Sink 存在且
类型正确等共有规则在两种提交入口共同经过的 owner 处实现，不只由专用 route 检查。专用 endpoint
只有实例在该 Peer 启动并挂载时存在；通用 /jobs 独立存在，两者不必具有相同可用性。
disable 撤下 endpoint，但不取消已受理的 Job，也不影响旧 Job 查询；execute/claim 仍依据执行 Peer
的 Sink 启用与能力。不存在“用了 Job，所以 caller endpoint 必须独立于 Sink 生命周期”的推论。

CLI 新增 `inkcre-cli query "问题及上下文" --sink 7`，默认只发起工作并输出 Job；通过既有
`inkcre-cli job wait <id> --for 30s` 观察、`job get` 读取、`job abort` 停止。复用既有输入文件/stdin、
schema 发现和 compact JSON 输出能力，不新建 query 的任务控制子命令，也不把有异步结果的 Agent Query
塞进当前同步 recall --mode。Sink 发现/管理命令与初始 Agent 配置见 D-626 和下文。

## 结果提交与保存

D-622 确认使用 Sink-owned 普通 Agent Tool `submit_query_result`，输入为 D-621 的 answer + references，返回
同一结构化值。输入由现有 Agent runtime 的 Pydantic model 校验；Sink 从已完整记录的成功 ToolResult
取得值，不再解析最终自由文本，也不重复验证已通过工具边界的结果。该工具不写 graph、不修改 Job，
不要求模型携带 job_id，不引入 per-run context、终结型工具协议或新的 Agent output framework。

若有多次成功提交，按 Thread 消息及该批 ToolResult 的既有顺序取最后一次；后续失败提交不抹掉前一次。
普通 Assistant 文字不成为第二份结果。工具成功表示 Agent 已交付结构化回答，不等于 Job 已完成或
结果已存入数据库；definition 应说明提交后可以结束，但不为此修改通用 Thread 的终止语义。

Job handler 在正常结束及异常/取消清理时，将已记录的回答放入当前 job.state.result；然后正常返回或
继续传播原错误/取消，由既有 Job close 保存 state 与真实终态。正常结束却没有成功提交应明确报告
未交付结果，不能填补成空回答。D-627 确认以 termination 保留预算结束原因，有回答不意味着检索穷尽。

本轮不提供逐步候选或实时回答发布，也不做持久 Thread、强制补跑总结、隐式重试/恢复。当前
batch 未闭合、进程崩溃、数据库收尾失败或 expire_overdue 先关闭记录，均可能使内存回答未被持久化。
这是 D-622 接受的 best-effort 边界，不能宣称“已经调用提交工具就一定不会丢结果”。

## 执行基线

关键预演已完成，见 [preflight](preflight.md)。D-628 确认四条验收旅程与交付终点；实施次序及横切
影响见 [实现计划](implementation-plan.md) 和 [Impact Handshake](impact-handshake.md)。新 Query handler
与真实持久化收尾仍需在实施后验收，不把已有 Thread 实验等同于整个功能已通过。

不由本拓扑预先推出新数据库表、通用 query framework、持久 Thread 或 MCP/client-web 改动。

## 读取工具复用与初始 definition

D-624 确认初始 Agent 使用六个已有读取工具，加上 D-622 的 submit_query_result；不另建“研究”“总结”工具。

| Exact Tool ID | 责任 |
| --- | --- |
| retrieve | lexical/semantic/hybrid 查询；各路保留各自结果 |
| get_entities | 批量读取持久 Block/Relation 记录 |
| resolver | 发现/调用 exact Resolver 的公共 typed read methods |
| get_entity_neighborhood | 读取实体邻域 |
| find_path | 有界路径查询 |
| get_connected_components | 按明确关系条件查询种子连通性 |
| submit_query_result | 提交本次回答与引用，归 Agent Query |

六个读取工具当前实现在 organization/tools.py。D-629 撤回中央 app/agent_tools 方案：retrieve 与
get_entities 回归 InfoBaseManager；邻域、路径、连通性回归 GraphNavigationRetrievalManager；
resolver 回归 Resolver 领域，submit_query_result 归 AgentQuerySink。专用 schema 随领域迁移。
工具注册是调用方式，不成为业务 owner；runtime 只拥有注册、输入绑定与执行，不拥有检索编排。
单 Block 内容行为由 Resolver 实例执行；现有 resolver 工具的跨类型发现/批量分派建议复用
ResolverManager，D-630 已确认该分工。不在 Resolver 基类添加 Agent 专用抽象方法。
Tool handler 是领域所属 controller，Manager/Resolver 方法是 service；不把 handler 整体塞进业务类。
工具 schema、输入/结果适配在 controller 接合；业务调用保持普通领域接口，runtime 负责工具输入验证。
bootstrap 显式加载注册；Organization 与 Agent Query 的 definitions 继续引用相同 exact IDs。
必要常量/类型导出不顺带加载 Organization 实现。语义、参数键和结果行为先保持；去掉读取路径对
OrganizationError 等写入专用合同的偶然依赖，不能简单搬整个 tools.py 或把它作为共享转发层。

初始 definition 作为可编辑的推荐模板提供，创建后是普通 agents 记录；模型由配置者选择。
模板表达 D-620 的目的、依据与推论区别、可用能力和 D-622 的交付动作，不规定固定检索顺序/工具配额。
不配 graph 写入、organization 调度或外部研究工具；不在启动时覆盖用户修改。不新增模板 registry，
具体模板交付/CLI 配置步骤见 D-626 的普通管理旅程，不要求用户已经 checkout 仓库。

现有 resolver Agent Tool 拒绝 bytes（包括嵌套 bytes），它不是 MCP Resource 或任意多模态交付接口。
该限制经明确产品复核后由 D-625 接受为本轮边界，不是由历史实现自动推导出的永久产品上限。

## 已确认：本轮内容理解边界

D-625 确认本轮使用 Resolver 可交付的文本/JSON，以及图中已有或普通 Resolver 读取所 materialize 的文字
内容；不新增 Query 执行期间将原始图片、音频、视频作为模型输入的通路。媒体 Block 仍可被检索、引用
并沿图读取 OCR、转录或解释；这不是只检索 text resolver，也不禁止已有读取的 lazy materialization。
Agent 不能把衍生文字中的缺口当作原始媒体中不存在证据，更不能声称已查看未能取得的原始内容。

此取舍避免本轮跨及通用 Agent/AI 消息合同和 dialect 投影。以真实媒体案例检查工具是否能取得衍生
正文，以及没有可用正文时能否准确说明缺口；需要原始媒体理解的需求应保留为已知能力边界，而非伪装
成已经回答或系统中没有相关信息。

## 已确认：通过普通 CLI 管理完成配置

D-626 确认无需本地 Core checkout。Agent Query 的使用文档提供完整、可复制编辑的 AgentForm JSON，包含推荐
prompt、七个 exact tools、tool_choice 与可调整的模型调用预算；配置者选择现有 AIModel 并填写 model。
文档是推荐模板的单一交付位置，不为它新增模板 REST API、registry、安装副作用或 CLI 内置 prompt。
模板描述信息需求、依据与推论的区别、D-625 内容边界及 submit_query_result，不规定固定检索步骤。

已有 ai models、agent tools、agent create/update 和 connection 命令可复用。补齐普通 sink 命令组：
types、list、get、create、config get/replace、enable、disable、delete。create --type 与 config replace
使用既有 --input/--input-json/--schema；动态 config schema 来自 sink-types catalog，不在 CLI 硬编码。
这些操作映射既有 Sink REST，不引入 query setup 向导或把 Agent、Sink 创建合并为一个事务。
enable/disable 作用于当前连接的 Peer，不增加新的 delegation 或跨 Peer 默认选择行为。

文档旅程是：发现模型/工具 → 将模板保存为本地 JSON、选择 model → agent create → sink create
（config.agent 引用返回的 Agent ID）→ sink enable → query --sink → job wait/get。每步使用实际响应 ID，
不自动选择唯一模型、默认 Agent 或默认 Sink。已具备 AIProvider/AIModel 和基础检索配置是此旅程的前提；
本轮不借初始化 Agent Query 扩展成部署向导。模板预算初值随真实模型验收校准，不成为协议常量。

当前 Sink REST 列表返回完整 tuple，CLI 尚无 sink group；具体分页与 schema 发现对齐需在实现计划中
核对，不声称现有接口已经具备 Source REST 的所有能力。Sink nickname 目前仅创建时可填写，本轮不为
上述配置旅程额外设计通用实例 PATCH。

## 已确认：结束原因与 Job 终态

D-627 确认保持 Job 通用状态不变，由 Agent Query 判断是否完成自己的交付合同。Turn 正常返回时，将其原有
completed/max_model_calls 值记录为 job.state.termination；存在成功提交则 handler 正常返回，由
JobManager 关闭为 finished。不因为触及模型调用预算就判失败：最后允许的一次模型调用可以恰好完成
submit_query_result，而 Thread 此时仍返回 max_model_calls。finished 表示正常结束并已交付，不表示
检索穷尽或答案充分；预算结束原因继续可见，不能悄悄改成 completed。

| 执行结果 | Job 状态 | Agent Query state |
| --- | --- | --- |
| completed，已有提交 | finished | result + termination=completed |
| max_model_calls，已有提交 | finished | result + termination=max_model_calls |
| 上述任一种正常返回，但没有提交 | failed | termination + 既有 error 字段说明未交付；无 result |
| 执行异常、Job 超时或取消 | failed / timed_out / aborted | 按 D-622 尽力保留已有 result；沿用 Job 错误/终态合同 |

无提交不是“未找到信息”。Agent 可以提交说明缺少依据、references 为空的回答；这依然是交付。
普通 Assistant 最终文字不能替代 submit_query_result，也不由 Sink 解析或自动包装成结果。
无提交时在 Query owner 报告未交付错误，使用现有 Job 异常收尾，不扩充 JobManager 的业务分支。
已有结果后发生真实执行异常也不能改为 finished；结果与失败状态可以同时存在。

不增加 partial/success/has_result 字段或新的 Job 状态，不强制补跑总结。模型调用次数预算与 Job
wall-clock timeout 不混用。Thread 未正常返回时不虚构 termination；Job 已有状态足以表达中止原因。
后续预演覆盖最后一轮提交、预算结束无提交、已提交后异常及取消传播，不在设计阶段新增自动化测试。

预算检查是 Python runtime 的行为，而非模型的行为。本轮不把剩余次数、倒计时或最大调用数注入
system/user message，不增加预算查询工具，也不临近预算时向模型发送收尾消息。配置中的执行预算
继续由 Thread 消费，termination 供调用者观察，不回灌至模型。模板要求提交回答，与告知剩余预算不同。

## 执行资格：复用 Agent/AI 的本地判断

按 D-616 的接合，在 claim 前先取得本地运行中的对应 AgentQuerySink，再调用现有
AgentManager.can_execute(config.agent, "text")。该方法检查 Agent 是否存在、本地能否绑定其工具，
再交给 AIManager.can_execute 判断模型、Provider、dialect 和所需能力。它不是实际模型请求或远端
健康探测，不需要把同一判断复制进 Sink，也不新增资格注册表。

不预执行检索，也不要求全部索引完备或所有候选 Resolver 都可读取才能领取；这些属于实际工具执行
及证据判断。领取后按现有 run(agent_id, initial_message) 绑定当时的 definition，保留现有一次快照
语义；can_handle 不是资源预留，检查后变化沿既有失败处理，不重试或静默换模型/Sink。
运行实例访问与启停交错仍在 preflight 范围，不据此增加独立 Worker 或扩大 SinkManager 职责。
