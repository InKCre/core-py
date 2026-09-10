# Agent Tool 可用性检查（2026-09-10）

先补真实运行的开发可观测性，再改 Tool contract，保持预算不变以便对照。此前五条诊断轨迹与 bound schema 检查
已发现以下问题；源码尚未按本报告修改工具行为。

## 直接关联到已观察调用的问题

1. **发现流程描述不足**：resolver/graph_retrieval 的 description 只说 describe/invoke，`method`/`arguments` 等
   参数均无 description；没有说明应从 describe 返回的名称和 schema 调用。轨迹里出现 `read`、`content`、
   `incoming_relations` 等不存在方法，以及把 `get_text` 发给 graph 工具。应先补完整但简短的发现→调用示例与
   owner 区别，保持三个元工具。
2. **未知方法错误无法有效指导下一步**：只返回 `ValueError` + `Resolver method is not available` 或对应 graph
   文本；不知道合法名称，也没有下一次 describe 的具体参数。应由 capability owner 提供未知方法及可发现的方法
   信息，adapter 呈现适用 resolver/method 和一次可执行的恢复请求，不把方法表复制成第二个 registry。
3. **describe 过滤陷阱**：请求未知 `neighbors` / `find_referents` 等，只得到 methods=[] + missing_methods；
   模型再花一次请求才能发现全部能力。应保留精确过滤语义，同时返回紧凑的合法方法名或明确的无过滤 describe
   指引；无需在每个错误中回传完整 catalog。
4. **读取与写入参数语义过弱**：`source_ids` 没说明仅包含实际贡献的完整来源依据；`previous_synthesis_id` 没说明
   它用于重应用时的旧综合连续性；selected_text 没说明是来源中最小指称片段；candidate 参数没有呈现具体的谨慎
   使用边界。机械字段类型并不能替代这些使用语义。应由已有模型合同补 Field description，不结构化全体信息语义。
5. **retrieve 查询指导缺失**：query/mode 无语义说明，没有解释 lexical 与 semantic 的适用输入、hybrid 的独立
   分支及空结果的含义。轨迹出现多次长查询和空结果；它们不证明检索实现错误，但值得补操作指导后对照。

## 代码/Schema 直接验证、尚未证明导致历史预算失败的问题

- JSON Schema 接受 `{"action":"invoke"}`，运行时却因 calls 为空拒绝；describe 带 calls 也出现同样不一致。
  action 约束只藏在 model_validator。需要把条件表达给模型；是否进一步改为显式分支模型应以清晰性与兼容性决定。
- Graph Navigation 自动 reflection 取到的说明大量退化为 `find path` / `get block neighborhood`；direction、contents、
  cursor 没有解释，limit/max_hops 的运行时 bounds 不在生成 schema 中。完善 owner 方法合同，避免 adapter 复制规则。
- 指定不存在 Block 的 resolver describe 错误地退回“列举全部 Resolvers”。用 missing Block 替身验证，返回了 16 个
  无关 Resolver、约 43KB JSON；应区分“未指定过滤器”和“指定后未找到”。
- 原 Agent unexpected-tool 异常只向模型返回 `tool_execution_failed`，日志使用未正确接通的 app logger；此次开发
  追踪先保存真正异常和模型实际反馈，再确定哪些错误值得转换为可恢复领域错误。

## 复杂度判断

实测初始三种读取 Tool schemas 约 374 / 909 / 752 字符，candidate schema 约 1338 字符；单次 text Resolver
describe 与全部 graph methods describe 各约 2.6KB。没有证据说明正常 schemas 因体积过大导致失败。
主要负担是隐含条件、含糊参数、发现路径和低价值错误反馈，而不是元工具本身过度复杂。

批次子项失败当前保留在 results 中；不应为了一个 is_error 标记丢弃成功项，或自动重试整批。
后续用同一诊断输入、同一模型和预算对照错误次数、重复请求、新信息取得与终止点，同时检查语义质量。
