# Agent Query Sink

- **阶段**：Implementation / local acceptance。P1–P4 已落地，本地静态检查、运行时 catalog、动态 route 与 CLI/Job
  lifecycle 已通过；等待 draft PR preview 的真实模型 A1–A4。证据见 [implementation-evidence](implementation-evidence.md)。
- **目标与边界**：[D-611](../../decisions/D611-D620.md)。由 AI 组合既有 info-base 原子查询，承担检索决策并交付相关信息；不另建索引或接管下游创作。
- **位置**：`feat/agent-query-sink`，core-py root worktree；从干净且与 origin/main 一致的 `676886a4d2242be2f14465523c3267a126b60fd3` 切出。决策保留 D-611–D-650。
- **已确认交付物**：[D-620](../../decisions/D611-D620.md) 修正 D-612：基于 info-base 回答信息需求，实体是可寻址依据而非答案上限；允许跨材料比较、解释与有依据的推论。
- **已确认调用旅程**：[D-613](../../decisions/D611-D620.md)：独立检索调用，以既有 Job 承载。
- **已确认消费入口**：[D-614](../../decisions/D611-D620.md)：普通 Core REST + CLI；不含本轮 MCP/client-web 接入。
- **已确认配置归属**：[D-615](../../decisions/D611-D620.md)：实现 AgentQuerySink，使用 SinkBase 实例与 sink.config；不另建 deployment config。
- **已确认实例接合**：[D-616](../../decisions/D611-D620.md)：config 引用 Agent definition，禁用不隐含取消已开始 Job。
- **已确认入口与基类修正**：[D-617/D-618](../../decisions/D611-D620.md)：hooks 默认 no-op；Agent Query 自有 REST 入口，背后创建 Job，通用 Job API 亦可提交。
- **已确认 REST 受理回执**：[D-619](../../decisions/D611-D620.md)：202、Job 与 Location；不等待检索完成，后续复用 Job 控制。
- **已确认结果合同**：[D-621](../../decisions/D621-D630.md)：answer + references，正文对照实体依据；不再以 matches 列表为主体。
- **已确认结果提交**：[D-622](../../decisions/D621-D630.md)：普通 submit_query_result 工具，Job 收尾尽力保存历史中已成功提交的回答；无实时发布/恢复保证。
- **已确认 REST 生命周期**：[D-623](../../decisions/D621-D630.md)：query endpoint 随 AgentQuerySink 实例挂载/撤下；请求与 CLI 接口保留，通用 Job API 独立。
- **已确认工具接合**：[D-629](../../decisions/D621-D630.md)：六读取能力迁回各自领域，禁止 app/agent_tools；保留 D-624 的单一 registry、exact IDs 与初始 definition。
- **已确认内容边界**：[D-625](../../decisions/D621-D630.md)：使用文本/JSON 与媒体文字子图，不新增原始媒体工具结果通路；保持证据缺口可见。
- **已确认配置旅程**：[D-626](../../decisions/D621-D630.md)：文档模板 + 既有 Agent 管理 + 新增普通 Sink CLI 管理，不要求本地 checkout。
- **已确认结束语义**：[D-627](../../decisions/D621-D630.md)：正常 Turn 有交付则 finished，未交付则 failed；保留真实中断状态。预算只由 runtime 控制，不向 LLM 暴露。
- **当前复核面**：[Impact Handshake](impact-handshake.md)。[四条验收旅程与交付终点](acceptance.md) 已由 D-628 确认；[实现计划](implementation-plan.md)、[preflight](preflight.md)、[实测记录](preflight-evidence.md) 与 [corpus](corpus.md) 已准备。
- **事实依据**：[代码与边界调查](research.md)。区分读取工具可发现的方法、能够返回的内容和模型实际能够理解的输入。
- **下一步**：生成机械 artifacts，提交并推送 Core draft PR，完成 preview 真实模型 A1–A4；不合并。
- **文档修正**：D-631 已落实到领域 owner 文档；长期准则见 Hub draft PR #29，具体运行合同仍留 Core。

## 工作方式

遵循 parent 的 [discussion loop](../../collaboration/index.md) 和 [design taste](../../design-taste.md)。
新方案由 Agent 调查、推导并推荐，一次呈现一个重要复核面；低风险推论不逐项提问。讨论即时写回，
确认的决定进入唯一 decision register。未稳定的文档压力只记录于本 packet，不边讨论边改 durable docs。

完整流程为：产品设计 → 技术设计 ↔ 验收与实现计划探查 → 预演 → 冻结 baseline / Impact Handshake →
明确实施授权 → 实现与端到端验收 → 按约定交付并关闭。Parent task 不因本 unit 关闭而自动结束。

## 潜在影响与文档 owner

涉及 Core 的查询执行、Agent 工具适配与普通 Job API，以及 CLI 消费；MCP/client-web 的专门接入已排除。
不预设新的 Sink framework、独立 Agent runtime 或数据库表。已选择复用 Job，具体 handler 合同与横切改动由调用旅程传导。

后续稳定的 Sink/primitive query 关系归 Hub 产品/跨 unit 合同；运行、工具归属及具体接口归相应 Spoke。
当前只记录 promotion pressure，不编辑 `docs/_shared`，也不将旧 Organization 待提升项变成本 unit 的前置。
