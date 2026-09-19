# Organization 交付后的 Hub 待提升项

状态：待 owner reconciliation，尚未执行 Hub 修改或发布。本文件只维护提升范围与证据入口，不复制一套产品设计。
[Unit](../units/organization-nowledge-study/packet.md) 已依 D-562 生产交付 Core 0.2.0；
[生产回执](../units/organization-nowledge-study/production-delivery.md) 不代表 Hub 内容已同步。
Parent 保留此项，不默认让下一 unit 承担，也不为此重新打开已关闭的实现。

## 已有依据与目标 owner

| 责任 | 待核对的稳定结论 | 目标文档 |
| --- | --- | --- |
| Product | 中立的 information 模型；Organization 自动形成有望改善未来 use 的可复用区别，不以特定已知查询、用户指定主题或结构美观为前提。信息可具有多种演进性质、参与多个模型；不同组织行为并行成立，无统一方法。 | [Capabilities](../../../docs/_shared/10-prd/behavior/capabilities.md)、[Rules and invariants](../../../docs/_shared/10-prd/behavior/rules-and-invariants.md) |
| 跨单元技术合同 | 普通 Block/Relation 是图权威；Resolver 承载异构解释与具体行为，Agent/runtime/tools 和 Job 是执行载体；检索和图导航保持各自职责。关系内容由写方拥有，不建立 registry；Extension 复用 Resolver contribution 扩展。 | [Knowledge capability contract](../../../docs/_shared/20-product-tdd/knowledge-capability-contract.md) |
| 已有 rumination 合同 | 保持 focal-Block 产品行为，同时核对新的 Resolver 载体、显式与自动入口、完整直接邻接输入；不把旧 MVP 的实现限制继续写成通用合同。 | [Semantic retrieval and Peer capabilities](../../../docs/_shared/20-product-tdd/semantic-retrieval-and-peer-capabilities.md) |
| Claim 与证据 | 从仅有显式 rumination/media 的 realization 更新为整组已实现行为，同时保留实际语义误判、不可观测和未覆盖输入；Job finished 与生产成功均不是语义全对。 | [Claim realization matrix](../../../docs/_shared/20-product-tdd/claim-realization-matrix.md) |

当前跨单元文档仍将 rumination 写为仅显式请求、bounded snapshot，并保留无 periodic scan 的旧 MVP 边界。
这与本次交付的自动 Job 和 focal 上下文合同需要逐项 reconcile，不是简单追加一个 Organization 功能清单。
本地类名、配置键和具体工具参数继续由 [core-py Organization TDD](../../../docs/30-unit-tdd/organization.md)
拥有；不能因为已实现就全部提升成跨单元规范。

## 提升前必须保持的区别

- 学习来源不是实现权威。[Product 研究稿](../units/organization-nowledge-study/product-design.md) 保留了 Nowledge
  的 default recall、confidence 等状态描述；后续决定没有建立全局 latest/隐藏策略，也没有引入 Memory ontology。
  `read_lineage` 是有范围的显式读取，不是整个图的 currentness authority。
- Synthesis 保留来源、分歧、不确定性和说话者归属，是产品目标与判断依据，不是模型已能保证不出错。
  [合并前复审](../units/organization-nowledge-study/merge-review.md) 和整组验收保留真实残余。
- “Relation 可传导力”仍是研究线索，不是已交付的通用 cascade engine；证据缺失评估也没有成为通用状态。
  两项继续由 [P-031/P-032](../pressure-ledger.md) 保留。
- Domain vocabulary、新 Entity materialization、Human synthesis review 等延后或未采纳方案，不因整理文档而复活。
  [Transfer audit](../units/organization-nowledge-study/audit/nowledge-transfer-audit.md) 负责保留/降级/拒绝的依据。
- [Agent Tool 通用模式](../common-patterns/agent-tools.md) 是已确认的 task-level 指导；需单独核对适用范围与文档 owner，
  不将本 unit 的具体工具组合推广成统一 Agent/Organization 流水线。

## 执行边界

后续提升先恢复最新 decision、[glossary](../units/organization-nowledge-study/glossary.md)、
[representation lens](../units/organization-nowledge-study/representation-lens.md) 和实际实现，再写出精确的
`From → To` 及影响范围。不直接复制历史研究稿或整个 task packet。

本条目不是 Hub mutation 授权。实际执行时使用 shared-doc skill，从 Hub source 修改和发布开始，然后独立更新
Spoke ref；不得从本仓直接编辑 `docs/_shared`，也不把 Hub 修改、ref bump 和本地文档混入一个提交。
