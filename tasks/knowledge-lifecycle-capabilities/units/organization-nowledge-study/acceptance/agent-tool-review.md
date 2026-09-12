# Agent Tool 可用性检查（2026-09-10）

先补真实运行的开发可观测性，再改 Tool contract，保持预算不变以便对照。此前五条诊断轨迹与 bound schema 检查
已发现以下问题；源码尚未按本报告修改工具行为。

## 直接关联到已观察调用的问题

1. **发现流程描述不足**：resolver/graph_retrieval 的 description 只说 describe/invoke，`method`/`arguments` 等
   参数均无 description；没有说明应从 describe 返回的名称和 schema 调用。轨迹里出现 `read`、`content`、
   `incoming_relations` 等不存在方法，以及把 `get_text` 发给 graph 工具。D-529 改为机制优先：错误时返回可用方法名
   并提示 describe；description 极简，一般不加例子，保持三个元工具。
2. **未知方法错误无法有效指导下一步**：只返回 `ValueError` + `Resolver method is not available` 或对应 graph
   文本；不知道合法名称，也没有下一次 describe 的具体参数。应由 capability owner 提供未知方法及可发现的方法
   信息，adapter 呈现适用 resolver/method、短错误及合法方法名；不返回 next_request，也不复制第二个 registry。
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

## Resolver 响应复核

输入 schema 的体积与工具响应体积是不同问题。已检查保存的真实响应及 adapter 输出：

- 定向 text Resolver describe 返回 6 个方法；一份实际响应紧凑编码后约 2487 字符。其中方法 descriptions 合计
  666 字符，含内部缓存/持久化实现说明和重复的参数解释。应缩短到调用者所需语义，参数约束由 input_schema 承担。
- describe 的 resolver→methods 分组有作用：多个 Block 可共用同一 Resolver，避免重复返回相同能力。
  method name / description / input_schema 各有用途，没有证据支持删掉完整 schema 或重新包装全部返回值。
- unknown-method 错误按 D-529 附方法名列表，不附每个方法的完整 schema，也不提供预制的下一次调用对象。
- invoke 的 results 保留一项对应一项请求、关联字段及原始 Resolver 返回值。目前不能因为响应“看起来长”就裁剪
  heterogeneous solved content、Relation 字段或丢弃批次成功项。
- index/block/method 的关联信息有部分重复，但帮助直接辨认同一 Block 上的不同操作与失败项；不是本轮体积主因，
  暂不改。空 missing 字段在上述响应仅约 41 字符，也不值得单独改响应兼容性。
- 已确认的 43KB 问题主要来自未命中时误返回全目录，按已接受的过滤规则修复；正常无过滤全目录的体积与未来
  Extension 规模相关，当前没有证据要求新增分页或目录压缩协议。
- 外层 content/is_error 是 AI adapter 的公共 ToolResult 投影，不属于 resolver 独有包装。本轮不改其通用语义。

**已由 D-530 接受**：保留 describe/invoke 的响应骨架与关联，缩短方法 description、修复错误的全目录回退，并用
短错误 + 方法名列表完成纠错；不为少量空字段、关联字段另造响应协议。其余 Tool 响应继续逐个评审。
