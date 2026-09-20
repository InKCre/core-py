# 已核验的复用基础

2026-09-20，基线 `676886a4d2242be2f14465523c3267a126b60fd3`。仅静态代码/合同调查，未执行模型或生产数据请求。

## Agent 执行不需要重新发明

`app/business/agent/main.py::AgentManager.run` 读取持久 Agent definition，绑定工具后创建 Thread 并启动首个 Turn。
`thread.py` 已有并发 Tool batch、每 Turn 模型调用预算、取消和 messages。没有工具调用的 Assistant message
结束当前 Turn；达到预算也会结束，但不保证此时已有最终文字结果。这是结果交付设计需要处理的真实压力。
当前只实现 in-memory thread persistence；不能据此承诺跨重启会话恢复。

Agent/AI 不理解 info-base graph；查询策略、工具选择和结果含义属于其 caller。`AgentForm` 已包含 model、
system_prompt、tools、tool_choice 与 max_model_calls_per_turn，不应为本 unit 另造一份同义 definition。

## 读取工具已经存在，但物理归属还不能直接照搬

`app/business/organization/tools.py` 已注册 `retrieve`、`get_entities`、`resolver`、
`get_entity_neighborhood`、`find_path`、`get_connected_components`。
`retrieve` 可独立执行 lexical/semantic 或并发两路，保留各路结果/错误，不强行合成分数。
图工具交给 GraphNavigationRetrievalManager；Resolver 元工具发现/调用当前 exact Resolver 的 typed read method。

这些读取 tools 与 Organization mutation tools 同文件，输入模型主要位于 `schemas/organization_behavior.py`，
模块还导入具体 Organization behaviors。因此“handler 已有”不等于“新 sink 应依赖整个 organization 模块”。
后续应核对最小的正确复用位置与注册入口，保持现有 exact Tool IDs；本轮尚未决定代码搬迁方案。

MCP 的七个工具是另一组协议投影，`app/business/sink/mcp.py` 直接调用各 owner，并拥有 MCP Resource 交付。
它们不是 AgentManager 的 native Tool registry。不能为了复用能力而让本机 Agent 必须通过 MCP 调用自己，
也不能把 MCP wire schema 当作新 sink 的领域合同。

## 原子查询与 Sink 保持边界

- Lexical/semantic managers 返回既有实体及命中/排序信息；maintenance 是独立行为。
- GraphNavigationRetrievalManager 只查询既有图，返回邻域、路径、连通结构；不执行 Resolver。
- Resolver 解释内容；storage pointer 不能被检索 Agent 当成实际内容。
- SinkManager/Base 已有注册、持久实例、Peer enable intent 与 start/close，但 CLI 产品上也是 sink，
  并不是一个 SinkBase runtime instance。故“称为 sink”不自动决定必须新增实例行、endpoint mount 或 lifecycle。

依据：`docs/30-unit-tdd/{business-pipeline-and-authority,mcp-sink,lexical-retrieval,graph-navigation-retrieval}.md`，
`app/business/{agent,sink}/AGENTS.md`，上述当前源码。技术阶段再逐项追调用方，不以这些证据冒充完整 preflight。

## 已恢复的讨论依据

任务的 design-taste、collaboration protocol、Agent Tool common patterns 和 validation-boundaries 已重读。
关键约束是工具可组合、结果保留可寻址身份、定义与 SOP 分离、按真实轨迹诊断、不把部分成果丢弃，
以及不因重复分层增加校验边界。暂不新增同义的 task-wide guideline。

已按当前 AGENTS 的 advisor 指南取得一次独立、只读的产品判断：可寻址结果与简短文字结论不是二选一，
模型 Turn 正常结束也不证明检索目标达成。主代理据现有 Thread 实现复核，保留为方案/验收压力，
不把 advisor 建议记为 Sir 已批准的产品合同。

## 消费入口补查

`app/routes/retrieval.py` 提供普通 lexical/semantic REST，`app/routes/agent.py` 目前仅管理 definitions 和发现
Tools，没有公开的 Agent Thread execution API。`cli/src/inkcre_cli/commands/info.py::recall` 显式选择
lexical/semantic，独立返回各路结果。`MCPSink._register_tools` 的 recall 同样是调用原子查询，不是内部 Agent。

`client-web/apps/client-web/src/components/recall/RecallSearch.vue` 是应用级入口。当前 Search 调用 lexical，
再将 q 传给 List/Graph overview；这不是一个现成的 Agent Query 结果容器。是否扩展其体验是产品范围决策，
不能由目录位置或已有搜索输入框直接推导必须本轮改造 UI。上述读取没有修改 client-web。

## Job 复用调查

`JobModel` 已有 parameters、state JSONB，pending/running/terminal 状态和 timeout_seconds；
`JobManager.run` 在 can_handle 后原子领取，await handler，并统一处理取消、超时和异常。
`LexicalMaintainJobHandler` 已将报告写入 job.state；`JobRepository.close` 持久化 state 与终态。
普通 REST 和 CLI 已有创建/get/abort、有界 wait；不需要另建通用 Task API。

当前 handler 修改 state 仅影响内存模型，close 才写数据库；没有现成的运行中进展保存接口。
Agent Thread 的 messages 也仅在内存。结果可优先放在 Agent Query 自己定义的 job.state payload 中，
但不能声称现在已经支持边执行边返回候选、崩溃后保留未落库成果或恢复探索。
技术设计须明确“检索提交的结果”和“工具访问过的候选”有何区别，避免将所有原始命中冒充筛选结果。

另一项需预演的真实边界：`JobRepository.close` 只更新仍 running 的记录；超时清扫也会关闭记录。
结果发布不能假定 handler 的 finally 总能将成果写回。先确定需要保留的结果单位和时点，再选择最小保存路径；
当前不据此引入 checkpoint、重试或持久 Thread。

## 配置与 Sink 实例的区分

`SinkBase` / `SinkManager` 提供具名持久实例、config、Peer enable intent 与 on_start/on_close。
MCPSink 使用该生命周期持有 SDK session manager 和 exact endpoint mount；这是当前实现的资源需要。
`docs/30-unit-tdd/business-pipeline-and-authority.md` 已明确 CLI 是产品 sink，但不是 SinkBase instance。

`organization/rumination.py` 展示 deployment config 选择既有 Agent 的模式；实际 model/prompt/tools/预算
仍由 `agents` 持有。此前主代理/advisor 据无常驻 endpoint 建议省去实例，经 D-615 修正：Sir 要求 Core 内
该 sink 使用既有 Sink 实例组织配置与运行。保留 Agent 引用模式，选择关系的 authority 改为 sink.config。
不能将“无需常驻 endpoint”推导为“实例配置/生命周期没有价值”。

进一步核对：当前 SinkManager 有本地 `_running` map，没有公开的 running-instance 获取方法；JobHandler
是类型级 registry，不能按 Sink 实例重复注册。同一 Job type 可以按 parameters 中的 Sink 选择实例，
无需新增通用 Sink 执行或派发接口。disable 与执行的产品边界已由 D-616 确认，具体实现仍待预演。

## Sink 生命周期必要性复核

Sir 追问此前“没有独立 endpoint 启停”的含义，并要求检查 SinkBase 是否过度设计。这里必须区分三件事：
Sink 实例启用/禁用、具体实现拥有的资源启停，以及 HTTP route 挂载/移除。三者不是同义词。
此前由“没有 endpoint”推导“无需 Sink 实例”的依据过窄，D-615 已撤回该结论。随后 D-618 进一步纠正
入口假设：Agent Query 本身仍提供 REST，背后创建 Job；不是只有普通 Job REST。D-623 已确认随实例挂载。

当前 `SinkBase` 只有注册、配置类型恢复/更新与两个 abstract lifecycle hooks；没有通用 deliver、后台循环、
endpoint registry、snapshot/restore 或 reconcile。`SinkManager` 管 persisted intent 和本地实例，
`MCPSink.on_start/on_close` 自己管理 MCP SDK session manager 与 `/sinks/{id}/mcp` 挂载。
Manager 不直接管理 MCP route，因此不能把整个 Sink 模块称为 HTTP endpoint framework。

真实的专用倾向在于 `SinkBase.on_start(app: FastAPI)`：两个 hooks 被要求每个子类实现，Manager 也以
app 已提供作为 runtime 已启动的前提。Agent Query 无需常驻资源，照搬会产生两个空 override；但本机
Core 当前确实由 FastAPI bootstrap 提供 app，尚无证据要求这轮为无 HTTP host 再造 provider/context 层。
D-617 随后确认 hooks 默认 no-op、暂留 app 参数的局部收敛；不是重做 Sink framework 的授权。

REST 复核证据：`app/routes/job.py::create_job` 已经通过 `JobManager.create` 持久受理、返回 Location 并通知
worker，HTTP 不等待实际 Job 完成。Agent Query REST 可复用该业务入口，不需要内部发 HTTP 给 /jobs。
D-619 已确认业务受理返回 202，D-623 确认实例级 route；原 `/jobs` 创建资源返回 201 不因此需要更改。

独立只读复核也未发现必须重做基类的理由，并指出 Manager 有一条需纳入预演的交错：enable 等待
on_start 时尚未写 `_running`，并发 disable 可先更新 intent、发现无实例而返回，随后 enable 挂入实例。
这是源码推导而非已复现实验，属于 Manager 状态转换问题，不是删除 lifecycle hooks 就能解决的。
接合 Job eligibility 时不能忽略此交错，也不在本次基类讨论中擅自承诺锁、重试或全局 reconcile。

## 结构化结果交付的复用路径

D-621 确认后重新核对 `agent/main.py`、`agent/thread.py`、`agent/contracts.py`、`agent/persistence.py`
和 `job.py`/`persistence/job/repository.py`。现有工具边界是单个 Pydantic input → JSON return；成功值
进入 ToolResult，整个 batch 完成后才连同 Assistant message 一起写入内存 Thread。Sink 可以读取该历史，
无需新增 Agent runtime 回调或模型最终 JSON 解析协议。

JobHandler 传入的 job 是执行局部对象，JobManager.run 各终止分支调用 close 保存其 state；失败分支
合并 error 而非清空 state。独立 Tool 按 job_id 写数据库会增加第二个写入者，又可能被 close 的旧快照
整体覆盖，因此不推荐此路径。仅让普通工具返回结果、handler 收尾提取，能保持一个 Job state 写入路径。

独立 advisor 与主代理源码推演一致：该路径可在取消/异常时尽力保存已闭合消息中的回答，但不提供即时
持久化。某结果工具已完成而同批其它工具尚未完成时取消，结果尚未进入历史；数据库超时清扫先关闭记录
时 close 也不会再写 state。这些是具体残余，不以已有结构化工具支持冒充成果必达保证。

## REST route 与 CLI 消费入口复核

`run.py` 在 bootstrap 前将普通 Core routers 统一挂载，现有 Sink 管理、Job 管理 route 不随实例启停。
MCPSink exact mount 服务其实际协议 session，Agent Query 则受理 Job，不需要在接入 Peer 执行工作。
主代理与独立 advisor 曾据此推荐固定的 Agent Query-owned route，被 Sir 于 D-623 否决。错误在于
将共享 Job admission 合同推成两种产品入口必须具有相同可用性，又让执行基础设施决定 Sink 暴露服务的
生命周期。当前结论是 AgentQuerySink 自己挂载/撤下 endpoint；/jobs 继续独立，两者没有矛盾。

CLI 实际 console script 是 `inkcre-cli`，而非 `inkcre`。`commands/info.py::recall` 当前同步执行 lexical/
semantic 并独立返回；`commands/jobs.py` 已有 create/get/abort 与 observe 有界轮询。建议独立 query 命令
投影业务 REST，之后使用已有 Job 控制；不改已有 recall 输出使其有时返回命中、有时返回 Job。
`command.py` 已有 --input/--input-json/--schema，交付实现应复用，不另建内容输入格式。

## 六个读取工具的实际依赖

逐一读取 organization/tools.py 的 retrieve、resolver、get_entities、get_entity_neighborhood、find_path、
get_connected_components，及 schemas/organization_behavior.py 的对应输入模型。读取本体依赖各查询
manager、BlockService/InfoBaseManager/ResolverManager，不需要具体 Organization behavior；但所在模块
顶层导入了全部写入行为，organization/__init__.py 又导出工具，故新 consumer 不能只从该包 import 即算解耦。

retrieve 同时组合 lexical 与 semantic；resolver 的输入 schema 来自 ResolverManager 的公共方法反射，
无需修改 Resolver 或 Extension 增加 Agent metadata。现有 _exact_result 捕获 OrganizationError，不能
将这个 helper 连同读取函数机械迁移；共享适配层不应继续依赖 Organization 错误合同。

_project_json 会递归拒绝 bytes，然后转换模型/dataclass/普通JSON值；因此 get_solved_content 等方法
可被发现但其特定返回值未必能交付给内部 Agent。这个限制与 method discovery、实际方法支持情况不同。
六工具复用并不完成多模态内容支持。初始 Agent 的真实内容能力必须另行明确并纳入验收证据。

以下为已被 D-629 否决的历史提案，不是实施依据。主代理与独立 advisor 曾推荐普通 app/agent_tools
适配模块，集中工具专用投影/输入包装，保留单一的
AgentManager registry。tests/organization/acceptance/agent_definitions.json 是既有验收配置，而非
可直接作为新功能默认配置分发的权威；新模板应由 Agent Query owner 提供，不让验收数据塑造产品。

## 工具结果与多模态输入不是同一条通路

2026-09-20 核对 schemas/ai/chat.py：ToolResult.content 是 JSONValue；image/audio/video content parts
用于 UserMessage，而非工具结果。openai_compatible.py::_message_params 把每项 ToolResult 编码为
role=tool 的 JSON 字符串；AlibabaModelStudioDialect 复用此实现，仅覆盖 UserMessage 的多模态投影。
因此去掉 _project_json 的 bytes 拒绝或将 bytes base64 化，都不等于模型能看到图片、听到音频。

[Alibaba Function Calling 官方示例](https://www.alibabacloud.com/help/en/model-studio/qwen-function-calling)
以 tool_call_id 关联 tool 文本结果。该示例支持当前实现的依据，但不足以断言全部模型/协议都禁止多模态
工具结果。若本轮需要直接原始多模态理解，应进一步核验目标 dialect 的合法投影并做真实模型实验，不能
让 Resolver 增加 Agent 专用合同，也不能把 MCP Resource 或 CLI multipart 当作内部 Agent 已有能力。

ImageResolver/AudioResolver 的 get_text(default) 不支持；lexical context 返回元数据，可选 materialize
文本 child，但不直接返回 child 的正文。Agent 需沿图读取 OCR/转录及已有解释。PDFResolver 的默认
get_text 能读取文本层，不代表纯扫描 PDF 已被支持。文本与结构化证据可覆盖多种来源，但不是无损的
多模态内容替代；仅存在于图像空间关系、音色或视频时序中的证据可能缺失。

## 已安装 CLI 的实际配置入口

2026-09-20 检查 cli/src/inkcre_cli/main.py、commands/agent.py、source.py、extension.py 和 app/routes/sink.py。
CLI 已支持 ai models、agent tools/create/update 和普通 JSON 输入/schema 发现，但未注册 sink 命令组。
Core 已有 Sink types/list/get/create、config PUT、enable/disable/delete；enable/disable 取接入 Peer，
并非 Extension route_to_peer 形式。sink-types 包含 config_schema，因此新增 CLI 投影无需在 CLI 复制
AgentQuerySink 配置模型。当前没有单个 sink-type GET 或分页，不可机械照抄 Source CLI 路径。

推荐通过使用文档交付可编辑 AgentForm JSON，并复用已安装 CLI 的 agent create；这避免将 prompt 放入
CLI 或增加模板服务。该路径不依赖 checkout，但明确要求 deployment 已配置 AIModel 和基础检索。
Sink create 不启用实例，需显式 enable；查询 endpoint 因而能通过这一实际配置路径挂载。

## Turn 预算边界与 Job 收尾的实际次序

2026-09-20 复核 agent/thread.py::_execute_turn：没有 ToolCalls 的 Assistant 写入后返回 completed；
有 ToolCalls 时，先执行全部工具并写入闭合消息，再检查调用次数预算，达到上限返回 max_model_calls。
因此“最后一次调用成功提交回答”仍会触发 max_model_calls，不能仅凭该值把交付判为失败。

job.py::run 在 handler 正常返回时关闭为 finished；异常时记录 state.error 并 failed；wall-clock
TimeoutError 与 asyncio.CancelledError 分别关闭为 timed_out/aborted。Query owner 可以在正常 Turn
返回后判断是否有已提交结果，无需改这些通用分支。独立只读 advisor 与主代理判断一致：保留原 Turn
结束原因，已交付的正常预算结束不应误报失败。此为源码推演，尚未完成真实模型或取消路径验收。

## 本地执行资格已有 owner

agent/main.py::can_execute 已有 Agent 查询、工具绑定和 AIExecutionRequirement 的组合；
ai/main.py::can_execute 检查本地 dialect、模型/Provider 配置与声明能力，不发远端请求。
AgentManager.run 则在执行时重新加载 definition、绑定工具并构造 Thread。复用这些行为即可接入
Job can_handle；无需新增 Sink-owned AI 能力检查或以一次模型调用探测是否可领取。
can_execute 返回 false 不意味着所有 Peer 都不可执行；不能据此在受理入口拒绝持久化 Job。
