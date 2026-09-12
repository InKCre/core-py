# 命题识别 SOP：evidence stance 复测

D-557 只有部分改善，未达到稳定排除同源支持误判的目标。技术摘要案例正确 no-op，rollout 条件案例仍
写入原方案 supports 派生内容。三次执行均自然结束。原始证据见
[stance-role 记录](tool-repair-stance-role.json)。

## 实现与条件

只替换 evidence stance SOP 前两段：先识别目标实际命题、归属和模态，区分来源记载与对象命题，再判断
证据贡献；不把目标换成另一个更容易比较的命题。两个方案派生案例均不能被改读为方案有效性的断言。
工具定义、Resolver 合同、共享提示词、工具组合、qwen3.6-plus 与 12 次调用预算不变；预算没有进入提示词。
没有新增字段、自检调用、推理输出要求或测试。

Definition 提交为 7bb868c9123ef5e6f72cd6d45537c5820a93bd51，配置到既有 preview Agent 后直接运行。
应用部署仍为 d8557909d02db02b1d694dc9c19058eae72b74b8（Preview 34692722037、debug 34692721031
均成功），应用代码没有改变。原始记录分别保存 head、definition_head 和实际 Agent definition；三个
thread 的实际系统提示均含新 SOP。静态 format/lint/typecheck/diff 检查通过。

初次启动在读取空库基线时遇到 PostgREST schema cache 503，没有创建数据或调用模型。环境恢复且认证
读取成功后重试。此后沿用上一轮修正后的 stance 单行为驱动：恢复 discovery 轮 stance 启动前的 26 Blocks、
14 Relations，重建词法索引，仅配置 evidence stance，一个 max_seeds=3 Job；原技术摘要通过 candidate
优先，其余自动选择。语义 Profile 仍未配置，不是严格单变量重放。

## 实际结果

Job 99 完成，13 次模型调用、15 次工具调用，零工具错误、零预算耗尽。

| 起点（本轮 / discovery ID） | 调用次数 | 结果 |
| --- | --- | --- |
| 技术摘要 407 / 347 | 5 | no-op，明确区别 provenance 与实质证据支持 |
| 美国区限额 387 / 327 | 4 | no-op，未取得可比较的第二个 Block |
| rollout 条件 408 / 348 | 4 | 调用 3 写入 401 supports 408，旧误判重现 |

401 对应原始方案 341。第一个案例的解释明确指出，技术摘要只是忠实转述原方案，已有 technical changes
described in 足以保留来源关系；相较 stance 轮相同内容案例的 12 次调用和误写，这是可观察的改善。
但第三个案例仍以原方案包含同样的 rollout 条件、具有批准归属作为支持理由，没有显示超出来源忠实性的
证据贡献。不能从一个正确 no-op 推导出同类判断已可靠，也不能从一轮结果隔离证明 SOP 是唯一因果。

美国区限额是本轮不同的自动起点；原事故提取案例没有重验。全部执行中没有验证“同源观察或推理提供
实质理由时仍能正确写入”的正向能力，因此不能把拒绝更多关系当作整体语义质量已经通过。
既定来源忠实性排除项仍未稳定生效，本轮不继续追加未确认修复。

## 清理

最终图 27 Blocks、15 Relations 已导出。临时候选边在执行后删除；27 Blocks、15 Relations、2 Jobs、
1 Agent、1 Model、1 Provider 全部清理，remaining_new_ids 均为空，无驱动 failure。
配置恢复/移除，Agent 日志导出后清理。第二个 Job 是词法维护，没有运行其它 organization 行为。
