# Organization Track

## Objective

打理 info-base，使 use 的效果更好。

## Known Capability Slices

- breakdown
- merge
- linking

这些是当前已知能力，不是 organization 的完备定义。只有能说明怎样改善 use 的新能力，才可
进入讨论队列。

## Design Card

每项 organization 能力依次说明：

1. 用户问题与期望改善的 use；
2. 输入的 blocks / relations / raw / solved 表示；
3. 对 info-base 的可观察改变；
4. resolver、storage、LLM、extension 与人工判断的职责；
5. 正确性、不变量、失败和部分结果；
6. 自动化验收 fixture 与质量指标；
7. 最小迭代及与其他 organization 能力的关系；
8. Hub 与跨仓影响。

## Guardrails

- organization 不是 collection 的一部分。
- indexing 不属于 organization。
- 现有 `SourceBase._organize`、`BlockManager.organize` 和 resolver `breakdown` 不约束新设计。
- 不因为已知能力列表存在，就假定每个 organization 场景都必须归入其中之一。
