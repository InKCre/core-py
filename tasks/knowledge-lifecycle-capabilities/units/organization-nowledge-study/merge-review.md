# PR #100 合并前复审

2026-09-12，审查基线为 `a3eaff20d720a73e31a7c2b22a65881340c98dcf`。本轮由 Sir 要求重新审查整个 unit，
为 PR #100 合并作准备；不执行合并，不新增回归或聚焦测试，新修复方案仍先复核。

## 结论与阻塞

运行拓扑符合已确认设计，但发现一个应在合并前修复的确定性缺陷：
`SupersessionBehaviorResolver.read_lineage()` 的默认探索上限为 1000 个 Block，最终却使用递归 DFS 检测环。
一条合法的 1000 节点无环链在 `_cycle_detected()` 中触发 `RecursionError`，无法返回 current/history 投影。
同一实现的 100 和 400 节点输入正常返回 false。复现只创建内存 RelationModel，使用不可连接的本地数据库
占位配置，没有访问数据库、调用模型或新增测试文件。

D-560 中 Sir 已同意修复。环检测现改为标准库 TopologicalSorter 的显式栈实现，保持接口、探索上限、方向
和环判定含义不变；不提高 Python 递归上限，不改变图模型。本地一次性检查的 100/400/1000/10000 节点链
及其闭环均得到正确结果，静态检查通过；Preview 读取及当前整组运行正在准备，尚不宣告动态验收通过。

复审发现的另一项历史合同差距：D-519 要求候选局部失败不丢弃其它 seeds，原六种探索行为的
`run_automatic()` 直接等待 `build_seed_message()` 和 `run_configured_agent()`。一个 seed 在选择后消失，
或一个 Turn 耗尽预算，会结束整个 Job，后续 seeds 未处理；此前真实验收已观察到后一种情况。
Rumination 原先仅单独容忍 seed_missing。Sir 随后在 D-559 同意落实：七种自动行为对候选缺失和单次预算
耗尽记 recoverable_failure 日志并继续；配置、数据库、provider、其它执行异常和取消仍传播。显式 focal
rumination 的错误行为不变。已提交的图效果保留，正常遍历结束的 Job 可以 finished，但不说明每个 seed
成功或图语义正确。实现使用私有异常边界，无 broad catch、重试、新状态或报告。
本次 format/lint/typecheck、foundation、静态审查、既有测试（14 passed / 53 skipped）及 diff 检查通过；
七处自动边界与显式调用链已逐项审阅。没有新增测试或重新运行真实模型，不声称该异常路径已有新的远端证据。

### read_lineage 的定位

该读取合同记录在 D-506，具体放置由 D-520 确认为 SupersessionBehaviorResolver.read_lineage，而不是通用
Resolver base。它从一个 focal Block 沿已有 supersedes 关系取得有界子图，解释仍未被后继替代的前沿，
并报告环和截断。它没有新的 HTTP endpoint 或专用 Agent Tool，可通过既有 Resolver 方法发现/调用访问。
例如 C supersedes B、B supersedes A 时，完整无环结果的前沿是 C，A/B 仍在返回历史中；它不判定图上
替代关系是否语义正确、不按时间戳选择“最新”、不隐藏检索结果，也不是第八种 Organization 行为。
Sir 先要求解释这个方法，随后在 D-560 同意修复其长链算法。

## 已核对的设计与实现

- 七种独立行为由 concrete BehaviorResolver 承载；Job 不依赖 Agent Thread，没有 Evolution umbrella Job、
  BehaviorReport、第二个 behavior registry 或 ExecutionAdapter。
- descriptor 是通过对应 Resolver 惰性取得的普通 Block；单一 candidate 工具从注册的 Resolver 发现能力。
- 精确写入落在行为 Resolver，调用者传入的 session 不被 helper 提交；默认自有短事务保留完整写入。
  开放世界的语义判断不伪装为数据库验证。无环与相反 stance 检查仅针对当前可见图，不承诺全局并发约束。
- Resolver reflection 已移到 ResolverManager；MCP 和内部 Agent 分别适配，没有 Organization 对 MCP 的依赖。
  实体批量读取保留逐项类型；图查询为三个稳定的直接工具；成功写入不要求复读确认。
- Rumination 的 focal 内容与 direct-relation 构造保留原有行为，所附 definition 仅绑定三个草稿/提交工具。
- 开发追踪默认关闭，使用既有日志后端，不新增执行持久化或恢复 authority。本文不把日志开关视为数据脱敏承诺。
- 本 PR 没有 schema migration、新依赖、默认 Agent/config/schedule 或 shared Hub 文件修改。

## 交付整理

按照既有 implementation-evidence 的合并前清理边界，移除仅服务 PR #100 的
`.github/workflows/preview-agent-debug.yml` 和 `scripts/preview_agent_debug.py`。它们可从 Git 历史恢复。
通用 `OBSRV__AGENT_DEBUG` 能力和操作文档保留；后续 preview 部署不再由本分支自动重新开启调试。
未删除任务证据、信息世界 fixture 或其它 session 的文件。

修正本地 Organization TDD、parent/unit 入口和 PR 描述中的旧工具组合及“尚未进行真实验收”等过期状态。
历史验收不重写，最新证据以 unit packet 路由。Unit 和 parent task 均不因 PR 准备而自动关闭，Hub promotion
仍是独立 owner 流程。

## 验证

审查基线包含最新 origin/main，差异为 0 个落后提交、24 个分支提交。GitHub 显示 MERGEABLE/CLEAN，
三个 required checks 均成功，strict latest-base 开启，没有未解决 review threads。

本轮运行了既有检查，没有创建测试：

- `pdm run check:foundation` 通过；
- format/lint 排除未跟踪的 `.agents/skills/python-backend-code` 后通过；
- typecheck 为 0 diagnostics；
- 既有测试为 14 passed、53 skipped，没有向共享数据库运行数据库破坏性测试；
- backend 技能的静态审查为 0 errors / 0 warnings；
- `git diff --check` 通过。

这些检查不能证明语义质量，也没有覆盖尚待确认的修复。

## 语义质量及尚未覆盖的范围

最新整组初始世界证据是 [discovery 轮](acceptance/discovery-review.md)：6/7 Job、19/20 次执行自然结束。
Refinement 仍有无产出耗尽；技术摘要被用来替代完整旧提案、来源重述被写成支持关系等误判仍可见。
最新 evidence stance 专项是 [stance-role 轮](acceptance/stance-role-review.md)：5/4/4 次调用，零错误/耗尽；
技术摘要正确 no-op，但 rollout 条件仍被原方案错误 supports。不能把三次自然结束写成语义验收通过。

Sir 已接受部分派生内容不准确的 best-effort 残余；这不自动说明其它错误关系符合定义。现有证据支持按需配置、
可扩展的能力实现，不支持默认自动启用或“可靠替用户维护正确知识”的宣传。当前 PR 未自动启用这些行为。

验收使用单一模型、英文小语料和词法检索；没有语义 Profile、长期大图或 Extension 自有行为的真实运行。
上游更新两轮仅在早期版本运行过，尚未观察到旧 synthesis 到新 synthesis 的完整自动 edited 闭环。
最近的修复轮次不能补足这项证据，也不能证明同源的实质证据贡献正向识别已经可靠。
