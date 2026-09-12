# 逐项类型引用与无需确认指导复测

状态：D-552 已实现、提交、部署并完成初始世界复测，临时数据已清理。局部交互有正面证据，整组验收仍不通过。

## 运行边界

- 代码：`f4362add582151df7de08d7a1aae77a3f83e1631`。Preview：34563263424 成功；debug：34563262293 成功。
- get_entities 接收 entities: `{type, id}[]`，共享提示词告诫成功回执无需确认，候选标记不执行行为。
  删除 rumination 旧复读例外句；未增加回执内容或 runtime 约束。
- Qwen3.6-plus、12 次预算、初始 fixture、前三种顺序/后四种独立入队方式不变；预算不进入提示词。
  未新增测试，未运行 upstream-change 阶段。随机候选和前序图变化仍使逐 seed 对照不严格。
- 原始工具 schema、提示词、轨迹、图与清理结果：[tool-repair-references.json](tool-repair-references.json)。

## 结果

| 行为 / Job | 模型调用次数 | 结果 |
| --- | --- | --- |
| rumination / 65 | 11、10、12 | 第三次预算耗尽 |
| supersession / 66 | 6、2、3 | 全部自然结束 |
| refinement / 67 | 6、8、4 | 全部自然结束 |
| evidence stance / 68 | 12 | 首次预算耗尽 |
| synthesis / 69 | 11、10、3 | 全部自然结束 |
| existing-referent anchoring / 70 | 12 | 首次预算耗尽 |
| duplicate assertion / 71 | 2、2、3 | 全部自然结束 |

17 次执行：14 次自然结束、3 次预算耗尽。117 次模型调用、126 次工具调用；4/7 Job 完成。
2 次工具错误均在 draft_graph，get_entities 和 Resolver 子项未观察到错误。

## 本次修改的直接证据

- 12 次 get_entities 调用全部采用逐项 type/id，均成功，包含多个 Block 的批量读取。
  未覆盖混合 Block/Relation 或随机读取，不为补覆盖新增测试，不能声称这些分支已由真实模型验证。
- 5 次有写入并自然结束的执行，在最后一次写入后直接结束，没有再发起工具调用。
- Rumination 第一次第 9 次 submit_graph、第 10 次标记候选、第 11 次结束，没有读取回执 ID。
- 第二次第 2 次标记候选后继续检索 Atlas 并构造派生信息；后续读的是美国/欧洲原有材料，不是为了核对
  返回的 descriptor 或 candidate Relation。最后第 9 次写入，第 10 次结束。允许独立语义工作的原则未被
  改成“首个写入即强制停止”。
- 与上一轮相同原始信息角色的第三次 focal 是批准的 Nimbus 修订方案 241：前 9 次调查上下文，
  第 10、11 次分别写关系，第 12 次标记 evidence stance 候选，随后到达调用上限。没有重现回执 ID 类型误用
  和多轮确认。但最后一次回执之后已经没有剩余调用机会，不能用这个尾部证明模型本来会自然结束。

这些观察支持改动减少了本轮确认性复读，但不证明未来不会再发生，也不能证明整体效率改善。
尤其 supersession/duplicate assertion 本轮没有新增对应关系，正常结束不能当成发现覆盖充分。

## 剩余失败与语义

- Rumination 的前两次各有一次 draft_graph 参数误用：一次把完整 blocks/relations 图当作文本 Resolver 输入，
  一次传 content 而不是 text。均在后续纠正，不属于本次 entities 输入错误。没有在运行中追加修复。
- Rumination 第三次没有参数错误或确认性复读，仍耗尽；evidence stance、anchoring 也在检索/读取中耗尽。
  因此不能继续将这些耗尽全部解释为回执确认问题，也不应未经评审提高预算或删掉探索能力。
- 派生 Block 248 将欧洲 50 并发描述为 current effective limit，只依赖 225/226，没有保留 228 的迁移例外；
  后续综合 255 虽正确保留迁移差别，也不会自动修正已存在的 248。
- Rumination 从 242 提取了 244、245，并生成对六月事故的描述 246，但这些新 Block 没有来源边连回 242。
  245 的文本提到原 postmortem，并不补足缺失的可导航来源关系。
- `242 candidate for supersession` 把五月独立事故送往替代行为，缺少同一演进主题的依据，仍是候选选择残余。
- `241 supersedes 240` 正确衔接方案修订；综合 254 保留两个事故的区别与六月事件时间点，综合 255 保留
  rollout 条件、Lab 未测试 legacy tenants 与客户观察，且未把 newsletter 副本列为独立实验来源。
- `245 refines 244` 将事故排除范围补充到摘录事实；它的语义价值与来源缺陷分开评审，不因写入成功自动通过。

## 清理和交接

最终图 31 个 Block、24 条 Relation。已移除本轮 31 个 Block、24 条 Relation、8 个 Job、7 个 Agent、
1 个模型、1 个 Provider；恢复/移除临时配置，日志导出后清理。所有 remaining_new_ids 为空。
此处记录实现效果，不新增修复授权；若继续调整草稿界面、探索/结束方式或预算，须先与 Sir 复核具体方案。
