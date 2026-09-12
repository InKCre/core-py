# PR #100 合并前复审

2026-09-12 首轮审查基线为 `a3eaff20d720a73e31a7c2b22a65881340c98dcf`；2026-09-13 继续复验 `4a0f266`、`48ed482`。
本轮由 Sir 要求重新审查整个 unit，
为 PR #100 合并作准备；不执行合并，不新增回归或聚焦测试，新修复方案仍先复核。

## 结论与阻塞

**PR 已具备按当前 best-effort 边界合并的条件；本轮不执行合并。** D-561 修正已随 `48ed482` 推送，
Preview 三节点链的完整读取、截断和真实闭环均正确，三次并行健康请求均在读取结束前返回 200，临时资源已清理。
递归环检测和同步读取执行位置均已修复，查询算法与上限不变；已知 SQL 性能问题按 Sir 的明确决定留待以后。
此前将 1000 节点远端读取作为新合并门槛不成立，历史失败保留，不扩大本轮范围，也没有跳过读取验收。

本结论表示已批准修复、局部文档纠正、既有 CI 与实际读取验证闭合，不表示整组语义判断全部正确、默认可以
自动启用或已关闭 Unit。下文的错误关系与未覆盖输入仍是交付残余。

首轮发现的确定性缺陷是：`SupersessionBehaviorResolver.read_lineage()` 的默认探索上限为 1000 个 Block，
原实现最终却使用递归 DFS 检测环。
一条合法的 1000 节点无环链在 `_cycle_detected()` 中触发 `RecursionError`，无法返回 current/history 投影。
同一实现的 100 和 400 节点输入正常返回 false。复现只创建内存 RelationModel，使用不可连接的本地数据库
占位配置，没有访问数据库、调用模型或新增测试文件。

D-560 中 Sir 已同意修复。环检测现改为标准库 TopologicalSorter 的显式栈实现，保持接口、探索上限、方向
和环判定含义不变；不提高 Python 递归上限，不改变图模型。本地一次性检查的 100/400/1000/10000 节点链
及其闭环均得到正确结果，静态检查通过。Preview 小链读取和截断结果正确，1000 节点读取失败；
详见 [读取复验](acceptance/lineage-read-review.md)，其中也披露了一次辅助闭环探查的构造错误。

复审发现的另一项历史合同差距：D-519 要求候选局部失败不丢弃其它 seeds，原六种探索行为的
`run_automatic()` 直接等待 `build_seed_message()` 和 `run_configured_agent()`。一个 seed 在选择后消失，
或一个 Turn 耗尽预算，会结束整个 Job，后续 seeds 未处理；此前真实验收已观察到后一种情况。
Rumination 原先仅单独容忍 seed_missing。Sir 随后在 D-559 同意落实：七种自动行为对候选缺失和单次预算
耗尽记 recoverable_failure 日志并继续；配置、数据库、provider、其它执行异常和取消仍传播。显式 focal
rumination 的错误行为不变。已提交的图效果保留，正常遍历结束的 Job 可以 finished，但不说明每个 seed
成功或图语义正确。实现使用私有异常边界，无 broad catch、重试、新状态或报告。
本次 format/lint/typecheck、foundation、静态审查、既有测试（14 passed / 53 skipped）及 diff 检查通过；
七处自动边界与显式调用链已逐项审阅。当时未重新运行真实模型；后续 4a0f266 整组 Job 均 finished，但没有逐次
Agent 日志，因此仍不能声称已经动态覆盖这两种候选局部失败路径。

### read_lineage 的定位

该读取合同记录在 D-506，具体放置由 D-520 确认为 SupersessionBehaviorResolver.read_lineage，而不是通用
Resolver base。它从一个 focal Block 沿已有 supersedes 关系取得有界子图，解释仍未被后继替代的前沿，
并报告环和截断。它没有新的 HTTP endpoint 或专用 Agent Tool，可通过既有 Resolver 方法发现/调用访问。
例如 C supersedes B、B supersedes A 时，完整无环结果的前沿是 C，A/B 仍在返回历史中；它不判定图上
替代关系是否语义正确、不按时间戳选择“最新”、不隐藏检索结果，也不是第八种 Organization 行为。
Sir 先要求解释这个方法，随后在 D-560 同意修复其长链算法。

## 可读性、可维护性、文档与注释复审

本轮重新沿七种 BehaviorResolver、Agent 工具与输入模型、Resolver reflection、Graph Navigation 和开发追踪的
调用链检查；与首轮整组差异审查合并判断。重点是读者能否恢复责任和失败含义，而不是行数、排序或消除所有重复。

小图复验后再次核对公开/私有读取边界、Session 退出后的图字段、七种 Job 路由、候选局部失败边界和对应说明，
没有新增合并阻塞。总览中“seed 限制起始成本”的表述也统一纠正：Job 限制 seed 数量，不代表 rumination
一跳上下文具有关系数量上限。未借此调整现有行为或重构配置 helper。

审查发现与本轮处理：

1. **实际读取成本被 async 方法隐藏。** 修正前 `supersession.py:read_lineage` 在 async 方法中逐节点执行同步 SQL。
   稀疏 1000 节点链约需 2000 次关系查询，且期间不会主动让出事件循环。20 节点约 11.6 秒的远端读取、
   长链期间的健康检查超时与此一致。应把同步读取的执行位置和图遍历的往返成本分别说清、分别处理；
   仅换环检测算法或加线程都不能证明长链延迟已解决。D-561 批准仅将完整同步读取移出事件循环，SQL 优化延期。
2. **公开方法说明缺少结果含义。** 修正前 `read_lineage` 没有 docstring，实际方法发现只返回 `read lineage`。
   现用简短说明明确“读取 supersedes 历史；截断或有环时不返回 current 前沿”，详细方向、例子和限制放在
   Organization TDD。没有把内部循环、缓存或参数重复解释塞入 Agent 可见 description。
3. **局部文档的职责和范围有歧义。** `business-pipeline-and-authority.md` 原先将“有界候选读取”归给 Job，
   而实际由 BehaviorResolver 完成；`submit_graph 是唯一 graph-write Tool` 应明确限定为 rumination 的所附
   definition。该文档与 `semantic-retrieval.md` 将 rumination 的全部 direct relations 快照称为 bounded，
   容易被理解为数量有限制；现明确说明“一跳、不递归，但没有关系数量截断”。以上三处均已纠正，不重设计行为。

低优先级的类型维护机会是 `_shared.py` 配置 helper 接受任意 Pydantic model，再用 Any 访问 agent；当前实际调用者
只有已有的 RuminationConfig 和 BehaviorAgentConfig。可以将静态类型收窄到真实输入，不需要新协议或配置抽象；
它不是这次已观察失败的原因，也不作为合并阻塞，本轮未修改。

以下复杂度有明确依据，审查未发现需要借此扩大重构的理由：七种独立行为保持本地写入和选择策略，Job 路由简单明确；
Resolver 工具 schema 的动态分支和 envelope 是已观察 provider 合同的适配，相关注释解释了保留原因；
invoke 的 index/block_id/method 是 D-530 明确保留的关联信息；已有 schema 字段名称保留实体身份，写入工具描述
给出关系定义而非重复参数。环检测新注释说明长链不应消耗 Python 调用栈，调试代码说明日志失败不得覆盖 Agent
实际结果。未新增 generic behavior 层、关系 registry 或为了消除重复而合并行为。

### D-561 批准的实现与验证范围

将 read_lineage 的同步读取整体放到工作线程，由该线程创建和结束 Session；保留公开 async 方法和返回
合同，不把通用 ResolverManager 改成新的执行适配层。这个修改只解决阻塞 Peer 事件循环的责任，不承诺缩短
SQL 遍历时间。本轮不继续比较或实施数据库优化；默认节点/关系探索边界、方向、截断与空前沿含义保持不变。
线程读取没有共享或外部传入 Session，也不访问 Resolver 实例上的 ORM Block；返回对象仅包含已加载的图字段。
取消 await 不会强制停止已经开始的同步读取，Session 仍由该线程退出时关闭，文档不声称解决了同步 SQL 的取消。

上述说明修正一并处理；配置 helper 类型收窄不纳入。验证复用既有 Preview 读取与并行健康请求，使用 C → B → A
三节点链检查完整、截断和闭环，不新增测试或修改 Agent 定义/预算。

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

4a0f266 修复后再次运行上述本地检查，结果相同：14 passed / 53 skipped，typecheck 0 diagnostics，静态审查
0 errors / 0 warnings；三个 required checks 和 Preview 部署通过。这些检查不能证明语义质量或长链读取延迟。

48ed482 再次通过相同本地检查，三个 required checks 均成功，
[Preview 部署](https://github.com/InKCre/core-py/actions/runs/34707301558) 通过；
[本轮小图读取](acceptance/lineage-read-review.md) 的三种结果和并行健康响应全部通过。分支包含检查时最新 main
（0 behind / 29 ahead），PR 非 draft，没有 review conversation 待解决。最终证据提交仅更新文档与 task packet，
不改变已验收源码；其 CI 状态以 PR 页面为准。

## 语义质量及尚未覆盖的范围

最新整组初始世界证据是 [merge 轮](acceptance/merge-run-review.md)：七个 Job 均 finished，最终 39 Block / 27 Relation。
无逐次 Agent 日志，不能据此声称零预算耗尽或每个 seed 自然结束。完整提案与局部 rollout 陈述被记 duplicates
assertion、来源重述被记 supports 等误判仍在；临时数据与配置已清理。运行结束不等于语义验收通过。

此前有逐次轨迹的整组证据是 [discovery 轮](acceptance/discovery-review.md)：6/7 Job、19/20 次执行自然结束。
Refinement 仍有无产出耗尽；技术摘要被用来替代完整旧提案、来源重述被写成支持关系等误判仍可见。
最新 evidence stance 专项是 [stance-role 轮](acceptance/stance-role-review.md)：5/4/4 次调用，零错误/耗尽；
技术摘要正确 no-op，但 rollout 条件仍被原方案错误 supports。不能把三次自然结束写成语义验收通过。

Sir 已接受部分派生内容不准确的 best-effort 残余；这不自动说明其它错误关系符合定义。现有证据支持按需配置、
可扩展的能力实现，不支持默认自动启用或“可靠替用户维护正确知识”的宣传。当前 PR 未自动启用这些行为。

验收使用单一模型、英文小语料和词法检索；没有语义 Profile、长期大图或 Extension 自有行为的真实运行。
上游更新两轮仅在早期版本运行过，尚未观察到旧 synthesis 到新 synthesis 的完整自动 edited 闭环。
最近的修复轮次不能补足这项证据，也不能证明同源的实质证据贡献正向识别已经可靠。
