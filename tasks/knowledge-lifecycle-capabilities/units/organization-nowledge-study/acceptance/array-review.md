# 普通数组 schema 重验

结论：D-550 的工具修复已获得真实运行证据；整组 organization 仍未通过验收。
上一轮 21 次指定 ID 读取全部因字符串数组失败，本轮 15 次指定 ID 读取全部成功，一次随机批量也成功。
没有新增容错解析或修改 SOP；预算耗尽仍出现在 rumination、refinement、anchoring。

## 版本与范围

- 服务版本 `9a7ab937c7cdf742a8cc9c26f42b8979040e141d`；preview 34557205312、debug 34557207370 成功。
- 只修改 entity_ids 的 array/null 联合字段为普通数组，默认空数组表示随机读取；其余代码、定义、模型和
  预算沿用上一轮。Qwen3.6-plus，每次执行 12 次模型调用，数值不进入提示词。
- 同一既有初始世界，前三种行为顺序、其余四种独立入队；未跑 upstream-change 阶段，没有新增测试。
- 原始定义、schema、完整图与轨迹：[tool-repair-array.json](tool-repair-array.json)。对照见
  [batch-review.md](batch-review.md)。前序图、随机候选及模型输出会改变后续输入，并非严格逐 seed 对照。
- 一次旁路只读进度查询发生 TLS EOF；主驱动正常完成，没有重发创建请求或恢复中断运行。

## 结果

| 行为 / Job | 模型调用次数 | 结果 |
| --- | --- | --- |
| rumination / 57 | 7、9、12 | 第三次预算耗尽 |
| supersession / 58 | 7、3、3 | 全部自然结束 |
| refinement / 59 | 4、12 | 第二次预算耗尽 |
| evidence stance / 60 | 3、9、3 | 全部自然结束 |
| synthesis / 61 | 7、6、5 | 全部自然结束 |
| existing-referent anchoring / 62 | 12 | 首次预算耗尽 |
| duplicate assertion / 63 | 2、5、2 | 全部自然结束 |

18 次执行：15 次自然结束、3 次预算耗尽；111 次模型请求、129 次工具请求，整体及 Resolver 子项均无调用错误。
4/7 Job 完成。工具错误消失不等于行为完成率提高，不据此宣称整体优化成功。

## 工具修复证据与边界

15 次指定 ID 请求都使用 JSON 数组，包含多 ID 读取，且没有字符串兼容处理。一次请求省略 entity_ids、
指定 random_count=10，成功返回 10 个不同 Block，覆盖默认空数组的随机分支。
未观察到 Relation 批量请求或显式空数组请求；不补新测试来制造覆盖，保持 best-effort。

这显著支持上一轮 schema 形状是调用失败来源的推断；仍不宣称知道模型服务内部如何推断字段类型。
此修复没有更改 Pydantic 错误术语；如果未来仍出现错误输入，内部 tuple 术语的可理解性仍是已知残余。

## 剩余预算问题：成功调用之后的语义决策

### Rumination 57 第三次

Focal 212 为批准的修订方案。第 4 次标记 supersession 候选，工具准确返回
descriptor_block_id=218、relation_id=202。第 5 次却把二者都按 Block 读取，取到了不相关的 Atlas Block 202。
第 6–9 次反复核对邻域、尝试 Relation 218（不存在）、最终读取真正的 Relation 202；第 10–12 次继续
检索 Nimbus 并读取事故邻域，随后耗尽。

本次工具零错误，但实体类型使用错误产生了无益绕行。写入反馈已经使用明确的实体类型字段名，不能据此
断言必须再包装 Block/Relation、增设运行时约束或扩大 description。第 4 次已完成候选转交，仍未自然收尾；
不向模型公开预算、不提高预算来掩盖问题。后续方案需要重新复核，不在本轮追加。

### Refinement 59 第二次

Focal 209 是 Lab 重放，邻居 210 是转述副本。第 1–3 次读二者、邻域并检索；第 4 次随机读 10 个 Block；
第 5–10 次读假设、时间线、团队材料、行为 descriptor 与其邻域；第 11–12 次再次检索并读取另一方案。
全程无写入、无调用错误，最终耗尽。前一次正常 no-op 不能证明退出行为稳定；也不能在未观察到结束文本的
执行中把“模型认为必须找到结果”当作已证实的内部心理。可确认的是搜索扩展没有落实为 no-op 退出。

### Anchoring 62

Focal 215 是从五月事故提取的事实。反复搜索 Nimbus 产品/应用名称后，第 10 次标记 synthesis 候选；
第 11 次复读 descriptor，第 12 次又读取六月事故邻域，随后耗尽。与 rumination 一样出现候选标记后的复读
和扩展；是否改变公共指导、行为 SOP 或工具组合仍属于需要确认的新修复设计。

## 图语义复核

- `215 extracted-finding-from 213` 保留摘录来源，未将纯摘录当 refines；`212 supersedes 211` 正确衔接方案。
- Synthesis 224 清楚指出 Lab 是唯一技术来源、新闻转述不是独立佐证；223 保留两版方案及上线前置条件。
- Synthesis 222 先保留团队 attribution 和假设限定，末段却将 network team 的“disputes”强化为“excludes”，
  并将两个团队的观点概括为共同认定 retry amplification 是 contributing factor；结尾语气仍比来源强。
- `196 challenges 197` 再次把新版并发限制与旧版当作证据反驳，没有充分区别适用版本演进；不能验收通过。
- 本轮没有新增 refines、refers to 或 duplicates assertion；不能将正常结束或不写错误关系视为发现覆盖充分。

## 清理与下一步

最终图 29 个 Block、22 条 Relation。已清理 29 个 Block、22 条 Relation、8 个 Job、7 个 Agent、1 个模型和
1 个 Provider，恢复或移除临时配置，相关日志导出后移除；所有 remaining_new_ids 为空。运行记录保留图、定义和日志。
本次接受的 schema 修复已实现、提交并重验；剩余行为修复不自动获批。先依据上述具体绕行与扩展，重新评审
候选处理完成后的退出指导，不预设删除探索能力、增加预算或强制首个写入后结束。
