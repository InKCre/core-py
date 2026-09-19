# Organization Nowledge Study

- **Unit ID**: `organization-nowledge-study`。
- **状态（D-562）**：**Closed / production delivered**。PR #100 已 squash 合入 main（`915be5a`），Release PR #101
  发布 Core 0.2.0（`b3ccb00`）；2026-09-13 02:04:12（Asia/Shanghai）生产部署与 stable 接纳完成。
  独立健康请求通过，生产目录已有七个 automatic Organization Job，行为配置仍为空，没有默认启用。
  [生产交付记录](production-delivery.md) 保留版本、镜像、Heroku release 与探针回执。Parent task 保持 active，
  包括尚未执行的 Hub owner reconciliation；本 packet 随 parent 生命周期保留。
- **交付修正（D-561）**：read_lineage 同步读取移出 Peer 事件循环的修正已随 `48ed482` 推送，公开说明与局部 TDD
  已纠正。Session 在线程内创建和关闭，查询算法与上限不变。Preview 三节点完整读取、截断、真实闭环以及并行
  健康响应均通过，临时资源已清理。SQL 性能优化明确延期，没有扩节点或跳过读取验收。
  [读取复验](acceptance/lineage-read-review.md) 保留最终结果、此前失败与清理回执。
  D-559 的候选局部失败继续已实现，
  其它故障与取消仍传播，显式 rumination 不隐藏耗尽。不新增测试。已移除预定的 PR 专用临时调试设施。
  [合并前复审](merge-review.md) 记录 findings、检查和残余；合并授权与 unit 关闭条件现由 D-562 确定。
- **最后一轮 Agent 设计（D-557）**：`7bb868c` 的 evidence stance SOP 已先识别目标命题与证据贡献；工具合同、
  共享提示词、模型、预算与工具组合不变。使用现有 preview 配置新 definition 验证，没有新增测试。
- **最新整组验收**：4a0f266 的 Job 101–107 全部 finished，18/6 初始图变为 39/27，临时数据和配置已清理。
  没有逐次 Agent 日志，不能宣称零预算耗尽；图中仍有局部陈述被误作 whole-Block 重复、来源重述被记 supports
  等问题。见 [整组复评](acceptance/merge-run-review.md)。生产交付和 unit 关闭不改写这些语义残余。
- **关闭后边界**：没有继续执行的本 unit 修复或发布工作；新发现的修复先复核，不继续无边界地微调提示词。
  结束探索与不存在性证明的区分已沉淀至
  [通用模式](../../common-patterns/agent-tools.md)，新的修复方案仍先经 Sir 复核。
- **实现阅读入口**：[Organization TDD](../../../../docs/30-unit-tdd/organization.md) 与最新 decision 解释已交付合同；
  Product 研究稿和下面的历史进度保留推导过程，不能据其中过期的 active、候选或授权表述重新启动工作。

## 历史进度

以下记录保留各轮当时状态；当前实现、验收及授权边界以页首和最新 decision 为准。

- **D-557 验收**：Job 99 的 5/4/4 次执行均结束，零错误/耗尽；rollout 条件仍写同源 supports。见
  [stance-role 评审](acceptance/stance-role-review.md)，不以这次专项结果代替当前整组证据。
- **D-556 验收**：工具定义与 Resolver 合同补充来源忠实性排除项后，stance 轮 12/10/6 均结束，但两个
  同源 supports 误判重现。驱动参数已按既有至少 3 的合同纠正，清理完成，见 [stance 评审](acceptance/stance-review.md)。
- **D-555 验收**：`ebf220a` 的结束探索指导完成 discovery 轮，6/7 Job、19/20 次执行自然结束；
  refinement 仍无写入耗尽，evidence stance 把来源重述写为支持。清理完成，见 [discovery 评审](acceptance/discovery-review.md)。
- **D-554 验收**：`5fef0fd` focal 轮 5/7 Job、15/17 次执行结束；evidence stance 无写入耗尽，
  synthesis 最后一次写入后耗尽。清理完成，见 [focal 评审](acceptance/focal-review.md)。
- **Current implementation（D-554）**: Sir 接受派生内容不够准确的 best-effort 残余，授权恢复 rumination
  专用三工具组合；已移除其探索/candidate 工具与共享探索提示拼接，保留 Resolver/Job 入口及外部候选消费。
  已检查其余六种行为，无跨行为精确写入或任意图写入工具，保留合理的读取/图检索能力；提示词明确不必
  为写前准备重读已有完整内容。format/lint/typecheck/diff 检查已通过；本次尚未进行新的真实模型复测，
  不沿用旧轮次结论。
- **Current acceptance（D-553）**: `2dac3e1` 已提交部署并完成 guidance 初始世界复测及清理。
  7/7 Job、21/21 执行自然结束，113 次模型/138 次工具调用，零预算耗尽与工具错误；rumination 8/10/11、
  evidence stance 2/7/2、anchoring 3/5/5。仍有重复读取、候选/关系语义与派生内容问题，整组语义不通过。
  详见 [guidance 轮评审](acceptance/guidance-review.md)。不追加未获批修复，不新增测试。
- **Current diagnosis**: Sir 要求定位 rumination、evidence stance、anchoring 耗尽根因。已逐调用核对：
  语义检索未配置与长词法查询错配、重复读取/图路径利用不足是可见成本；rumination 最后仍有效写入，
  另两者主要堵在目标发现，不能统一称死循环或预算不足。见
  [剩余预算诊断](acceptance/remaining-budget-diagnosis.md)。进一步发现 rumination 提示词未保持 focal 目的；
  已按 Sir 建议为两个实体读取工具补充 null 可能来自类型误选的说明，静态检查通过，尚未部署。
  其它修复未实施。
- **Current implementation（D-552）**: Sir 授权应用逐项类型引用和无需复读成功回执指导并复测。代码与定义已修改，
  format、lint、typecheck、diff 检查通过；`f4362ad` 已部署复测并清理。12 次读取引用调用均成功，5 次写入后
  自然结束的执行均未在最后写入后再次调用工具；整组仍不通过。详见 [references 轮评审](acceptance/references-review.md)。
  4/7 Job 完成，rumination/evidence stance/anchoring 仍耗尽；不新增测试，不继续擅改方案。
- **Current decision（D-551）**: get_entities 采用逐项 `{type, id}[]`。保留简洁成功回执，撤回完整 Relation
  返回提案；用提示词明确无需复读确认成功写入。已核对既有指导并非缺失，但未阻止本例。实施状态见 D-552。
- **Diagnosis history**: Sir 要求诊断实体类型误用的工具界面根因。已区分“类型跨工具重新编码”与“候选写入
  被误认为行为执行”，取消默认类型不足以解决实际显式误选；证据和未获批方向见
  [实体界面诊断](acceptance/entity-interface-diagnosis.md)。后续修正与实施状态见 D-551、D-552。
- **Current repair（D-550）**: Sir 已确认 entity_ids 使用普通数组、默认空数组代表随机读取，移除 null 分支。
  已提交 `9a7ab93` 并完成 preview 初始世界重验：15 次指定 ID 与 1 次随机批量均成功，整轮调用错误为零。
  不增加字符串解析，不改 SOP。旧 batch 证据保留。
- **Previous array run**: array 轮 4/7 Job 完成；rumination `7、9、12`、refinement `4、12`、anchoring `12` 仍有预算耗尽。
  工具修复有效不等于整组通过；具体轨迹、语义残余和后续待评审范围见 [普通数组重验](acceptance/array-review.md)。
- **Previous run**: `faa74ba` 已完成 preview 初始世界重验并清理。Refinement `5、5、4` 次均自然结束，
  rumination 仍 `8、10、12` 第三次耗尽，synthesis 也耗尽；5/7 Job 完成。新增 get_entities 的 21 次指定 ID
  调用全部因字符串数组失败，一次随机批量成功。整组不通过；证据与待复核的最小修复提案见
  [批量入口重验](acceptance/batch-review.md)。暂不继续改 SOP，先评审工具干扰的修复。
- **Acceptance authority（D-548、D-549）**: 重新验收、相关提交和推送自主执行，新修复方案先经 Sir 复核；
  将已批准的本地工具修改发布到 preview 后重验，不能用旧版服务验证新入口。
- **Current decision（D-547）**: Sir 授权实体读取升级为 `get_entities`，支持批量指定 ID 或一次取多个随机 Block；
  本地实现并同步定义输入；format、lint、typecheck 与 diff 检查通过，已提交部署并重验，结果见页首。
  历史验收记录不改写。随机读取使用数据库随机排序，尚未验证大图性能。
- **Prompt decision（D-546）**: Sir 已确认 rumination 修复方案，并将 refinement 修正限于批量检索、无需找到
  refinement 即可 no-op 结束；已按此部署并重验。预算保持不变且不向模型公开。
- **Stopped run（D-545）**: 此前未经批准的运行保持停止，现场仅作审计记录，不能用于证明新方案效果，见
  [已停止的诊断记录](acceptance/closure-review.md)。
- **Current work**: 工具修复及静态检查完成；原版本端到端基线已导出并清理（7 个 Job，2 完成、5 预算耗尽）。
  修复版 4b69dd9 已完成同模型、原提示词、12 次预算的完整初始世界对照并清理：不可用方法 71→0，
  含错误的工具请求 24→2，但仍有 4 个 Job 预算耗尽及语义偏差。两项最小收口只做静态检查。
  结论与后续残余统一见 [对照评审](acceptance/tool-repair-review.md)，整组语义验收未通过。
- **Active edge（D-542）**: 下一轮聚焦 system prompt 或工具组合，保持模型及预算不变。
  七份 SOP 已落独立定义输入，两套现有验收入口共用；工具集合不变，完整重验与清理已完成。
  完成 Job 3/7→5/7，自然结束 11/15→17/19，模型请求 137→133；仍有语义残余，详见
  [本轮效果评审](acceptance/prompt-review.md)。本轮修改尚未提交。
  依据与实施边界见 [新一轮方案](system-prompt-and-tool-composition-plan.md)。
  不能仅凭错误减少、Job 完成或增加预算认定组织结果正确。
  实施与环境证据统一见 [工具修复实施记录](acceptance/tool-repair-implementation.md)。
- **Verification constraint（D-541）**: 不得新增任何回归测试或聚焦测试；已撤掉新增回归文件和单工具探测脚本。
  已有测试只同步接口变化；以静态检查、代码审阅和端到端黑盒验收验证修复。
- **Repair scope**: 公共 Resolver 方法直接入 schema、发现/错误反馈、实体基础读取、三个直接图查询、轻量候选
  投影、同模式精确写入定义和命名。依据见 [修复方案](agent-tool-repair-plan.md)、
  [命名检查](acceptance/tool-naming-audit.md)、[通用模式](../../common-patterns/agent-tools.md)。
- **Latest acceptance**: 原 PR #100 两轮语义验收未通过；开发日志已验证过真实读回。当前基础设施修复及 schema
  探测不改变此结论；本轮修复尚待端到端效果证据。
- **State**: **Verify / Acceptance active after D-527 implementation。Product closed by D-493，Technical material boundaries by
  D-523，best-effort black-box Acceptance by D-525，Implementation Plan by D-526，Preflight/Impact Handshake closed by D-527**。
- **Objective**: 以逐项学习 Nowledge 得到并经 transfer audit 修正的 Product model 为同一 implementation vertical 的
  Product foundation，围绕这一整组 Product features 形成一套 Technical design、Acceptance、Implementation Plan 并
  整体实现对 InKCre info-base organization 系列能力的改善；内部行为边界不成为 delivery slices，也不构造 generic
  Organization framework。
- **Guardrails**: info-base 存储 information，不把个人 Memory ontology 提升为全局模型；organization 根据过去证据
  预测未来可复用价值，但不知道某次实际 future use；不从 Acceptance 便利性反推 Product；不复制 Nowledge 功能清单；
  不为了结构美、干净或图形观感整理；`no Core transfer` 不等于禁止 Extension capability；Technical/Acceptance 必须先
  恢复现有实现并确定最小 owner/surface；源码、targeted tests 和 core-py local durable-doc mutation 已由 D-527 授权。
- **Verification**: Product 阶段必须让 external evidence、inference、accepted Product design 和 decisions 分别可恢复。
  Technical / Acceptance 只为 accepted Product results 建立 claims，不因实现方便复活 audit 已拒绝的 Nowledge packaging；
  D-495 已纠正“研究返回 none 即可终止”的旧 framing；D-496 进一步要求整组功能共同进入唯一 delivery loop。
  最后一项机制关闭后执行独立 [Nowledge transfer audit](audit/nowledge-transfer-audit.md)：以过度借鉴、记忆产品假设泄漏、
  重述既有 truth 和无解释力抽象为主问题；覆盖检查只用于发现漏审对象，不以覆盖完整为由批准 transfer。
- **Current Truth**: Knowledge Evolution 已由 D-470 关闭。已接受
  `Information -> one or more evolution properties -> one or more evolution models -> relation / state transition`。
  model/property 不是 information object 的互斥分类。新增官方证据支持将 Nowledge 分为 supersession lifecycle、
  accretive refinement lineage 和 evidence stance，而不是一个 progression state machine。Past-use forecasting 属于
  Product admission loop，不属于 evolution execution。
- **Decision lineage（历史沿革，当前工作见页首）**: D-495 supersedes D-494's research-only classification，D-496 removes the attempted delivery-slice framing，
  D-497 将 Job 降回运行载体。D-498 defines Organization through the end-to-end distinction-realization axis；D-499 classifies
  the retained Product results；D-500 places focal-Block reads in Resolver、neutral topology in Graph Navigation and request-
  specific interpretation in Application。D-501 withdraws run-time Tool allowlists：each execution family selects a complete
  purpose-built Agent definition。Technical design now moves from accepted minimal shared mechanics to exact per-model candidate/
  evidence/judgment/command contracts；it does not generate components from feature-name symmetry。D-502 restores an omitted
  accepted Product boundary：ordinary edits append a new Block and old `--edited-->` new continuity；observable upstream edits
  reach affected synthesis through its source-basis Relation and trigger reapplication，while bytes changing invisibly behind a stable
  Storage pointer remain an explicit best-effort defect。The false stable-address Product prerequisite and P-033 are withdrawn。
  The synthesis exact-contract candidate now separates `SynthesisProposal(text, source_ids)` from reapplication context：its
  command writes basis plus `edited` continuity，while independent evolution models alone may later assert supersession/refinement。
  Its current review candidate also closes the end-to-end runtime tail：cheap mechanisms form bounded candidate regions without
  enumerating subsets；the synthesis Agent explores and judges；and the exact Tool mutates the graph。D-518 later corrects the
  unnecessary effect-report tail：the graph owns effects、JobStatus owns lifecycle and logs/traces own diagnosis。
  D-503 accepts that complete runtime contract and corrects its exact source-basis Relation content from the over-broad
  `contributes to` to `synthesis`；the direction remains source -> derived synthesis。
  Technical review now applies the same exact derivation to scoped supersession：the active candidate limits a clean
  `successor --supersedes--> predecessor` edge to whole-addressable dominance，keeps semantic time distinct from record time，adds
  transaction-visible cycle prevention，and makes current/history a bounded Resolver projection rather than global retrieval
  state；because generic Relation writers remain possible，the projection must also expose anomalous cycles honestly。Its SOP
  now distinguishes referent from the narrower evolving subject and tests addressability、subject continuity、scope coverage、
  semantic succession、replacement authority and complete dominance；the first implementation may delegate all six open-world
  judgments to the purpose-built Agent while deterministic code only proposes evidence and enforces graph mechanics。
  Sir further identifies reusable prerequisite materialization and cross-model assistance：explicit scoped information can make
  later judgments cheaper and steadier，while a model that abstains on endpoint granularity may still identify another behavior's
  candidate。The active candidate keeps this separate from supersession mutation，prefers a stateless
  `information --candidate for--> behavior descriptor` signal over stateful `needs organization`，and reopens a Resolver-backed
  behavior Block only because it now has a concrete graph-reference/Extension-routing use。D-504 accepts this cross-model
  candidate law and allows an Agent to cautiously choose any existing exact behavior descriptor，not only rumination。Current
  review corrects the previously misunderstood `resolver.ruminate/supersede/synthesis` proposal by comparing three placements。
  Current code shows concrete Resolvers already perform lazy materialization、AI-assisted work and graph authoring，so pure-read
  framing is withdrawn。The active minimal candidate makes each behavior Block's exact Resolver type its identity and actual
  orchestration carrier，with `consider_candidate()` as the only shared graph-routing capability。A Source-like pointer is deferred
  because Organization has no separate persisted behavior instance/config/state to point at，and a second identity-to-callable
  registry would duplicate ResolverManager。Agent-neutral exact graph commands remain independently callable beneath orchestration。
  D-505 accepts this exact BehaviorResolver design；Technical work returns to closing scoped supersession's complete runtime
  contract。D-506 closes scoped supersession as whole-Block dominance with six semantic conditions、an exact idempotent command、
  transaction-visible cycle rejection and a bounded current/history projection。The next exact derivation is non-dominating
  refinement。D-507 closes it as compatible additive lineage with contained scope narrowing、information-role continuity and no
  dominance/currentness/provenance claim。The next exact derivation is evidence stance：support/challenge must be grounded in a
  real evidential relation rather than wording agreement or contradiction。D-508 closes evidence stance as provenance-preserving
  defeasible support/challenge without truth scoring or evidence-weight persistence。The next exact derivation is existing-
  referent anchoring inside the open contextual-linking family；it must resolve only existing identity-bearing information and
  must not revive automatic Entity materialization。D-509 closes that model with an occurrence-local selected-text Block：
  `source --has mention--> fragment --refers to--> referent`，rather than overclaiming the composite source or encoding selectors
  in Relation content。The next exact derivation is provenance-aware duplicate assertion；its active consumer review has found
  that an induced-only input subgraph cannot preserve count-once semantics when two input Blocks connect through an omitted
  duplicate。D-510 corrects D-500 to bounded full-component expansion from the input seeds。D-511 closes duplicate assertion
  around the assertion-relative 断言来源事件、whole-Block equivalence、non-independence、canonical edge and no-occurrence-entity
  boundary。All six exact-model contracts are now closed；the active edge reconciles the complete set against Acceptance、shared
  runtime、Extension influence and Implementation-plan prerequisites instead of deriving another behavior。该 reconciliation
  已发现并撤回一个技术设计偏差：来源产品的 `Nowledge Job families` 命名不属于 InKCre，而且“四条 Job + 一个
  rumination-candidate Job”用局部缺口塑造了运行拓扑。D-512 已从本地 behavior 责任推出五条独立自动 Job，其中
  rumination 拥有完整候选规律；`candidate for` 只是每条目标 Job 可消费的一种高优先级 seed。
  D-513 接受 append-only 的档位 1：它约束本 unit 自有 Organization output，并作为其它 producer 的指导原则；不成为
  database、BlockManager、PATCH 或 Extension persistence 的全局 enforcement。现有 mutable upstream provenance 是明确的
  best-effort residual，只有具体 use failure 才推动 owner-specific adoption。D-514 进一步确认当前只有 changed synthesis
  是确定的 direct revision caller；首版由完整 synthesis command 原地实现 Block + basis + `edited` transaction，等第二个
  exact direct caller 出现后才提取 `append_block_edit()`。
  D-515 已撤回 D-512 的 Evolution Job 合并：由于没有证据证明 supersession、refinement 与 evidence stance 共享候选和
  运行边界，七个 exact behaviors 各有独立 Job。六个模型 mutation methods 放在相应 concrete BehaviorResolver；Agent
  侧只注册一个 `record_organization_candidate` Tool。D-516 接受 descriptor 使用 exact Resolver type + empty content 的
  持久形状，但 Sir 正确拒绝了 post-registration global sync。D-517 改为复用 Resolver 自注册与 Agent Tool dynamic
  schema：唯一 candidate Tool 接收已注册 behavior type，由 target Resolver class 在实际 candidate transaction 内惰性
  fetchsert descriptor；Job 需要自身 graph receiver 时复用同一 mechanics。D-518 删除没有消费者的 BehaviorReport、成功
  `Job.state` effect snapshot 和共享 `changed`：graph 表达持久效果、现有 JobStatus 表达执行状态、结构化日志/trace 提供
  过程诊断；exact methods 只向直接调用者返回 model-specific IDs/created state。代码复核进一步暴露 D-512/D-515 中
  “Job owns candidate law”的不精确简写：
  D-519 让 exact Job Handler 只做 availability + invocation，候选/判断/写图由 target BehaviorResolver 拥有；七个 Job
  types 独立但只共享 `max_seeds` occurrence bound。随后对 duplicate query/use 的核对发现：强行寻找具体 consumer
  并不是 Organization behavior 成立的前提；修正保留 bounded Graph Navigation component query 与 count-once use law，
  把 synthesis 降回一个
  cross-model consistency example，而不新增 designated consumer、evidence-counting Application、component state 或外部
  transport。Sir 随后提出真实 maintainability pressure：relation content 可能散落在 writer/readers。D-520 让
  exact behavior module 的公开 `Final` constant 成为 runtime token authority，generic graph 保持 vocabulary-blind；简单
  consumer 传 constant，只有非平凡解释才增加 behavior-owned typed read。Persisted token rename 仍必须显式 migration，
  不能靠改常量。该检查还暴露 planned content-Resolver supersession read 的反向依赖，并将其移到
  `SupersessionBehaviorResolver.read_lineage()`。D-520 同时确认 Organization behavior 不需
  绑定当前具体 consumer；它只需留下可查询的区别和稳定 use law。Whole-set audit 随后确认真正未关闭的下一条边界是
  Agent 如何在初始候选之外搜索、读取和导航，而不是另造 consumer 或 behavior。Sir 进一步纠正：防止任意数据库
  访问没有必要成为架构边界，且不能把 Block/Relation 再包装成 `Information`。进一步 review 又撤回了
  `read_blocks -> get_label/get_text`：它虽然不改名，却把 Resolver 的开放 typed capability 压成 Organization 自己的
  窄读取协议。D-521 让 Resolver owner 持有 method discovery/invocation，并确立 owner-coherent meta-tool 原则。D-522
  进一步把共享探索面收敛为 `retrieve`、`resolver`、`graph_retrieval` 三个元工具：hybrid retrieval 保留两个原生结果
  分支，Graph Navigation methods 不再逐个增加 Tool ID。当前不采用 PostgreSQL/Cypher 是 ROI 判断，不是能力禁令；
  Organization 不依赖 MCP Sink 是必须保持的依赖边界。随后一次缺少因果链的候选错误地在 BehaviorResolver 与
  deployment config 之间插入了独立 ExecutionAdapter。D-523 将结构重新压平：具体 Organization operation 直接实现为
  BehaviorResolver method；Agent-backed method 读取 `core.organization.<behavior>` 并选择完整 Agent definition，Job/route
  只做薄调用。Rumination 从 `OrganizationManager` 迁移到 `RuminationBehaviorResolver`；exact mutation/read methods 仍可
  脱离 Agent config/runtime 直接调用。D-524 随后撤回按内部机制罗列的确定性 Acceptance：整组验收从普通 info-base
  input 与 automatic Jobs 黑盒触发，只观察 graph/use result、Job lifecycle 和必要 diagnostics。类型/schema/import/transaction
  等结构保障回到 Implementation Plan/preflight/implementation verification；小型真实语料只形成带 residual 的 best-effort
  Human whole-run disposition，不冒充穷尽证明或未定义的可靠性 SLO。D-525 接受“多地区服务配置与运行证据”和“多方
  事故复盘与修复建议”两个相互交织的 information worlds；实现时优先把 content/manifest 保存为独立 fixture files，但
  这不是 Acceptance 条件，也不批准 generic corpus framework。
- **Decision authority**: [D-461–D-470](../../decisions/D461-D470.md)、
  [D-471–D-480](../../decisions/D471-D480.md)、[D-481–D-490](../../decisions/D481-D490.md)、
  [D-491–D-500](../../decisions/D491-D500.md)、[D-501–D-510](../../decisions/D501-D510.md)、
  [D-511–D-520](../../decisions/D511-D520.md)、[D-521–D-530](../../decisions/D521-D530.md)。Reserved range D-461–D-540；
  create later shards only when the next accepted decision exists。

## Delivery Route

```text
Nowledge study + transfer audit          # Product complete
  -> Technical design <-> Acceptance    # active
  -> Implementation Plan
  -> Preflight
  -> Impact Handshake + Sir explicit start
  -> Execute
  -> Verify / Promote / closure
```

The parent task still has no single global phase；this route belongs specifically to the Nowledge implementation vertical。
Technical and Acceptance may expose Product gaps and reopen them，but may not replace the accepted Product model with an easier
implementation shape。

## Human / Agent Boundary

- Agent 自主完成一手资料核实、反例、模型拆解、候选方案、代码/依赖调查、可丢弃 spike、artifact 更新和阶段内连续推进。
- Human review 用于 material Product / Technical / Acceptance 取舍、authority/scope 变化、多个 credible 方案选择，或
  Agent 缺少 Human-owned information / direction。
- 源码 mutation 已由 D-527 授权；本轮 task-packet commit 已明确授权，后续 implementation commit 仍需另行显式命令。
- Sir 接受或纠正 material decision 后，同一轮更新 decision 与其 semantic owner，然后继续工作；不把普通研究问题
  转化成逐步确认点。
- 与 Sir 沟通时，除代码标识、专有名词和双方已经确立的 glossary 外使用中文；不要为了沿用文档术语突然切换英文。

## Artifact Navigation

- [Unit glossary](glossary.md)：本 unit 的稳定讨论词表，区分组织模型、operation、consumer、执行适配器及已接受的
  exact models；同时列出已弃用或必须限定的词，避免实现位置和产品语义再次混淆。
- [Organization from first principles](organization-first-principles.md)：从 info-base authority、collect/use 区分与未来 use
  不可知性演绎 Organization，并以 distinction realization causal/time axis 串联 model、candidate、evidence、judgment、
  graph authority 与 later-use affordance；D-498 accepted foundation。
- [Product design](product-design.md)：accepted Product behavior、model、boundary 和 live material choice。
- [Insight Detection Product shard](product/insight-detection.md)：D-485 closed analysis。
- [Working Memory Product shard](product/working-memory.md)：D-486 closed downstream-projection boundary。
- [Skill Suggestions Product shard](product/skill-suggestions.md)：D-487 closed synthesis/promotion boundary。
- [Rule Suggestions Product shard](product/rule-suggestions.md)：D-488 closed descriptive/normative-force boundary。
- [Memory Freshness Product shard](product/memory-freshness.md)：D-489 closed freshness/currentness/support boundary。
- [Organization Extension pressure](product/organization-extension-pressure.md)：D-490 accepted cross-unit Product pressure；
  exact contribution mechanism deferred to one approved concrete behavior。
- [Community Detection Product shard](product/community-detection.md)：D-491 closed structural-projection boundary。
- [Flags / Memory Maintenance Product shard](product/flags-memory-maintenance.md)：closed D-492；no independent behavior，P-032
  retained。
- [Info-base representation lens](representation-lens.md)：用 Block / Resolver / Relation / Graph 的现有 authority 模型
  判断 Nowledge mechanism 应转移为 information、contextual graph meaning、runtime interpretation 还是 application projection。
- [Mechanism inventory](mechanism-inventory.md)：官方 Background Intelligence 行为的 reviewed / active / queued 路由；
  只管理研究覆盖，不拥有 Product design。
- [Knowledge Evolution evidence](evidence/nowledge-knowledge-evolution.md)：official evidence、inference、unknown 和 freshness。
- [Crystals evidence](evidence/nowledge-crystals.md)：official synthesis、source-dependency and candidate evidence with
  D-471–D-475 closure。
- [Memory Links evidence](evidence/nowledge-memory-links.md)：official relation/reason/authority evidence and D-476 closure。
- [Ontology evidence](evidence/nowledge-ontology.md)：official vocabulary/type/open-world evidence and D-478 no-transfer closure。
- [Entity extraction evidence](evidence/nowledge-entity-extraction.md)：official trigger/output/search evidence and D-479
  closure。
- [Memory Compaction evidence](evidence/nowledge-memory-compaction.md)：official candidate/action evidence、existing InKCre
  duplicate boundary and D-480 closure。
- [Automatic Labeling evidence](evidence/nowledge-automatic-labeling.md)：official assignment/search/consolidation evidence and
  D-482 closure。
- [Memory Type Review evidence](evidence/nowledge-memory-type-review.md)：official primary-type/reclassification evidence and
  D-483/D-493 closure。
- [Insight Detection evidence](evidence/nowledge-insight-detection.md)：official cross-domain/pattern/provenance evidence、
  unknowns and D-485/D-493 closure。
- [Working Memory evidence](evidence/nowledge-working-memory.md)：official generation、scope、injection、edit/history evidence
  and D-486 closure。
- [Skill Suggestions evidence](evidence/nowledge-skill-suggestions.md)：official detection、compilation、testing、activation and
  provenance evidence and D-487/D-493 closure。
- [Rule Suggestions evidence](evidence/nowledge-rule-suggestions.md)：official rule semantics、scope、suggestion、review and
  Context delivery evidence and D-488 closure。
- [Memory Freshness evidence](evidence/nowledge-memory-freshness.md)：official score、ranking、access and lifecycle evidence with
  D-489/D-493 closure。
- [Community Detection evidence](evidence/nowledge-community-detection.md)：official clustering、summary、search and graph
  evidence and D-491/D-493 closure。
- [Flags / Memory Maintenance evidence](evidence/nowledge-flags-memory-maintenance.md)：official flag meanings、review、cleanup
  and D-492 closure。
- [Nowledge transfer audit](audit/nowledge-transfer-audit.md)：closed D-493；已检查并修正过度学习、照搬和不必要的新抽象。
- [Technical design](technical-design/index.md)：整组功能的当前实现恢复、owner/topology constraints 与共同缺口。
- [Model realization map](technical-design/model-realization-map.md)：依据 D-498 区分 exact model、family/pattern、invocation
  law、candidate specialization 与 invariant，并逐项投影 semantic question、graph distinction 和 later-use consumer。
- [Minimal mechanisms and consumers](technical-design/minimal-mechanisms-and-consumers.md)：从现有代码能力与 D-499 exact
  models 推导干净的 Relation content、graph-owned synthesis basis、model commands、behavior-owned automatic Jobs 和最小无状态读取
  投影；当前 material Technical review。
- [Synthesis operation contract](technical-design/synthesis-operation-contract.md)：逐项推导 synthesis 的候选、证据、判断、
  提案、命令、机械重放以及 `edited + synthesis` 的 best-effort 重新应用闭环。
- [Scoped supersession operation contract](technical-design/scoped-supersession-operation-contract.md)：逐项推导 whole-Block
  dominance 的可寻址性边界、候选/SOP、transaction-visible cycle check 与 bounded current/history Resolver projection。
- [Non-dominating refinement operation contract](technical-design/non-dominating-refinement-operation-contract.md)：推导
  additive lineage 的 whole-Block、scope compatibility、information-role、non-dominance、exact command 与普通图遍历边界；
  D-507 accepted。
- [Evidence stance operation contract](technical-design/evidence-stance-operation-contract.md)：推导 evidence/assertion role、
  proposition/scope alignment、provenance-preserving `supports`/`challenges`、mixed-evidence abstention、exact command 与无
  truth-score use 边界；D-508 accepted。
- [Existing-referent anchoring operation contract](technical-design/existing-referent-anchoring-operation-contract.md)：推导
  `refers to` 的 identity-bearing target、竞争 referent 排除、指称片段的 whole-Block 边界、exact command 与跨来源 query
  path；D-509 accepts `source --has mention--> fragment --refers to--> referent`，明确不创建 Entity。
- [Provenance-aware duplicate assertion operation contract](technical-design/provenance-aware-duplicate-assertion-operation-contract.md)：
  推导完整断言、命题/适用范围、同一 provenance occurrence、非独立性、canonical edge、重放与 count-once consumer；当前
  D-511 accepted exact model；D-510 已将 input-induced partition 修正为从输入 seeds 沿 exact Relation 有界补全连通分量。
- [Technical / Acceptance coverage reconciliation](technical-design/coverage-reconciliation.md)：六个 exact models 关闭后的
  whole-set audit；区分可直接进入 Implementation Plan 的已关闭设计与仍需 Technical 决策的缺口。当前先关闭
  `candidate for` 的自动 carrier：修正先前遗漏 rumination 的四路径计数，为 rumination 提供完整的独立自动 Job；各
  behavior-owned Job 都可把指向自身 descriptor 的 edges 作为高优先级 seeds，而不是增加 candidate-only Job、同步 cascade
  或 generic dispatcher。随后按真实 caller/authority 分类原地 Block mutation 的
  append-only 边界。
- [Cross-model organization assistance](technical-design/cross-model-assistance.md)：评审可复用 referent/scope/scoped-
  assertion materialization、Relation-to-whole-Block law，以及通过 exact behavior Block 传递非命令式候选的最小拓扑。
- [Behavior Resolver and graph execution entry](technical-design/behavior-descriptor-resolver.md)：比较信息 Resolver methods、
  exact behavior Resolver 与 Source-like pointer；当前推荐 behavior Block 的 exact Resolver type 同时作为 identity 与实际
  `consider_candidate()` orchestration carrier，不复制 registry，并澄清“Relation 传导力/动态图”不等于任意代码执行。
- [Append-only information edit boundary](technical-design/append-only-information-edit-boundary.md)：从真实 Block mutation
  callers 按 authority 分类并比较五种实施档位，而不是按 Core/Extension 分类；D-513 只让本 unit 自有 Organization
  operations 遵守 append-only output contract，把它保留为 ecosystem guidance，不改 generic PATCH、不迁移现有 producers、
  不新增共享 helper 或全局 enforcement。
- [Exact Tools and behavior descriptors](technical-design/exact-tools-and-behavior-descriptors.md)：D-515 让七个 exact
  behaviors 各有独立 Job，并将六个模型 mutation methods 放在相应 concrete BehaviorResolver；单一 candidate Agent Tool
  动态分派到 target Resolver。D-516 接受 exact Resolver type + empty content descriptor shape；D-517 接受 registration-
  aligned lazy materialization。D-518 删除 BehaviorReport 与统一 effect result：Job 不 import Agent/Thread、不认识 Tool
  IDs，只调用 BehaviorResolver operation；正常完成不写 Job.state。graph、现有 JobStatus 与结构化 logs/traces 分别承担
  效果、生命周期和诊断。
- [Automatic Organization Job contracts](technical-design/automatic-job-contracts.md)：D-519 从现有 Job/Cron 依赖方向接受七条
  薄 Handler、BehaviorResolver-owned stateless seed selection、一个 `max_seeds` occurrence bound、candidate-local failure
  与两个不重复 Job lifecycle 的 structured diagnostic events。
- [Duplicate component query](technical-design/duplicate-component-query.md)：定义 seed partition + spanning proof + missing/
  truncation query result 与 count-once use law；不为 Organization behavior 强行绑定具体 consumer，synthesis 只保留为
  集成案例；D-520 accepted。
- [Relation content ownership](technical-design/relation-content-ownership.md)：owner-local constants 解决 runtime string
  scatter，exact migration discipline 解决 persisted rename；不建 registry。并提出 supersession lineage read 从 information
  Resolver base 移到 behavior Resolver 的依赖方向修正；D-520 accepted。
- [Agent exploration tools](technical-design/agent-exploration-tools.md)：D-521/D-522 accepted；三个 owner-coherent 元工具
  组合 hybrid retrieval、完整 Resolver typed capabilities 与全部 Graph Navigation methods；不增加 `Information`
  wrapper、不压缩 Resolver、不依赖 MCP Sink，初始 candidate 也不成为视野上限。
- [BehaviorResolver Agent definition selection](technical-design/behavior-deployment-configuration.md)：D-523 accepted；
  `core.organization.<behavior>` 只选择完整 Agent definition，operation 直接实现为 concrete BehaviorResolver method，
  不新增 ExecutionAdapter；rumination 从 `OrganizationManager` 迁移到 `RuminationBehaviorResolver`。
- [Black-box Acceptance structure](acceptance/index.md)：D-524 accepted；从普通 info-base input/config 到 automatic Jobs，再
  到 graph/use result、Job lifecycle 和必要 diagnostics 的 best-effort E2E 观察。内部机制检查不再冒充 Acceptance。
- [End-to-end corpus](acceptance/semantic-corpus.md)：D-525 accepts 两个 realistic information worlds、无 Human focal input
  的 whole-set automatic execution、Human before/after/use review 与明确 residual；不是逐 behavior 机械打分表。Fixture
  content/manifest 优先独立于 test code，但不建设共享 framework。
- [Implementation Plan](implementation-plan.md)：D-526 accepted whole-unit dependency order、源码落点、验证与交付边界；
  Resolver reflection 明确落在 ResolverManager 而非 Resolver base。
- [Implementation Preflight](implementation-preflight.md)：已核对真实源码 owner/caller、MCP overlap、Resolver method surface、
  Graph indexes、Agent/config operator path、baseline 与 database environment residual；结论 ready with residuals。
- [Impact Handshake](impact-handshake.md)：D-527 accepted implementation 的 `From -> To`、blast radius、不变量、验证和未授权
  边界；源码实施已开始。
- [Implementation Evidence](implementation-evidence.md)：记录当前已实施 surfaces、静态/collection evidence、数据库与真实
  provider residual；它不把尚未执行的黑盒旅程写成已通过。
- [Agent definition selection correction](technical-design/agent-adapter-boundary.md)：D-501 撤回 run-time Tool policy；多个
  purpose-built definitions 已按场景完整组合 prompt、model、Tools 和预算，执行路径只需选择正确 definition。
- [Relation semantic contract](technical-design/relation-semantic-contract.md)：从 neutral graph、heterogeneous models、
  Agentic judgment 和 durable use 推导 model-specific Tool、干净 Relation content 与 exact consumer 的责任边界；当前
  material Technical review。
- [Behavior carrier and dependency direction](technical-design/behavior-carrier.md)：核实现有代码没有统一 behavior 实体，
  区分 execution/code/durable carriers，并评审 Agent/Tool/Job adapters → exact operation → Resolver/InfoBase 的单向依赖与
  Resolver 定向复用方案。
- [Acceptance](acceptance.md)：D-524/D-525 已关闭的 best-effort black-box whole-feature-set 验收边界。
- [Decision shard D-461–D-470](../../decisions/D461-D470.md)：accepted material decisions 的单一 task-state authority。
- [Decision shard D-471–D-480](../../decisions/D471-D480.md)：Crystals and later mechanism decisions。
- [Decision shard D-481–D-490](../../decisions/D481-D490.md)：cross-mechanism Agentic execution and later decisions。
- [Decision shard D-491–D-500](../../decisions/D491-D500.md)：Community Detection、Flags、transfer-audit closure and vertical-
  lifecycle corrections。
- Verify / Acceptance active；实现与静态证据已收敛，等待可用 database/provider 运行 PostgreSQL journeys 与 Human-reviewed
  two-world black-box Acceptance；环境不可用期间保留 residual，不回写为 Product/Technical failure。

本 packet 只投影范围、当前阶段、active edge 和导航，不重复 design、evidence、decision 或 completed-work history。
