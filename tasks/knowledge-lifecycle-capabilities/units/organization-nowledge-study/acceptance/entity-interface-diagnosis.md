# 实体类型误用：界面组合诊断

**D-551 纠正**：Sir 已否决为了确认而返回完整 Relation；成功回执后没有必要再核对写入。
读取接口确认采用逐项 `{type, id}[]`，而非下文原提案的两组 ID 数组。下文保留诊断与被撤回提案的沿革，
不代表已批准设计。实际提示词已有“不要常规复读；具体语义/身份疑问除外”，不能声称此前完全未告诫。
下一步提示词应明确成功回执足以确认该次操作；不要为确认写入再读取返回 ID，不把这种复读当作独立探索需要。

状态：诊断与待评审方向，不是已批准修复；未改代码、未运行新验收。
依据：array 轮 Job 57，Thread c5805dc5-913e-4518-9665-3a432dfc4aae，完整轨迹见 tool-repair-array.json。

## 实际发生的两种错误

| 调用 | 输入/反馈 | 可确认事实 |
| --- | --- | --- |
| 4 | record_candidate 返回 descriptor_block_id=218、relation_id=202、created=true | 写的是 212 --candidate for--> 218 |
| 5 | get_entities(entity_type=block, entity_ids=[218,202]) | 显式把 Relation 202 当 Block 读取，命中无关 Atlas Block 202 |
| 7 | 读取 Block 212 邻域，得到完整 candidate for Relation 202 | 此时图事实已展示 |
| 8 | 响应文字仍称已建立 supersession，并查 Relation 218 | 又把 descriptor 的 Block ID 当 Relation ID；同时混淆候选与执行 |
| 9 | 查 Relation 202 | 正确返回 candidate for 和两端点；之后继续扩展到事故上下文 |

第 5 次明确提供 entity_type=block，不是遗漏类型被默认值误导。第 8 次也显式选 relation，
所以仅取消默认值不能解决本例。工具按所声明类型读取的行为正确，且存在同号 Block，不能靠存在性发现意图错误。

## 界面的具体负担

1. **类型只在上一工具的字段名中，后继调用要重新编码。** CandidateWriteResult 是两个类型不同的 ID；
   get_entities 却只接受一个全批次 entity_type 与通用 entity_ids，混合结果无法原样分组读取，
   调用者要拆分、分类并改写字段。get_entity_neighborhood 也要求再次将类型名与裸整数配对。
   局部字段命名正确，不代表跨工具接口可组合；这是对上一轮“名称已明确”的补充纠正。
2. **结果是持久化回执，不是直接展示的图效果。** 候选工具已经有简短的“不执行 behavior”说明，
   所以不是完全缺少定义；但返回值只含 ID/created，没有 content/from_/to_。模型需要额外读取才能看到
   写入的确实是 candidate for 而不是 supersedes。这个省略降低响应大小，却增加理解和核对成本。
3. **错误意图可以得到合法成功响应。** 选错类型但同号实体存在时，普通 CRUD 无法知道调用者本意。
   这是错误传播的条件，不是应引入全局 ID、跨类型自动纠错或数据库验证层的证据。

## 因果边界

一次轨迹证明发生了实体类型误用和操作含义误读，也足以指出界面转换负担；不能证明某个界面变化必然消灭错误。
尤其第 7 次已展示完整关系，模型第 8 次仍误解，故完整结果也不是充分条件。不能把所有后续查询归因于 ID 混淆：
第 4 次响应已经另提出寻找方案的问题背景，后续探索另有独立动机。

## 建议讨论的方向（未获批）

- 读取仍保留一个工具，但用 block_ids、relation_ids 两个普通数组承接各自命名空间，允许同批读取；
  返回按 blocks、relations 分组的原生实体，而不是新建 information 包装。随机语义和缺失位置另行明确，
  不为本例仓促修改全部查询工具。
- 候选写入优先返回实际写入的普通 Relation（含 id/from_/to_/content），而不只返回两个 ID 的回执。
  它显示的是实际图事实，不是下一步请求，也不是 behavior report。是否保留 created、descriptor 返回值
  应按真实调用需求决定，不能无依据把所有写工具一起改造。
- 先评审类型传递与结果语义这两个界面问题，不先加长 system prompt，不新增 registry、runtime enforcement、
  全局 ID 编码或字符串解析，不增加测试。
