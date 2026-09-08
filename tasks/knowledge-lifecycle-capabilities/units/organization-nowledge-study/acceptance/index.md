# 整组 Organization 能力的黑盒验收

- **状态**：D-524/D-525 accepted best-effort black-box Acceptance strategy and initial corpus。
- **权威分工**：[上层验收合同](../acceptance.md) 定义希望观察到的 Product 差别；本目录只描述一次 best-effort 黑盒
  观察，不承诺完备证明，也不为方便测试改变 Product/Technical design。

## 验收边界

```text
ordinary info-base inputs + deployment setup
  -> declared automatic Organization Jobs
     -> opaque system under test
        -> observable info-base graph / later-use reads
        -> Job lifecycle + diagnostic logs
           -> Human whole-run assessment + explicit residuals
```

验收驱动只允许：

1. 通过正常的 info-base/Source/Resolver 输入路径准备 realistic information；
2. 准备真实 provider、Agent definitions、`core.organization.<behavior>` configs 和调度所需的 deployment facts；
3. 从现有 Job/Cron 边界触发自动 Organization，不调用 BehaviorResolver 内部方法，也不提供 focal Block、pair、source set
   或未来 query；
4. 从正常 Block/Relation、Resolver、retrieval/Graph Navigation 和声明的 later-use 路径读取结果；
5. 读取 JobStatus 与日志来解释未运行、失败、unresolved/no-op，但不检查内部 Tool-call 顺序或 prompt reasoning。

数据库 fixture 可以作为隔离的环境准备手段，但不能直接写入本应由 Organization 产生的 relation、descriptor、candidate 或
derived result。Acceptance 也不为了获得纯 HTTP 黑盒而新增没有 Product 需求的管理 endpoint。

## 为什么撤回机制级 Acceptance

此前候选把 graph mutation、transaction、replay、config、Job、meta-tool、Extension 接线分别列成大量确定性 tests。这些
大多是 implementation facts：可由类型/schema、import direction、代码审查、现有 `pdm run check` 和少量真正有回归价值的
实现侧测试覆盖。逐项把它们升级成 Acceptance 会产生三个问题：

- 测试内部结构，而不是 organization 是否让 info-base 变得更可用；
- 鼓励为容易断言的机械形状优化设计；
- 以大量绿色小测试制造对强语义自动行为的虚假信心。

因此这些检查只进入 Implementation Plan / preflight / implementation verification；不构成 Acceptance evidence inventory。
只有某个机械缺陷能在黑盒旅程中产生可观察失败时，黑盒验收才通过最终效果覆盖它。

## Best-effort evidence law

本 unit 不声称从小 corpus 证明所有未来 information、provider 或模型上的可靠性，也不引入未经 Product 定义的成功率/SLO。
Acceptance 由 Human 对整轮结果作判断，并记录：

- 哪些预期可复用区别真实出现且可被后续读取使用；
- 哪些合理地 unresolved/no-op；
- 哪些有用关系被遗漏；
- 是否产生了危险的错误 authority，例如错误 supersession、虚假 referent、伪造共识或重复证据计数；
- 哪些失败来自 provider/config/runtime，而不是 semantic judgment；
- 仍无法覆盖的输入、Extension 和外部 Storage pointer residuals。

它不采用“七种 behavior 每个 case 必须机械通过”的完备门槛，也不用平均准确率掩盖严重错误。一次明显违反模型 authority
law 的 false positive 仍是 material evidence，Human 不能用更多低风险成功关系把它算术抵消。最终 disposition 是基于样本
的工程判断，而不是假装客观完备的分数。

## Human 看到什么

Human 只看：

- corpus 中原始 information 与 provenance context；
- Organization 前后的 Resolver-readable graph difference；
- current/history、source drill-down、referent reachability、duplicate count-once 等 use results；
- 与未发生/失败结果相关的 bounded Job/log diagnostics。

Human 不看 chain-of-thought，不按 Tool-call 数量评审，也不在产品运行中 approve/reject 某次 synthesis。这里的人审只属于
Acceptance evidence；它不引入 Human Organization lifecycle。

## 静态与实现侧检查的正确位置

以下仍可能是必要工程保障，但不是黑盒 Acceptance：

- Job 是否 import Agent/config、Resolver base 是否反向 import Organization；
- exact relation token、schema、config key 和 Pydantic bounds；
- Tool registry 数量、dynamic schema binding 和 Extension registration；
- transaction/cycle/replay 的针对性 regression tests；
- type/lint/migration/primary repository gate。

它们是否实施、实施多少，由 Implementation Plan 按真实回归风险与静态可证明性决定；不会从本文件生成“一项合同一个测试”
的机械清单。

## Requalification

当 Product model、behavior SOP、Agent Tool set、selected model、candidate heuristics、Resolver meaning 或 corpus 发生足以影响
结果的变化时，重新执行 whole-set black-box journey。纯重构只需通过实现侧检查，除非它触及上述黑盒连接。
