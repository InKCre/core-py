# Cross-Model Organization Assistance

- **状态**：D-504 accepted cross-model contract；D-505 closes behavior descriptor Resolver/execution realization。
- **问题**：一个 exact model 可能可靠地发现自己的前置表示不足，同时也能判断另一个 Organization behavior 值得
  改善该表示。若只 no-op，第二项可复用判断会丢失；若当前 Agent 直接取得所有 mutation Tools，又会折叠行为边界。

## 两种不同的“先整理”

### 物化可复用信息

如果 referent、scope 或从复合来源中抽出的 scoped assertion 会被多次查询、链接或判断，它们可以由 rumination、
breakdown 或另一个 exact behavior 通过 LLM 形成普通 Block/Relation graph authority。后续模型优先复用这些显式
信息，减少每次从原始文本重新推断造成的成本和漂移。

但默认产物应是模型真正缺少的**完整可寻址信息单元**，而不是机械建立抽象 metadata：

```text
H = “欧洲区并发上限为 50，美国区并发上限为 100。”

H --source-relative exact role--> HEU = “欧洲区并发上限为 50。”
H --source-relative exact role--> HUS = “美国区并发上限为 100。”
```

`HEU` 与 `HUS` 现在可以分别参与 supersession，且仍能回到 H。若“支付服务”或“欧洲生产环境”本身已经存在或
确实值得跨来源复用，可以另外通过 existing-referent anchoring / exact contextual linking 连接；不能仅因内部 SOP
曾临时识别 referent/scope 就一律造 Block。

这些 Organization-authored 结果提高稳定性但不成为绝对真值。它们必须保留来源和普通 edit/version continuity；
上游出现可观察变化时，相关 exact model 仍需重新判断。

### 保存跨模型候选

Sir 提出的最小图形是：

```text
information --needs organization--> organization-behavior Block
```

当前推荐保留这个 topology，但把 content 收窄为：

```text
information --candidate for--> exact-behavior descriptor Block
```

原因是 `needs organization` 很容易被解释成尚未完成的工作项。一旦持久化这种含义，就必须定义 claim、完成、失败、
撤回、重试和 resolved/unresolved 生命周期，并会反向要求 D-503 已刻意省略的 terminal-result state。`candidate for`
只断言“现有证据足以让目标行为考虑这个信息”，不承诺调度、适用或成功；目标行为仍可 no-op/unresolved。

候选 Relation 可以继续留存，因为“曾/仍是合理候选”不等于“尚未执行”。自动运行优先扫描新出现的 candidate
Relations，并由已有 positive-edge/replay checks 抑制明显重复；不增加 queue table、completion Relation、cursor 或
generic dispatcher。

## Behavior descriptor Block 的角色

若 target 要被确定性执行路径识别，它不能只是内容为 `rumination` 的任意 `core.text.v1` Block，也不能指向某个
Agent definition：behavior 不是一段普通同名文本，Agent 也只是可替换执行方式。

这个用例第一次为一个精确、Resolver-backed 的 behavior descriptor Block 提供了实际理由：

- Block 只给 exact behavior 一个可寻址的语义身份与可读描述；
- prompt、AI model、Tools、预算、Cron 和 Job 状态仍由 execution/config owners 持有；
- 每个 exact behavior Block 的 Resolver type 同时提供 identity 与 `consider_candidate()` orchestration；
- Extension 将来可以拥有自己的 descriptor 与 handler，而不修改 generic graph semantics。

这会重新打开先前“当前不需要 `OrganizationBehavior` entity/registry”的结论，但理由已经改变：不是为了运行时
polymorphism 或配置，而是为了让一个 graph Relation 精确指向可扩展的跨模型候选 consumer。是否现在批准这一
Block contract，必须作为 material decision 单独复核；不能在 supersession Tool 中偷偷引入。

## 完整协作路径

```text
supersession Agent examines B and compound H
  -> primary result: no supersedes edge，because H is not sufficiently addressable
  -> independent assistance judgment: H is a candidate for decomposition/rumination
     -> fetchsert H --candidate for--> decomposition descriptor

decomposition/rumination execution scans its new incoming candidates
  -> reads H through Resolver
  -> LLM creates HEU and HUS plus exact source-relative provenance Relations
  -> ordinary new Block/Relation facts become observable

supersession candidate formation sees B / HEU / new graph neighborhood
  -> Agent now proves whole-addressable dominance
  -> B --supersedes--> HEU
```

Primary model and assistance outcome remain distinct。The supersession operation itself still does not create HEU/HUS or gain
generic graph mutation。Agent runtime exposes one
`record_organization_candidate(information_id, behavior)` Tool；its dynamically bound schema admits only registered exact
BehaviorResolver types。The selected class lazily fetchserts its descriptor and invokes shared `record_candidate()`，which only
validates endpoint roles and fetchserts `candidate for`。

## Relation-to-whole-Block Law

A Relation applies to the endpoint Block as one information unit。This does not require one sentence per Block or automatic
sentence splitting；atomicity is relative to the asserted relation。When the desired relation holds only for one sentence or
claim inside a Block，that claim must first become an independently addressable Block with provenance back to the source。

This law applies beyond supersession：support/challenge、refinement、duplicate、referent anchoring and source-relative roles must
all abstain when their endpoint granularity would make the edge over-claim。

## Accepted Candidate Admission Law

An Agent that owns `record_organization_candidate()` may choose any existing exact behavior descriptor Block，not only rumination。
“Free choice” means the target set is open and Extension-growable；it does not mean arbitrary strings、automatic behavior creation
or marking every uncertain case。Before writing，the Agent must establish：

1. it found a concrete representational or semantic obstacle/opportunity，not merely that its primary model no-oped；
2. the target descriptor's declared behavior directly addresses that obstacle or can produce a reusable distinction needed by
   a later exact model；
3. the target input is sufficiently addressable for that behavior to consider；
4. current graph authority does not already contain the needed result or the same exact candidate edge；
5. observed recurrence、topology or downstream pressure gives a reasonable best-effort expectation that paying the additional
   Organization cost is worthwhile。

The single exact Tool validates only existing endpoints、target resolver role and fetchsert identity through the target Resolver。
It does not let the Agent invent a
unregistered behavior ID、submit a descriptor payload or submit a generic GraphForm。The target class may mechanically
materialize only its own canonical descriptor。A newly written candidate edge counts as a graph
effect even when the originating model itself produced no primary Relation。

## Accepted Result And Remaining Realization

D-504 accepts scoped-information materialization、Relation-to-whole-Block atomicity、open target selection and
`information --candidate for--> behavior descriptor` as the cross-model attention law。The descriptor is not an Agent、Job or
pending task，and the edge has no completion lifecycle。

The active Technical candidate lets each behavior Block's exact Resolver implement actual `consider_candidate()` orchestration。
This reuses existing Resolver registration instead of adding a Source-like pointer and second capability registry；the latter only
becomes justified if Organization gains separately persisted behavior instances/config/state。The target set is not limited to
rumination；any existing exact behavior Block whose Resolver exposes the capability may be marked。The exact source-relative
Relation content linking a compound source to extracted units remains owned by the producing behavior rather than one generic
`derived from` relation。
