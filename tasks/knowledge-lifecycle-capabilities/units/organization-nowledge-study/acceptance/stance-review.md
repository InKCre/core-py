# 来源忠实性排除项：仅 evidence stance 复测

D-556 的措辞修复已经部署，但没有解决同源支持误判。三次执行均自然结束，两次仍以来源的权威或包含
相同内容作为 supports 的依据。不能将这次结果报告为修复通过。原始证据见
[stance 记录](tool-repair-stance.json)。

## 变更与验证条件

应用源码为 bf16ebdc372a5524113700f53ee1aca3b62d18b3。Preview application 34691527351 与调试配置
34691526275 均成功后运行。工具定义明确排除“仅证明派生内容忠实于来源”，不因来源权威例外，同时
保留同源观察/推理贡献实质理由的可能；Resolver 判断合同同步，Agent SOP、共享提示词、工具组合、
模型和预算不变。静态 format/lint/typecheck/diff 检查通过，没有新增测试。

只配置 evidence stance Agent，使用 qwen3.6-plus、12 次模型调用预算，未向模型公开预算。既有驱动恢复
discovery 轮 Job 92 启动前的 26 Blocks、14 Relations，排除之后的错误 supports 和其它并发行为写入。
Block ID 重映射、词法索引重建，语义 Profile 仍未配置，没有运行其它 organization 行为。

驱动最初错误设置 max_seeds=1，违反现有 Job 参数至少 3 的合同。Job 97 保持 pending，没有 Agent 调用。
中断驱动并核对后，将同一个 pending Job 修正为 max_seeds=3，恢复记录与清理；没有修改产品参数合同。
原首个 seed 通过临时 candidate 优先，其余按普通自动选择。原始记录保留 setup_correction 和 interruption。
该错误属于验收驱动，不是模型延迟或模型失败。

## 结果与实际覆盖

Job 97 完成，共 28 次模型调用、32 次工具调用，零工具错误、零预算耗尽。实际加载的工具定义和输入
judgment_contract 均包含本次修复，不是部署了旧定义。

| 起点（本轮 / discovery ID） | 调用次数 | 结果 |
| --- | --- | --- |
| 技术摘要 380 / 347 | 12 | 调用 11 写入 374 supports 380，误判重现 |
| Atlas rollout 361 / 328 | 10 | no-op，正确识别各证据只覆盖部分断言 |
| rollout 条件 381 / 348 | 6 | 调用 2 写入 374 supports 381，误判重现 |

374 对应 discovery 的原始方案 341。第一项的最终解释仍称原方案提供权威依据；第三项解释原方案包含
相同 rollout 条件，因而直接支持提取内容。轨迹没有显示超出来源忠实性的实质证据贡献。明确排除项已经
提供，模型仍作出同类判断，因此“补清这一句定义即可修好”的预期没有得到支持。这不证明所有提示词
优化无效，也不支持断言模型内部究竟忽略了哪句话。

第二项的 no-op 有实际理由：新限额公告、旧限额说明及实验各自只覆盖复合 rollout 说明的一部分。
但它不是同源推理仍可提供有效 stance 的正向验证。原事故提取案例 344 没有再次成为起点，不能宣称原三个
误判案例都已重验。此次不是严格单变量实验，也不能仅从调用次数增加认定新措辞导致了效率下降。

## 清理与交接

最终图 27 Blocks、16 Relations 已导出；临时候选边在执行后删除，其删除前内容保留于 Agent 输入。
27 Blocks、16 Relations、2 Jobs、1 Agent、1 Model、1 Provider 全部清理，remaining_new_ids 均为空，
没有驱动 failure。配置恢复/移除，Agent 日志导出后清理。只运行了一个 evidence stance Job，另一个 Job
是词法维护。新的修复方案仍需 Sir 复核，本轮没有追加修改或回滚已批准的语义定义。
