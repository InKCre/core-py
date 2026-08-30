# Authority Lifecycle

> Architecture-understanding provenance shard. See [index](index.md).

- **U-001 — Joint graph semantics**: block/relation/resolver/storage 共同决定信息如何保存与解释。
- **U-007 — Upstream needs evolve core contracts**: 具体 source/use pressure 可以传导到
  info-base、collection、organization、application 与 extension，但必须保留证据链。
- **U-008 — Persistence time and authored time differ**: block row time、memo-authored/source time、
  collection observation time 不得互相替代。
- **U-011 — Complexity follows marginal utility**: 不以理论上还能更完整为继续设计的充分理由；比较
  unresolved harm、机制覆盖率、dependency/obscurity 与长期维护成本。选择足够有效的低成本机制后停止，
  同时把剩余风险与弱保证写清楚。D-056 的 time watermark 是实例，不是这条方法本身。
- **U-023 — Incremental state must name its authority scope**: ETag/Last-Modified 只对产生它们的 configured
  request URL 有效；source-time watermark 只对产生它的 exact feed graph root 有效。cursor/timestamp 本身不是
  可跨 identity 重用的事实，因此 state 同时保存 scope reference（本例为 configured URL 与 feed block ID）；
  config 或 native identity 改变时 reset unrelated heuristic，而不是让旧 cursor 误删/误跳新 source facts。
- **U-024 — Source config change is not proven feed continuity**: RSS feed continuity 依次由 source-scoped native
  feed ID、declared self URL、source-scoped configured URL 证明。无法 exact match 时创建新的 feed root，旧 feed/
  items 保留；同一 declared identity 下 configured URL 可以更新。`source_instance_id` 是 scope，不足以单独
  证明两次外部 information 来自同一 feed。
- **U-025 — Schedules create commands, not hidden effects**: manual collection 与 scheduler trigger 都先创建普通
  PENDING collect job，再由同一个 atomic-claim runner 执行。schedule 是 command creation policy，不应成为绕过
  job diagnostics、status、retry 和 source-state semantics 的第二条 effect path。
- **U-033 — Spend common-path complexity only for material marginal return**: 当一个更精确的表示要求每个高频事实
  永久携带额外 identity、状态或一致性关系，却只保护罕见边缘情况时，先判断边缘情况能否通过明确的 producer
  invariant 安全、局部地退化。只有退化不造成错误 mutation、信息丢失或 authority 混淆，并且 common path 的
  语义、维护与 use 收益显著时，才选择较简单表示；这不是“忽略 edge case”，而是把复杂度放在实际产生回报的
  分支。Mail 的 plain `tags` + same-Mailbox duplicate non-reconciliation 是当前 reference pressure：罕见情况增加
  best-effort canonical Email Block，而不是让每条 flag Relation 重复 locator 或产生可变状态歧义。
- **U-034 — Identifier usability requires exact-one resolution in an explicit scope**: identifier 不是脱离 namespace、
  comparison scope 与 operation 的绝对标签。一个 reference/reconciliation/mutation boundary 只有在候选经过 scope
  与 eligibility 过滤后恰好解析为一个既有实体时，才能据此复用或修改该实体。零候选表示当前本地无 referent，
  多候选表示当前 scope 内不唯一；两者都不能被 arbitrary first/min-ID selection 隐藏，但 token 仍可作为
  source-native evidence。具体 shallow outcome 由领域 command 决定：继续较弱 ladder、创建、保留 unresolved 或
  skip；common contract 只禁止在非 exact-one resolution 上作用于某个既有实体。Mail D-264 是当前 reference
  pressure。
- **U-035 — Reconciliation completes absence but preserves contradiction；shared ladders own mechanics, not evidence**:
  一个 exact-one candidate 的 identity fact 为空时，可以用后续同 scope 的 non-null evidence 补全；双方同一 identity
  fact 均为 non-null 且冲突时，不得靠覆盖值、继续较弱 rung 或内容猜测掩盖矛盾。若多个 Source 已经重复出现
  strongest-to-weakest ladder，通用 Source-domain mechanism 可以内聚 ordered async execution、candidate cardinality、
  short-circuit 与 rung-labelled typed outcome；comparison scope、evidence meaning、eligibility、compatibility 和最终
  command effect 仍由各领域 owner 决定。Mail D-265 是当前 reference pressure；exact utility API/name 等待
  implementation preflight。
- **U-036 — Locate controls reuse；input kind controls the newly created representation**: identifier/reference ingestion
  先在明确 scope 内 locate existing domain entity；只有 exact-one 才授权复用，zero/many 则不把 ambiguity 隐藏为
  arbitrary choice。若 command 仍必须表达输入事实，它可以创建一个新的领域实体；reference-only observation 创建
  sparse/incomplete entity，full collection 创建完整或可继续物化的 entity，但二者不需要不同的 placeholder type 或
  reconciliation lifecycle。Mail D-266 是当前 reference pressure。
- **U-037 — Judge heuristics by expected harm and recovery topology，not error probability alone**: “猜错概率低”不足以
  证明 heuristic 值得采用；同时评估错误后果、系统能否检测、是否能自动/自然恢复，以及是否把内部歧义转嫁为用户
  纠错操作。不可检测地把错误外部 bytes 持久化为 semantic content，且只能让用户尝试另一个 locator 才可能纠正，
  即使低概率也不应采用。优先选择可见、局部、不会伪造 authority 且可由 Organization 修复的退化，例如产生
  best-effort duplicate。Mail D-271 是当前 reference pressure。
- **U-044 — Match concurrency machinery to expected harm，while keeping the normal result valid**（candidate Product TDD /
  Unit TDD）：即使 deployment 是 single-user，自动化和异步入口仍会产生并发，因此不能假设 race 不存在；但也不因
  理论 race 自动引入 exactly-once、专用唯一约束、回滚协议或复杂 duplicate lifecycle。先保证竞态残留不使正常
  command 失败或改变其领域结果，再用 lock/recheck 等局部机制减少残留；只有损害足以支撑成本时才升级更强保证。
  Organization 可修复低损害冗余，但不能成为 producer 放弃低成本预防的理由。Mail D-287 是当前 reference pressure。
- **U-048 — Do not gate primary progress on an orthogonal best-effort effect**（candidate Product TDD / Unit TDD）：先明确
  command 的 primary accepted effect；若另一项配置行为失败既不否定已接受事实、也不妨碍安全推进，而且为了重试它
  会阻塞高价值进度、重复大量工作或引入新的 ledger/retry lifecycle，则该行为应在 primary commit 后 best-effort
  执行并留下有界 diagnostics，而不劫持 progress cursor。只有 side effect 本身属于 correctness boundary 时才允许
  gate。Mail D-310 的 graph/checkpoint 与 `mark_as_seen` 是当前 reference pressure；Memos primary delete + best-effort
  cleanup 提供了较早的同类 evidence。
