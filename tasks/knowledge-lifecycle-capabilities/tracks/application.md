# Application Track

## Objective

让用户或下游能力通过 info-base 有效找到、导航和使用信息。

## Known Capability Slices

- 特征检索
- 语义检索
- 图导航检索

## Design Card

每种检索依次说明：

1. 用户问题与查询输入；
2. 可检索对象和返回结果；
3. 消费 block content、raw、solved、relation 或 resolver projection 的方式；
4. 排序、过滤、路径、上下文与组合语义；
5. 所需索引或其他派生结构及其 owner；
6. core-py API 与 client-web 交互；
7. 精确性、质量、性能和失败验收；
8. 最小迭代与 Hub / 跨仓影响。

## Guardrails

- point lookup、storage raw fetch 与产品检索不能混称。
- indexing 是 application / retrieval 的实现支撑，不是 organization。
- sink 或 client 不接管 info-base 的 graph authority。

## Active Slice

当前没有 active application ownership unit。[Semantic retrieval](../units/semantic-retrieval/packet.md) 已完成。
[Mail extension](../units/mail-extension/packet.md) 可以因真实邮件 journey 推动必要的 basic use/query、semantic
retrieval 或 graph navigation 改进，但这些横向结果不自动关闭 feature/graph-navigation ownership units。
