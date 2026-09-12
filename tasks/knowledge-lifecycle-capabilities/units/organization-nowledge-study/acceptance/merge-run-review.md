# 合并复审整组运行

2026-09-13（Asia/Shanghai），应用和 Agent definition 均来自 `4a0f26644df6a2071454b8d5cd159db0dbafbd1a`。
原始持久证据为 [tool-repair-merge.json](tool-repair-merge.json)。本轮没有修改提示词、工具组合或预算，也没有新增测试。
模型为 qwen3.6-plus，每个 Turn 仍为 12 次模型调用；七个 Job 均为 max_seeds=3、timeout_seconds=900。

## 运行结果与证据边界

复用两个初始信息世界，18 个 Block、6 条关系；维护词法索引后，前三种行为依次运行，后四种行为独立排队。
Job 101–107 全部 finished；最终为 39 个 Block、27 条关系，其中新增的 21 个 Block 包括 7 个 descriptor。
没有本轮驱动失败或 Job failed/timed_out。下表耗时由 Job 的 started_at / closed_at 计算，包含模型和数据库等待，
不是模型推理耗时。

| 行为 | Job | 耗时（约） |
| --- | --- | --- |
| rumination | 101 | 4 分 56 秒 |
| supersession | 102 | 3 分 5 秒 |
| refinement | 103 | 5 分 46 秒 |
| evidence stance | 104 | 7 分 18 秒 |
| synthesis | 105 | 6 分 30 秒 |
| existing-referent anchoring | 106 | 5 分 18 秒 |
| duplicate assertion | 107 | 4 分 11 秒 |

Preview 部署保留 logging backend=none，本轮逐次 Agent events 均为空。D-519 现在允许候选局部失败后继续，
所以七个 finished **不能证明每个 seed 正常完成、没有耗尽预算，或动态命中了并验证了局部失败继续分支**。
本轮没有重建已移除的 PR 专用调试设施。

一次独立状态查询遇到 PostgREST 503，正文为 `prepared statement name is already in use`；随后状态查询和
Core `/livez` 均恢复正常。该环境异常单独保留，不把它和更早的长链读取故障认定为同一个根因。

## 图语义评审

**可用结果。** Synthesis 1551 对比新版与旧版修复机制，保留 1529、1540、1541、1542 四个来源 Block 的
synthesis 关系，形成可直接使用的比较文本。它没有把这些来源宣称为四份独立实验。1518/1519 的重复关系连接
Lab 测量和引用该测量的 newsletter，具有避免同源传播重复计数的价值；仍应保留原始信息中的样本与范围细节。

**明确的误判。** 1530 是包含机制、批准和上线条件的完整 revision 2 提案；1544 只表示其 rollout begins。
`1530 --duplicates assertion--> 1544` 将完整提案与局部陈述当成 whole-Block 重复断言，不符合定义。
`1531 --supports--> 1535` 则把原事故说明与其“两个事故分开”的派生重述记为证据支持，没有提供超出重述的理由。
这不能视为 D-557 的同源 stance 问题已经解决。

**需保留上下文的结果。** Supersession 1384 的 successor 是标题 Block 1540，predecessor 是旧完整提案 1529。
1540 通过 status、specified change 以及 rollout 路径携带附加语义；不能仅因标题文本短，就认定这个图表达无效。
但它没有连接回原始新版提案 1530，且 core.text.v1 的 get_text 本身不会展开这些关系。读取 current 时能否恢复
完整 scope 和来源，仍需组合图查询；本轮不能宣称已验证这种承接完整性。

Anchoring 写出 `1543 --has mention--> 1552 --refers to--> 1530`，selected text 为 production-scale replay passes，
target 却是整个新版提案。条件与方案的语义角色存在错配风险，不能仅以二者相关就判为正确锚定。

**遗漏与粒度残余。** Rumination 形成了 1536/1538、1537/1539 两组近似重复表达；若只读取 1543/1544 的文字，
也容易丢失其通过 prerequisite for 表达的条件关系。没有 refines、candidate for 或 edited 产出；无逐次日志，
不能将它们一律解释为主动 no-op。Atlas 旧新限制替代、更多独立证据以及上游修改后的 synthesis 更新仍未覆盖。

以上是完整最终图的 best-effort 评审，不是逐项必达的工具调用清单，也不构成新增修复授权。现有结果表明运行可结束，
但不能声明整组语义验收通过。此轮没有改变模型后再挑选成功输出。

## 清理与交付

七个行为配置恢复原状；本轮创建的 27 条 Relation、39 个 Block、8 个 Job、7 个 Agent、1 个模型和 1 个 Provider
均已删除，各表 remaining_new_ids 为空。长链探查创建的两组图和 MCP Sinks 已在本轮开始前清理，没有混入该语料。
没有删除其它运行的数据，没有修改数据库角色/schema，也没有停止 WSL 开发数据库。

本轮仅覆盖初始世界的一轮自动运行，不补足完整 upstream edited → synthesis 新版本闭环、语义检索 Profile、
其它模型/语言或 Extension 自有行为的证据。PR 的当前确定性阻塞仍见 [长链读取复验](lineage-read-review.md)。
