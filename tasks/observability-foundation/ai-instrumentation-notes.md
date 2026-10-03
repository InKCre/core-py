# AI 首批点位与验收说明

此说明供主任务整合到 `docs/40-deployment/observability.md`，不是新的长期权威文档。

## 已实现点位

| 入口 | 记录 | 语义与边界 |
| --- | --- | --- |
| `AIManager.chat` / `AIManager.embed` | `ai.chat` / `ai.embed` span；操作、部署内 model/provider ID、dialect、配置中的 model identifier | 所有共同 AI 调用均覆盖，包含非 Agent 和 embedding；不读图、不修改 `AssistantMessage` 等业务合同。模型 identifier 限 ASCII 标识字符且最多 128 字符，供应商任意返回的 model/id 不复制。 |
| OpenAI-compatible response、Alibaba stream | input/output tokens、缓存输入与推理输出 token、固定结束原因；Alibaba 首块耗时 | 在 SDK 实际解析 response/chunk 后记录。流式 `choices=[]` 的最后 usage 块仍采集，后到总量替换前值，每次调用只累计一次。 |
| Agent Thread | `agent.turn` → `agent.step` → 模型和并发 `agent.tool` | 使用 thread UUID、turn 和 model-call 序号建立关系；并发工具共享 step 父 span。只对已绑定 code-owned Tool ID 记录名称；provider ToolCall ID 使用 SHA-256 摘要关联，避免任意 ID 携带正文。 |
| info-base `retrieve` Tool | `inkcre.retrieval.candidates` 结构化事件 | 逐成功 lexical/semantic 分支记录候选 block/relation ID 与候选数；不记录 query、excerpt、label 或得分。候选只是召回结果。 |
| info-base `get_entities` Tool | `inkcre.entity.read`，`read.kind=persisted` | 只记录实际非空返回的 block/relation ID 和数量。不存在的请求实体不算读到；随机读取同样按真实返回记录。 |
| Resolver Tool 成功 invoke | `inkcre.entity.read`，`read.kind=resolved` | 成功方法调用及结果投影后记录目标 block ID；不记录动态方法名、参数、schema 或结果。此点位不声称覆盖 Resolver 内部所有传递读取。 |
| `AgentQuerySink.execute` 选取结果 | `inkcre.agent.query.result` | 在最后一个已闭合成功提交被选入 `Job.state.result` 后记录 Job ID、thread UUID、最终引用 ID 与数量。不是每次 submit 都算最终结果，也不声称此时 Job 的最终持久化已经成功。 |

GenAI 属性固定映射到 `semantic-conventions-genai` 修订 `e07f4ebacb08f56db8c4c882d117720333fbca04`，映射位于 AI owner 的 `telemetry.py`。span 名称保持固定，动态 model、Tool 和业务 ID 不作为指标维度。token 计数使用自有 `inkcre.ai.token.usage` counter，不冒充语义约定中不同聚合类型的同名指标。

数字 usage 接受非负 int64，真实零保留，缺失、负值、布尔或溢出值均不写入 token 计数；input/output 的 `source` 分别为 `provider` 或 `unavailable`。缓存和推理维度只记录供应商明确返回的已知值，不额外加到 input/output 总量。缺失字段另计 `inkcre.ai.usage.missing`。不估算成本、不创建价格服务，也不将部分 token 和称作完整用量。

原始 finish reason 只允许 `stop`、`length`、`tool_calls`、`content_filter`、`function_call`，其他值映射为 `other`，每次最多保留 16 项。基础模式不复制模型输入输出、provider config、异常文本或 stack。现有 `agent_debug`、PG/Logtail 内容行为不变，不能据此宣称整个部署没有内容日志。

最终引用最多导出前 128 项中有效的正 int64 ID，并记录完整 `reference_count` 和未导出数量 `unreported_reference_count`。业务结果自身不截断、不增加验证或持久化模型。最终引用由模型提交，记录关联不验证实体存在，更不证明答案确实基于该实体或答案正确。

首批来源点位限上述 Tool 和 Agent Query Sink；图遍历 Tool、直接非 Agent 检索 API、Resolver 内部依赖读取尚不属于来源关联覆盖范围。AI 共同执行 span 本身已覆盖全部经 AIManager 的模型调用。这些 trace/log 会采样和过期，不替代答案或图谱变更的长期证据快照。

## 已执行验证

`pdm run python tasks/observability-foundation/experiments/ai_otlp_probe.py` 使用本地 HTTP 合成 provider、真实 OpenAI SDK 解析、真实生产 Tool/Resolver/Thread/Sink 和 OTel SDK/exporter，并在首次 OTLP HTTP 入口解码三信号。数据库读取和 Agent 定义装载使用合成领域对象隔离；没有真实供应商或 PostgreSQL 端到端验收。

实验显式设置 `INKCRE_ENV_FILE=''`，只配置本地三信号接收端，并使用合成数据库/JWT/provider 参数；不读取工作区 Grafana 或外部 provider 凭据。最终运行获得 13 次 provider HTTP 请求（其中 1 次验证关闭遥测）、31 个 span、4 个来源事件，并通过以下观察：

- 关闭遥测时在既有第三方 span 内执行真实 Alibaba HTTP 流式调用，不改写该 span 属性、不替换外部 current context。
- unknown、零、部分和负 usage，以及 embedding 与流式末尾 usage 分别符合合同；中途和末尾相同总量不会重复累计。
- 并发工具有共同 step 父 span、时间重叠，工具错误结果与取消传播不变。
- 同一 Agent 旅程中候选 block `(11,12)`、实际读取 block `(11)` 与 relation `(21)`、Resolver 目标 block `(11)`、最后选中引用 relation `(21)` 分开记录，四事件在同一 trace。
- 同批两次成功 submit 只记录最后一个最终结果；正文、query、工具输入输出、provider 回显 ID/model、异常消息与答案的统一 canary 在首次三信号出口均不存在。

AI/Agent Ruff、格式和 pyrefly、数据库 import/ownership 边界检查通过；既有 `tests/agent/test_debug_trace.py` 4 项通过。真实供应商行为、真实检索数据库与已获准 preview/SaaS 是剩余验收层次。
