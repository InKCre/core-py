# Rumination / refinement 预算耗尽诊断与处理

当前有效方案另见 D-546：rumination 按复核方案修改；refinement 仅新增批量独立检索与无需找到 refinement
即可 no-op 结束的指导。已更新本地定义输入，未重新运行。以下停止记录和被撤回方案仅保留历史事实。

状态：**已停止并撤回修复方案（D-545）**。Sir 指出具体方案未经确认，且禁止让 LLM 知道预算。
下列诊断保留；“本轮最小处理”仅是被撤回的历史提案，不是获批设计。验收驱动已终止，不再继续运行。
新改的两份 SOP、预算数值注入和构造逻辑已撤回；后续必须先复核具体方案。
停止确认：本地驱动已终止；远端仅创建了 45、46、47，均已自然结束，无本轮 pending/running Job。
临时 Agent 定义已恢复为此前 SOP 并移除预算提及，现场数据保留，不再继续此运行。

## 已观察到的链路

证据来自 tool-repair-prompt.json，均无调用合同错误。

- Rumination 38 的耗尽执行以 129 为 focal。第 4 次标记 128 为 supersession 候选；第 5 次读取返回的 descriptor
  与 Relation，第 6 次取 draft schema，第 7 次使用 relation-only submit 自己写 supersedes，第 8 次复读确认。
  第 9 次转为广泛 Nimbus 检索，后续扩展事故上下文，第 12 次仍写 responds to。候选并非未写成功，后续动作也
  不能一概判为无价值；问题是转交/直接实现的取舍和一次工作何时结束不清楚，实际工作范围持续增长。
- Refinement 40 的耗尽执行以 135 为 seed。第 1 次重复读取已提供的文本及 solved content；四次词法查询全空。
  后续把 responds to、supersedes、candidate for、refines 混在一起查连通分量，并随机取另一 Block。
  它没有找到可落地的 refinement，也没有结束当前比较。
- LexicalRetrievalManager 使用完整词串 substring 或 plainto_tsquery(simple) 匹配；term 分支要求全部词项。
  长语义问题不等于良好的词法查询。新 Block 也可能尚无检索记录，不能用反复检索确认已读内容是否存在。
- AgentManager 将预算保存在 ThreadState 中；Thread 只把 messages、tools、tool_choice 发给模型。现有 system
  prompt 没有实际额度，所以不能假定模型知道第 12 次会被停止。这是初始额度不可见，不等于缺少动态剩余额度
  一定导致每一次失败。

这些证据不支持直接定性为相同请求的死循环，也不足以证明所有正常工作必然需要更高预算。

## 被撤回的处理方案（不得继续实施）

- 仅重写 rumination/refinement 的行为 SOP，其它五份 SOP、common prompt、工具列表和服务端代码保持不变。
- 在这两份定义中显示实际 model-response allowance，包括无工具的结束响应；数值从定义输入的
  max_model_calls_per_turn 渲染，并用于同一次部署的 Agent 配置，当前仍为 12。
- 明确当前 focal 工作与具体后续线索的关系；候选转交可作为该子问题的处理结果，不等待它同步完成。
  已提供的内容不作仪式性复读；relation-only 写入不需要新 Block 的 draft schema。
- Refinement 按新增含义和演进角色找比较对象；空词法结果改用合适锚点或已知 ID/关系，不反复改写长问题。
  连接关系必须服务于具体判断，不能把工作流/来源/演进混合连通当成同一演进主题。
- 不删除随机读取或图查询工具，不强制固定搜索次数/第一次写入后停止，不新增过程报告或完成标记。

## 被停止的验收

复用完整初始信息世界及七个自动行为，mode=closure；模型、12 次预算、自动 seed 规则与调度方式保持不变。
对照为上轮 prompt 的完整结果，服务代码同为 6ac43f0。不同前序图结果仍会影响后续 seeds。
不新增回归或聚焦测试，不仅按 Job 完成率判断效果。实际定义、轨迹和清理结果保存为 tool-repair-closure.json。
该文件只保留未经批准运行的现场，不能作为方案已获批准或效果已验收的依据。
