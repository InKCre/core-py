# 检索契约与最小充分引导复测

状态：D-553 实施后 guidance 初始世界执行及清理完成；21/21 自然结束，整组语义验收仍不通过。

## 运行与证据

- 源码 2dac3e1a409ce850a71692bbfa63eb4c9ac191f9；preview 34591473017、debug 34591471536 均成功。
- query 字段明确 lexical 要求全部查询词、semantic 按意义检索；两个实体读取工具解释 null 可能来自类型误选。
- 共享 prompt 按已有完整内容和信息缺口组织读取；专用 prompt 的“读取步骤”改为判断所需信息。
  rumination 明确围绕 focal Block，不改变产品职责，不禁止辅助探索。
- qwen3.6-plus，预算仍为 12，预算不进入提示词；语义 Profile 仍未配置。原初始 fixture、调度与 max_seeds=3
  不变，未新增测试。此轮仍未运行 upstream-change 阶段。
- 实际下发的 query schema 已从 thread.created 核验。完整提示词、工具、调用、图、清理见
  [tool-repair-guidance.json](tool-repair-guidance.json)。未覆盖混合类型读取或 null 纠错，不能声称提示效果已验证。

## 执行结果

| 行为 / Job | 模型调用次数 | 结果 |
| --- | --- | --- |
| rumination / 73 | 8、10、11 | 全部自然结束 |
| supersession / 74 | 5、7、6 | 全部自然结束 |
| refinement / 75 | 3、4、7 | 全部自然结束 |
| evidence stance / 76 | 2、7、2 | 全部自然结束 |
| synthesis / 77 | 6、5、3 | 全部自然结束 |
| existing-referent anchoring / 78 | 3、5、5 | 全部自然结束 |
| duplicate assertion / 79 | 3、8、3 | 全部自然结束 |

共 113 次模型调用、138 次工具调用，7/7 Job 完成，零预算耗尽、零工具错误、零顶层 null 回执。
不能由 is_error=false 推断没有语义误用。随机 seed 与前序图变化使此轮不是严格对照，尤其 evidence stance
没有重复上一轮的实验 seed，不能由 12→2/7/2 宣称同一困难已消除。

## 三个重点行为

### Rumination

- focal 273（五月事故）8 次结束；270（新闻副本）10 次结束；272（修订方案）11 次结束。
  首尾两个原始信息角色也出现在上一轮 rumination，对应 11→8、12→11；中间 seed 上轮是 Atlas 旧规则，
  本轮是新闻副本，不能直接比较。即使 seed 内容相同，工作结果和图仍不同。
- 14 次 retrieve 均有词法命中，未发生空查询；其中仍有长查询，命中自己/已知材料不等于增加有效信息。
- 首次输入已提供完整 focal 文本和空 direct_relations，调用 1 仍 get_raw_content/get_relations 并查邻域；
  之后扩展六月材料。第 7 次标记 refinement，第 8 次结束。无确认性复读，但前端信息复用问题未消失。
- 第三次先标记 supersession 候选，再标记自身 rumination 候选，之后创建方案差异说明。
  第 10 次写入、第 11 次结束；持续有效动作和冗余/语义错误必须分开看，不能只按完成状态评价。

### Evidence stance

- seed 259（rollout）、273（五月事故）、278（前序方案差异说明），三次均 no-op；没有被迫写 stance。
- 第二次在调用 2/3 并行查询，调用 3 使用 Nimbus，随后读时间线邻域；与上一轮直到调用 12 才查询 Nimbus
  的长空查询串不同。共 5 次 retrieve 均有命中，没有空查询链；但 seed 不同，不能推断单一因果。
- 273 的“六月事故不为五月事故提供证据”判断合理；但调用 1 又 get_entities 读取输入已有的 273，并并行
  查询也会返回它的邻域。允许 no-op 和减少步骤暗示没有充分解决已有内容复读。
- 对 278 的 no-op 把行为标识 relation 当作正确 refinement 关系理解，显示错误图语义可被下游宽容地继承。

### Anchoring

- seed 278、261（Atlas newsletter）、276（前序派生说明），与上一轮 248 不同。
- 各一次 retrieve，共 3 次，查询为 Nimbus remediation、Reliability Lab、Nimbus incident，均有命中。
  本轮没有无目标时长时间搜索的样本，不能证明那种 no-op 路径已改好。
- 278 中 revision 1/2 分别产生 mention Block 并锚定 271/272；261 中 the Reliability Lab result 锚定 260。
  是有具体价值的正确路径，且写后直接结束。
- 第三次 selected_text 为 Nimbus incident，但 276 正文没有这个连续片段，生成的 mention 不满足直接选取
  原文的要求。虽然上下文所指合理，仍不能因此忽略 source-grounded fragment 缺陷。

## 图语义评审

正面：272 supersedes 271 对应批准方案替代；259 refines 256 保留 rollout 限定；285 综合旧规则、新公告与
rollout 条件，保留 legacy tenants 迁移前 30 的例外；287 综合区分团队观察、假说、实验与未决根因，并保留来源。

残余：

- 273 candidate for refinement 的依据是将五月、六月独立事故联系起来，而不是同一演进主题的信息增量。
- 276 将“新闻没有独立 reproduction”扩成“没有独立 experiment 或 investigation”，强于原文；refines 关系
  也不能自动证明其内容可靠或带来非冗余增量。
- 278 称 replay gating 为 Preserved condition，同时注明 revision 1 未明确此条件，表述不一致。
- Relation 250/251 content 是 core.organization.behavior.refinement.v1，误将行为标识作为语义关系名称；
  没有采用已确定的 refines。此处是具体写入语义误用，不据此引入 registry 或限制任意 graph 写入。
- 272 被当前 rumination 再次标记 rumination candidate，并继续直接产出；其价值需审查，不能因不会立即执行
  就假定不存在重复工作的可能。
- Anchoring 的非原文 selected_text 缺陷见上。

因此：本轮没有重现预算耗尽，但组织结果仍有缺陷。检索契约/最小充分引导方向有局部正面证据，不能宣布
重复读取、候选质量、关系语义或无目标搜索已解决。任何后续修复继续先经 Sir 复核。

## 清理

最终图为 33 Blocks、32 Relations。驱动已恢复/移除临时配置，导出后清理日志，移除本轮 33 Blocks、
32 Relations、8 Jobs、7 Agents、1 Model、1 Provider。所有 remaining_new_ids 为空，无 failure。
