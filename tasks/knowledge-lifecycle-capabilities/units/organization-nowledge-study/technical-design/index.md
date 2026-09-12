# Organization Nowledge Vertical — Technical Design

- **State**: Technical material boundaries closed under D-495–D-523；best-effort black-box Acceptance closed under D-524/D-525；
  whole-unit [Implementation Plan](../implementation-plan.md) closed under D-526。Preflight is active。
- **Inputs**: accepted Product design and D-493 transfer audit；current core-py Organization、Agent、Resolver、InfoBase、retrieval、
  Job/Cron、Peer and Extension implementations。
- **Delivery boundary**: one Technical design and one delivery loop cover the complete feature set。The behavior boundaries below
  are semantic/runtime responsibilities，not delivery slices or partial-product gates。

## Product Responsibilities To Realize

Technical placement is subordinate to the accepted
[Organization first-principles derivation](../organization-first-principles.md)。The Product inventory is now being reclassified
through the [model realization map](model-realization-map.md)：`behavior` below remains working shorthand rather than approval of
a runtime entity、common interface or Agentic execution shape。

| Product responsibility | D-498 role | Required durable/use result |
| --- | --- | --- |
| Scoped supersession | exact model | scoped dominance becomes current/history meaning while all information remains |
| Non-dominating refinement | exact model | additive lineage remains traversable without false dominance |
| Evidence stance | exact model | support/challenge meaning remains scoped、attributed and non-destructive |
| Provenance-preserving n-ary synthesis | exact model/method | a qualified set produces reusable derived information with its complete basis |
| Dependency response | synthesis reapplication law | relevant source-graph change reconsiders an exact synthesis without adding a Crystal lifecycle |
| Contextual linking | model family | an exact link contract makes otherwise-hidden interpretive context reusable |
| Existing-referent anchoring | exact model inside linking family | implicit source meaning may resolve and anchor to existing identity-bearing information；ambiguity remains unresolved |
| Duplicate-assertion relation | exact model | copies of one provenance occurrence become explicitly non-independent without physical merge |
| Normative-authority separation | cross-model invariant | recurrent descriptive practice never becomes operational force without an entitled source/consumer |

The exploratory Agentic topology is an available realization for strong-semantic components that demonstrably need iterative
exploration/action，not the default Organization architecture or another Product behavior。Candidate heuristics、bounded direct
AI judgment and structural projections remain exact behavior choices。

## Recovered Current Topology

| Current capability | Actual boundary | Consequence for the complete feature set |
| --- | --- | --- |
| Explicit rumination | focal Resolver text plus direct-relation labels run one configured Agent | proves Agent + Resolver + graph-command composition，but depends on explicit focal input and cannot organize automatically |
| System-driven media interpretation | one exact Job scans a behavior-owned missing-output condition and runs modality-specific Agents | proves parallel behaviors may own different selectors/configuration without a universal dispatcher；its behavior-specific report is not a universal precedent |
| Agent runtime | persisted definition selects prompt/model/exact Tool IDs；runtime is graph-blind | every behavior owns its SOP and Tool selection；AgentManager does not acquire Organization policy |
| Agent graph tools | Resolver graph drafting and additive `submit_graph` are the only registered domain capabilities | Agents cannot currently search、resolve arbitrary candidates or navigate beyond initial context |
| Retrieval/navigation | lexical/semantic retrieval return real graph entities；graph navigation returns bounded neighborhoods and paths | the complete feature set should adapt these capabilities instead of reimplementing candidate search/traversal |
| Graph command | signed-ID `GraphForm` creates derived Blocks and relations among new/existing Blocks | all accepted graph shapes fit current authority；no new Entity/type/Crystal storage model is needed |
| Jobs/Cron | exact typed handlers own bounded execution；Cron materializes independent occurrences | automatic work can reuse this runtime；graph、JobStatus and structured logs already separate effects、lifecycle and diagnosis |
| Extension runtime | Extensions publish routes、Peer inbounds、Sources and Resolvers；type registration is process-monotonic | Organization extensibility remains an exact unresolved ownership/interface question，not permission for a generic hook |

## Whole-Set Execution Topology

```text
behavior-owned automatic trigger / explicit diagnostic invocation
  -> behavior-owned bounded candidate seed
     -> exact behavior SOP + resolved context
        -> least-powerful sufficient judge
           |-> deterministic / bounded direct AI assessment
           `-> Agent may search、resolve and navigate when required
              -> behavior-valid unresolved / no-op
              `-> typed behavior proposal / command
                 -> ordinary Block / Relation persistence
                    -> existing or exact model-owned use projection
                       -> later graph/use result
```

Evolution、synthesis、linking and duplicate handling each instantiate this topology independently。There is no runtime that asks
“which Organization method should run？” Shared code may expose graph observation、Agent exploration and safe graph commands，but
cannot select semantic outcomes or collapse no-op laws。

## Critical Graph Contract

The previous behavior-owned content-envelope proposal lacked its causal chain：it identified the need for exact producer/
consumer semantics but did not explain why behavior ownership follows from a neutral graph、heterogeneous behaviors、Agentic
judgment and extension requirements。

The full causal analysis and alternatives now live in
[Relation semantic contract](relation-semantic-contract.md)。The current conclusion is narrower than either extreme：the graph
persists concise Relation meaning without namespace、implementation owner、version suffix or a common payload envelope；the exact
Organization model owns applicability、SOP、model-valid spelling/direction、state law and operational force。Command/API versions
remain outside graph meaning。A `Relation.resolver` still needs a separate demonstrated generic dispatch/indexing requirement。

## Behavior Carrier And Dependency Direction

“Behavior-owned” names a responsibility，not a planned `OrganizationBehavior` entity。The current code and proposed minimal
topology are detailed in [Behavior carrier and dependency direction](behavior-carrier.md)：outer Agent/Tool、Job、direct-AI or
deterministic adapters depend inward on exact behavior modules/Managers；those modules depend downward on Resolver/retrieval/
InfoBase and never reverse-import Agent mechanics。Resolver remains the heterogeneous information interpretation and exact
derived-Block contract rather than acquiring cross-Block Organization production policy。A bounded read of persisted graph
meaning belongs to the exact BehaviorResolver when it interprets Organization vocabulary；set-level neutral topology remains a
Graph Navigation query and request-specific use remains application-owned。

D-505 closes the D-504 realization question in
[Behavior Resolver and graph execution entry](behavior-descriptor-resolver.md)：`candidate for` 为 exact behavior 提供了首个
已证明的图内 identity 与 runtime invocation 用例。Current code refutes a pure-read Resolver premise；the accepted design
uses each behavior Block's exact Resolver type as both identity and actual `consider_candidate()` orchestration carrier。It does
not add Organization methods to information content Resolvers，nor duplicate ResolverManager with a Source-like pointer registry；
exact graph commands remain independently callable beneath the concrete Resolver。

## Shared Technical Needs Proven By The Complete Set

### 1. Automatic invocation without a shared change lifecycle

The feature set cannot depend on a Human choosing a theme、pair or source set。That requires system-driven invocation，but does
not imply that every graph mutation must enter one durable event stream or that Organization promises exhaustive classification
of the graph。

The current recommendation is **independent exact periodic Jobs over current graph authority**：rumination、supersession、
refinement、evidence stance、synthesis、existing-referent anchoring and duplicate assertion each own a bounded candidate scan、
configuration、Agent SOP and structured diagnostics。They may prioritize recent Block/
Relation changes、missing positive outcomes、semantic candidates or derivation dependencies according to their own semantics。
An explicit focal invocation may remain a diagnostic/manual accelerator but is not the ordinary Product dependency。

Do not add a shared graph-change log、per-behavior evaluation ledger or cascade coordinator now：

- Product accepts candidate mechanisms as heuristics，not complete graph classification；
- each behavior needs different applicability evidence，so one event payload does not remove its current-graph scan；
- a durable consumer ledger makes no-op/unresolved into a second lifecycle and needs invalidation rules for every relevant
  neighborhood change；
- Organization-authored output would re-enter a shared event stream and require generic loop/termination semantics that D-475
  explicitly leaves unapproved；
- existing exact Job/Cron plus behavior-owned missing/stale/current predicates already cover automatic bounded work。

Repeated semantic reconsideration is allowed but bounded；persisted graph effects must be idempotent or append-only according to
the behavior。A run logs only what it selected in that invocation and never claims complete evidence coverage。If measured
cost or missed-value evidence later shows current-graph scans are insufficient，that concrete failure can justify a narrower
checkpoint/support record。

### 2. Agent-readable info-base exploration

Strong-semantic behavior needs bounded Tools for：

- lexical/semantic retrieval over existing Manager contracts；
- resolving one selected Block to faithful text/label；
- reading a bounded directed neighborhood and exact Relation meanings；
- optionally following a bounded path when the behavior SOP requires it。

These are reusable Agent capabilities，not a candidate protocol or generic Organization behavior。The first implementation use
must define the exact schemas and bounds；no duplicate retrieval engine is introduced。

### 3. Behavior-owned graph commands and replay

Current `submit_graph` deliberately inserts additive Blocks and Relations。The complete automatic feature set additionally needs：

- idempotent exact Relation assertion for replayed evolution/linking/duplicate outcomes；
- append-only derived information with recorded source basis for synthesis；
- a way to avoid duplicating the same derived result after an uncertain execution boundary without overwriting history；
- output validation that enforces each behavior's allowed graph shape while leaving Relation content open where Product requires
  exact contextual meaning rather than a registry。

Changing generic `GraphForm` semantics is not the minimum safe solution because existing rumination documents additive replay。

### 4. Use effects and read owners

Persisting a Relation is insufficient when the Product value depends on a later distinction：

- supersession needs a scoped current/history projection；
- evidence stance needs support/challenge provenance without collapsing disagreement；
- duplicate assertion needs evidence consumers to count one provenance occurrence once；
- synthesis and contextual links must remain traversable and Resolver-readable。

These projections reuse their natural read owner：a focal-Block interpretation may be a Resolver method；neutral topology over a
caller-supplied Block set belongs to Graph Navigation；request-specific counting/ranking remains Application。Where no consumer
exists，the Technical design must add the narrow consuming contract inside this same vertical rather than declaring graph
insertion to be acceptance by itself。

### 5. Delivery and Extension ownership

The generalized information behaviors are not automatically an Extension merely because Nowledge inspired them。Conversely，
Core ownership does not satisfy the accepted requirement that Organization can grow through Extensions。For the whole feature
set，Technical design must independently place：

- behavior semantics and execution owner；
- shared Agent/graph capabilities；
- automatic trigger and availability owner；
- any exact Extension contribution/influence seam；
- durable Product and Unit-TDD truth。

No generic Organization registry is admitted unless the complete set demonstrates a smaller solution cannot preserve these
owners。

## Technical Invariants

1. One feature set has one Acceptance and delivery closure；implementation order does not create partial shipped products。
2. Behaviors remain parallel semantic owners even when they share runtime capabilities。
3. Resolver interpretation、retrieval candidates and LLM output are evidence/proposals；only validated graph commands persist。
4. Initial candidates normally seed rather than cap Agent exploration。
5. Source Blocks remain authority；Organization output is additive/append-only and provenance-preserving。
6. Automatic replay cannot silently duplicate exact Relations、derived results or evidence multiplicity。
7. No physical merge、source rewrite、new Entity/type ontology、Human review lifecycle、generic archive state or relation-force
   engine is introduced。
8. The graph、JobStatus and structured diagnostics separately expose persistent effects、execution lifecycle and bounded
   selection/no-op/replay/failure reasoning；no BehaviorReport or successful Job-state snapshot duplicates them。

## Active Technical Edge

D-500 accepts [minimal mechanisms and consumer contracts](minimal-mechanisms-and-consumers.md)：clean semantic Relation content、
graph-owned synthesis basis over ordinary text Blocks、independent behavior-owned Job paths、shared read-only Agent exploration plus model-
specific mutation Tools，one focal-Block supersession Resolver read and one bounded connected-components Graph Navigation query。
D-501 closes [Agent definition selection correction](agent-adapter-boundary.md)：multiple purpose-built definitions already
compose prompt、model、Tools and budget per situation，so no run-time required/allowed Tool policy is added。The active edge returns
to exact per-model candidate/evidence/judgment/proposal/command contracts and synchronized Acceptance，without introducing a
shared Organization model interface。[Synthesis operation contract](synthesis-operation-contract.md) is the first exact-model
derivation。It identifies `text + exact source basis` only as a mechanical replay key and，under D-502，restores the accepted
append-only edit path：old `--edited-->` new plus `synthesis`-guided reapplication produces no-op or a new synthesis Block。
External bytes changing silently behind an unchanged Storage pointer remain an explicit best-effort defect rather than a reason
to add a universal stable-address/version subsystem。D-503 closes this synthesis contract end to end and corrects its exact
source-basis Relation content to `synthesis`；the next exact derivation is scoped supersession。

[Scoped supersession operation contract](scoped-supersession-operation-contract.md) is closed by D-506。Its
candidate keeps scope in endpoint meaning rather than Relation payload，therefore permits `supersedes` only when dominance covers
the complete addressable predecessor；it also separates semantic succession from database record time and defines a transaction-
visible cycle check for the exact command plus a bounded focal-Resolver current/history projection。Generic Relation writes still prevent
a global no-cycle guarantee，so the projection reports any observed cycle instead of inventing a current frontier。The next
exact-model derivation is non-dominating refinement。

[Non-dominating refinement operation contract](non-dominating-refinement-operation-contract.md) is closed by D-507。It
permits explicit scope narrowing while the predecessor remains valid outside that scope，requires information-role
continuity and material additive gain，and keeps `refines` separate from dominance、evidence and synthesis provenance。Its exact
command only validates endpoints、visible cycle and fetchsert identity；ordinary graph traversal supplies additive-lineage use。

[Evidence stance operation contract](evidence-stance-operation-contract.md) is closed by D-508。It treats
`supports` / `challenges` as source-attributed defeasible evidence bearing rather than text agreement、truth labels or
currentness；it requires whole endpoints、evidence/assertion roles、proposition/scope alignment、inferential relevance、recoverable
provenance and one determinate stance。Ordinary graph use preserves disagreement without a global score。

[Existing-referent anchoring operation contract](existing-referent-anchoring-operation-contract.md) is closed by D-509。It no
longer places `refers to` directly on a composite source Block。It materializes only the resolved selected text as an
ordinary referring-fragment Block，then writes `source --has mention--> fragment --refers to--> existing referent`。This keeps the
stable predicate queryable and makes the exact referring part recoverable without generic Entity extraction、span schema、
same-as merge or a special read surface。The next exact-model derivation is provenance-aware duplicate assertion。

[Provenance-aware duplicate assertion operation contract](provenance-aware-duplicate-assertion-operation-contract.md) is closed
by D-511。It limits `duplicates assertion` to complete equivalent assertions derived from one assertion-relative source
occurrence，keeps every Block/context，uses lower-ID direction only as storage normalization，and leaves representative/counting
to current-call use。It also exposes a defect in D-500's input-induced component query：two seeds may connect through a duplicate
outside the input set。D-510 accepts bounded full-component expansion from the seeds and explicit truncation rather than
overstating evidence independence。Technical work now reconciles the complete model set against runtime、Extension and
Implementation-plan prerequisites rather than deriving another exact behavior。

[Technical / Acceptance coverage reconciliation](coverage-reconciliation.md) is the active whole-set review。It finds no missing
Product model or database entity：the remaining additive implementation surfaces are exact commands、BehaviorResolvers/
descriptors、Agent adapters、seven behavior-owned Organization Jobs、two bounded reads and their
schemas/evidence。The whole-set Technical review found two real boundaries。First，D-504 accepts `candidate for` targets including
rumination，but no current automatic carrier consumed rumination candidates；D-512 corrects the earlier candidate-only path，and
D-515 further removes its combined Evolution Job。Every exact behavior now owns its automatic Job and may treat edges targeting
its own descriptor as high-priority seeds；there is no candidate-only Job，synchronous cascade or generic dispatcher。The
remaining boundary is append-only address meaning：current
generic and producer-specific in-place Block mutations can
retroactively change persisted Organization Relations and synthesis basis。[Append-only information edit boundary](append-only-information-edit-boundary.md)
now classifies the real callers by authority rather than by Core/Extension ownership。Its semantic guidance treats in-place
sync as the clean case only for a rebuildable projection backed by another local persisted authority；currently only the Source
anchor is proven。After comparing ROI levels，D-513 stops at Organization-local append-only
outputs plus ecosystem guidance：no generic PATCH change、producer migration、shared helper or global enforcement。Mutable upstream
history remains a stated best-effort residual until a concrete owner-specific use failure justifies a higher level。

[精确修改入口与 Behavior Descriptor 物化](exact-tools-and-behavior-descriptors.md) 的 Job/ownership 部分由 D-515 关闭：
七个 exact behaviors 各自拥有 Job，图中不增加 generic evolution descriptor；六个模型修改方法由相应 concrete
BehaviorResolver 拥有，单一 candidate Agent Tool 动态分派到 target Resolver。D-516 accepts exact Resolver type + empty
content as descriptor identity；post-registration global sync is rejected。D-517 binds the single Tool to a
dynamic enum of registered BehaviorResolver types and lets the selected class lazily fetchsert its descriptor inside the real
candidate transaction。D-518 removes the unconsumed BehaviorReport、shared `changed` and successful Job-state snapshot；graph、
JobStatus and structured logs own effects、lifecycle and diagnosis respectively。D-519 closes the seven Jobs'
invocation、seed、bound、failure and diagnostic contracts while keeping behavior semantics on each BehaviorResolver。

[七条自动 Organization Job 的运行合同](automatic-job-contracts.md) 从现有 `JobHandler -> JobManager -> Cron` 实现反推
最小边界。D-519 修正“Job owns candidate law”的旧简写：Handler 只检查并调用 exact BehaviorResolver；Resolver
拥有 stateless seed selection、判断/Agent orchestration、graph mutation 和过程日志。七种 Job type 保持独立，但只共享
一个 `max_seeds` occurrence bound；no BehaviorReport、cursor、candidate lifecycle 或 Job-to-Thread dependency。

[重复断言的连通分量读取与解释边界](duplicate-component-query.md) 关闭 D-510 的 query projection，而不强行寻找当前
具体消费者：任何 evidence-sensitive use 都可把完整 `duplicates assertion` component 解释为一次来源贡献；synthesis
只是必须遵守这一规律的集成案例之一。Graph Navigation candidate 返回 input-seed partition、spanning proof、missing
seeds 与 block/relation truncation；当前没有外部消费者，因此不新增 HTTP/MCP transport、component state 或 persisted
representative。

[Relation content 的代码权威与消费方式](relation-content-ownership.md) 由 D-520 接受：behavior semantic authority、
owner-local persisted-token constant、vocabulary-blind graph 和 current consumer 各有独立责任。Writer/readers 共享 exact
behavior module 的 `Final` 常量；只有非平凡模型解释才增加 typed read API。Persisted token rename 仍需 migration，不能靠
改常量。该检查同时把 supersession projection 从 information Resolver base 修正到
`SupersessionBehaviorResolver.read_lineage()`。

[Agent 初始候选之外的探索工具](agent-exploration-tools.md) 由 D-521/D-522 接受：`retrieve`、`resolver` 与
`graph_retrieval` 三个 owner-coherent 元工具分别组合 hybrid retrieval、完整 Resolver typed capabilities 与全部 Graph
Navigation methods。`read_blocks -> label + text` 已因压缩 Resolver 能力而撤回；Graph methods 不再逐个增加 Tool ID。
当前不采用 PostgreSQL/Cypher 是 ROI 判断，不构成能力禁令；Organization 和 MCP Sink 彼此无依赖。

[BehaviorResolver 的 Agent definition 选择](behavior-deployment-configuration.md) 由 D-523 接受：具体 Organization
operation 直接实现为 concrete BehaviorResolver method；Agent-backed method 读取 `core.organization.<behavior>` 并选择
完整 Agent definition，Job/route 保持薄调用。这里不新增 ExecutionAdapter 抽象。Rumination 从 `OrganizationManager`
迁移到 `RuminationBehaviorResolver`；exact mutation/read methods 仍可脱离 Agent config/runtime 直接调用。
