# Graph Navigation Retrieval

## Control

- **State**: Complete — implementation、owner-separated publication、exact-head CI/CD and actual Preview shell closure
  completed on 2026-08-23。
- **Objective**: 让用户或下游能力从一个已定位的 graph entity 出发，取得可理解、可继续沿方向导航的
  既有 Blocks/Relations，而不要求加载整个 info-base graph。
- **Current work**: closed；return to implementable-unit selection。
- **Decision authority**: [task decision register](../../decisions/index.md)；本文件只投影当前 unit 状态、
  working hypotheses 与 discussion queue。
- **Execution gate**: passed on 2026-08-18。The approved Impact Handshake covers Hub contract/corpus、peer-local managers、
  endpoint indexes、Resolver preview hard cut、application routing/Search、Graph View rewrite and proportionate design-system
  changes。

## Implementation checkpoint — 2026-08-18

- Hub Product TDD and one machine-readable topology corpus are drafted on the dedicated Hub branch；they remain uncommitted
  until owner-separated review/push。
- core-py owns the presentation-neutral public manager、read models、endpoint query primitives and endpoint indexes。
  PostgreSQL integration passes on migration head `50b2c08dd267`；a transaction-local sparse 50k probe selected
  `relations_from_id_desc_idx` and completed the bounded page in under 1 ms on the development runtime。
- `@inkcre/core` implements the same contract directly over PostgREST。Its unit corpus and a real PostgREST smoke both pass；
  the smoke produced a 3-Relation endpoint-closed neighborhood and a 2-hop outgoing path without RPC or Peer delegation。
- Resolver registration now requires distinct preview/full renderers over the same solved-content authority。Core、Mail and
  Twitter in-scope registrations have bounded interaction-free previews；old `sink/graph` and app-owned full-graph/community
  machinery are hard-cut。
- client-web owns role-named scene routing、application Recall/Search、entity-local inspectors and the rewritten bounded
  Graph navigation host。The actual local shell now passes random/isolated initialization，4-Block/3-Relation focal
  navigation，soft outgoing emphasis，3-Block/2-Relation shortest path，modeless Relation/Block/Solved Content outlets and
  browser-back restoration against the converged PostgREST runtime。
- design adds only the proven generic `InkPopup.scrim` capability (default remains modal) plus focused evidence and a
  Changeset。A generic SearchBar was not promoted because the second proven presentation consumer did not justify a stable
  abstraction yet。
- Implementation preflight exposed and fixed three delivery-baseline defects needed to run the actual shell：development
  Compose now builds the artifact-free `runtime` stage；development readiness accepts additional advertised capabilities；
  readiness/reset explicitly invoke `python scripts/container.py` after the image ENTRYPOINT hard cut。These are deployment
  contract fixes, not Graph business adaptations。
- The browser vertical exposed a fourth distributed-runtime defect：a JWT issued at the caller's exact current second can be
  rejected by a slightly slower PostgREST clock as `JWT issued at future`。The signing boundary now backdates `iat` by five
  seconds while retaining the existing bounded `exp - iat` contract；path and uncached relational reads no longer leak clock
  skew into domain callers。
- Review rejected the accumulated unit/component/helper test baseline rather than only this unit's new tests。client-web and
  design have removed Vitest/component automation and its test-only dependencies/config；core-py has removed ordinary
  manager、route、schema、adapter-helper、mock runtime and deployment-helper tests。Only admitted migration integrity，real
  integration/acceptance and mature Playwright E2E remain，outside the default repository gate unless their existing owner
  explicitly retains them。The organization-wide authority is now `.github/TESTING.md`；each governed repository only
  references that policy and records justified local suites/commands。Static enforcement and builds are the default CI
  proof；new automation requires explicit Sir approval after a manual/scripted black-box journey has matured。
- Operational self-review removed a speculative concurrency validation from both peer-local path implementations。Traversal
  now retains observed Relation rows；a candidate whose endpoint closure can no longer be assembled returns `not_found`
  instead of escalating an internal cross-statement race。Client Graph、Relation Inspector and Recall boundaries retain
  contextual diagnostics while presenting shallow completion messages rather than raw internal exceptions。
- Exact-head closure passed for core `d2cac7d` and client-web `5b8071e`。The actual Pages Preview + Preview PostgREST journey
  covered focal navigation、soft direction、Block/Relation inspectors、Solved Content and a four-Block/three-Relation
  shortest path without browser errors；the temporary Preview corpus was removed afterwards。

## Unit Review — 2026-08-18

### What is now stable

- **Product value**: graph-navigation retrieval 是从一个已定位的 Block/Relation 出发，对既有 graph facts 做 bounded、
  direction-preserving、identity-preserving 的取得；它既不等同于 Resolver 对 focal Block 的解释，也不只服务 Graph
  View。
- **MVP primitives**: Block neighborhood、Relation neighborhood、bounded shortest-by-hop path。Unrestricted N-hop、
  pattern language、community/centrality/ranking 不进入 MVP。
- **Result authority**: `GraphModel` 只承载 persisted Blocks/Relations，并保持 endpoint closure；operation-specific
  result 只补 continuation 或 ordered path evidence，不混入 label、preview、layout、scene delta 等 presentation。
- **Peer topology**: core-py/SQLModel 与 client-web/PostgREST 各自本地实现同一领域 contract；当前没有 graph-
  navigation Peer capability、HTTP inbound 或 database RPC。
- **Graph product model**: random focal + bounded one-hop 是默认 scene；canvas activation 改变 focal，Inspect 是独立
  secondary action；bounded active scene 覆盖 session cache；exploration scale 与 camera zoom 分离；direction 是 soft
  emphasis；Find path 由 application Search 组合、Graph View realize。
- **Presentation ownership**: retrieval 保持 presentation-free；Resolver registration 提供消费同一 solved-content
  authority 的 preview/full renderers；Graph/List 各自拥有加载 orchestration；InfoBase View 是 navigation host，
  Inspector/Solved Content 是 modeless route outlets。
- **Visual constraint**: Graph 必须从现有 InkCre palette、tokens、components 与 application shell 出发。被拒绝的
  full-screen spike 只保留为失败证据，不是实现参考。

### What is deliberately deferred

- general N-hop/ego graph、Cypher/SPARQL-like pattern matching、ranked/alternative paths；
- community analysis 及旧 Graph 全图 community/layout selector；
- graph-navigation Peer delegation、generic database RPC、cross-statement snapshot/retry；
- inline expand/full-content、manual node resizing、durable scene/layout/camera state；
- 将 Graph-specific node、toolbar、panel header 等伪通用组件 promotion 到 design system。

### Remaining gates

1. **Presentation preflight — complete**: [presentation-preflight.md](presentation-preflight.md) inventories the actual
   client shell and InkCre authority，closes the narrow Node/Relation/outlet state contract and identifies only two proven
   design-system pressures (`InkPopup` no-scrim and domain-neutral `InkSearchBar`)。A new broad visual spike is not a gate。
2. **Acceptance contract — complete baseline**: [acceptance.md](acceptance.md) separates public-manager parity、real producer
   graph vertical、client-web navigation-host journeys and non-snapshot visual review。
3. **Implementation plan — complete**: [implementation-plan.md](implementation-plan.md) maps the state diff into seven
   owner-separated increments，records exact module surfaces、runtime sequences、proof and failure branches。
4. **Preflight calibration — complete**: endpoint indexes、PostgREST query composition、Resolver preview migration surface、
   shared-corpus owner and Vue Flow measured-dimension/camera APIs are verified。Budgets (`8/20/50` scene scale、`4/8` hops、
   `1000/10000` explored Blocks) remain explicit provisional constants subject to real query/UX evidence，not open design。
5. **Impact Handshake**: freeze the exact mutation and verification boundary before governed source changes begin。

Preflight corrected one private query assumption without changing the public contract：a `both` neighborhood is assembled
from separately bounded incoming/outgoing Relation reads，then merged by ID-desc inside the manager。A single
`OR + ORDER BY id` query can favor the primary-key scan and filter away most rows；the split form used both proposed endpoint
indexes on a transaction-local sparse 50k topology and is directly expressible through PostgREST。The experiment rolled back
all generated rows and indexes。

## Why This Unit Exists

Feature/semantic retrieval 可以帮助定位一个可能有用的 Block 或 Relation，但当前通用 graph surface 会加载整个
info-base。缺失的是一个 bounded use capability：从已知位置取得有意义的局部 graph，并让 caller 沿 Relation
方向继续探索，而不是把全图可视化当作检索。

## Boundary With Resolver

```text
Resolver
  focal Block + hydrated content + relevant local Relations
    -> solved/use-facing interpretation
    -> may materialize an explicitly owned missing derivation

Graph navigation retrieval
  addressed Block/Relation + navigation request
    -> selected existing Blocks/Relations + navigation evidence
    -> read-only with respect to graph authority in the current hypothesis
```

- `Resolver.get_relations()` 是 Resolver 解释 focal Block 时取得 direct local facts 的内部能力；它不自动成为
  graph-navigation product contract。
- Resolver 可以把若干 adjacent Blocks/Relations 隐藏在一个 solved-content projection 内；graph navigation
  retrieval 反而必须保留 entity identity、Relation direction/content 与为什么该 entity 被返回。
- Resolver 的 `materialize_missing` 是 lazy interpretation contract；graph navigation retrieval 是否发现已有
  graph、是否触发 organization/materialization 是另一条 effect 边界，不能从 method 复用自然推出。
- Resolver label/solved content 可以服务结果呈现，但不能未经讨论成为 traversal selection authority。

## Working Product Topology

```text
feature / semantic / exact selection
              |
              v
       focal graph entity
              |
              v
 graph-navigation retrieval
              |
              v
 bounded existing graph result
              |
              +--> GraphSurface / future ListSurface
              +--> Agent or another application capability
```

这张图只固定 owner 关系与前后位置，不冻结请求字段、遍历算法或 UI。

### InfoBase Graph view pressure

client-web `InfoBase Graph view` 是本 unit 的明确应用场景。当前实现以 `Block.getAll() + Relation.getAll()` 构造
全图并在 browser 内做 community detection/layout；新的方向是让 scene 只持有由 recall、exact selection、
one-hop expansion 或 path result 得到的局部 graph。scene 如何累计、dismiss、layout 和 undo 属于 UI state，
不应被持久化为 retrieval authority。

直接打开 `overview` 时怎样取得初始 seed 不能从 one-hop contract 自然推出。D-356 修正了 owner：InfoBase View
不能拥有 lexical recall，但可以在 unresolved/404-like state 组合一个外部 recall surface 并消费其 selected Blocks。
允许的 initialization modes 是 random focal Block、bounded random Block set 与 recall-backed unresolved state；
D-357 已选择 random focal + bounded one-hop 为 default，另两种保持显式模式。明确
Block/Solved Content route 的 focal 不在 scene 时，仍可执行默认 bounded one-hop。
`overview` 只表示当前 accumulated scene 的无 focus 全貌。

### Approved Graph view UX scope

D-345 允许在本 unit 激进重做 Graph view 的视觉与交互，而不是只把全量加载替换成 query：

- node/edge 的信息层级、形状、颜色、方向、label 与 hover/active/new/focal/dimmed states；
- one-hop/path delta 进入 scene 时的 animation、camera fit 与 focus/defocus；
- dynamic graph 的增量稳定 layout，避免每次 expansion 全图跳位；
- community 从 dropdown 选择升级为 canvas 内可见、可进入、可返回 overview 的空间交互；
- Block Inspector 与 solved-content popup 的定位、尺寸、内容层级及其与 canvas focus 的配合；
- responsive/touch/keyboard/accessibility 与 reduced-motion fallback。

GraphCon deck 的可迁移原则是：community 是 canvas 上的空间对象；overview 与 focused scene 共用一张 mental
map；focus 通过 camera + contrast + reversible displacement 呈现。不能直接复制其 authored positions，因为
InKCre scene 会由 recall/expansion/path 运行时增长，community membership 也可能改变。

### Working focus-set model

Graph scene 持有已取得的 Blocks/Relations、稳定 home positions、selection 与瞬时 focus set。focus set 可以来自
focal one-hop delta、bounded path、multi-selection 或 computed community；它统一驱动 focal/context 对比、内部与
boundary Relations、可逆 peripheral displacement 以及 smooth camera fit，而不是让每种交互分别实现一套状态机。

增量 expansion 的 working sequence 是：

```text
graph delta
  -> merge into scene
  -> preserve existing home positions
  -> seed new nodes near the focal entity
  -> local settle / collision only
  -> focus focal + delta
  -> camera fit unless user navigation currently owns the camera
```

automatic camera 只响应 explicit selection、community enter、expansion、path 等明确动作；manual pan/zoom 暂停
automatic camera ownership，background changes 不偷走镜头，explicit refocus 才重新启用。reduced-motion 下用即时
position/contrast change 代替空间旅行。

### InkCre UI integration pressure

本 unit 不允许 Graph view 另造局部视觉语言。UI responsibility 的 working split 是：

- `../design` / `@inkcre/ui-web` 拥有跨产品语义可复用的 tokens、buttons、loading/empty/error states、tooltip 与
  generic overlay primitives；只有 Graph view 证明的真实通用缺口才下沉。
- client-web InfoBase Graph view 拥有 Block/Relation rendering、focus set、community hull、scene controls、camera、
  layout 与 navigation-host composition；不能因为这些元素需要统一风格就把 `InkGraphNode` 等 product-specific
  组件塞进 design system。
- `BlockInspectorPopup`、`SolvedContentPopup` 继续是 InfoBase route destination outlets；内部内容复用 UI
  primitives，GraphSurface 只 realize route，不重新接管它们的 shell。

已观察到的具体缺口：当前 Graph view 混用旧 `--ink-*` fallback、literal colors/sizes 与 `sys-var`；empty/error
states 未使用 `InkPlaceholder`；node 显示 exact Resolver ID 与 raw content slice；MiniMap/Background 直接硬编码
颜色。更重要的是，当前 `InkPopup` 无条件创建 full-screen scrim，因此 right-side Block Inspector 会阻断其背后的
navigation host。design-system preflight 需要判断最小通用修正是给 low-level popup 增加 modeless/no-scrim 能力，
还是已有 primitive 可以无损组合；不能在 Graph view 内复制一套 popup。

D-348 已固定 desktop route outlets 为 no-scrim/modeless，narrow-screen Solved Content 可以占满可用区域。新增的
Product pressure 是：Popup 不应继续充当“canvas node 固定太小，无法承载 Block 内容”的补丁。Graph nodes 应允许
content-driven、可变的尺寸；但 D-349 已拒绝 inline expand、inline full-content 与 node 内的业务 actions。node
本体始终是 preview surface，Inspector 保留 metadata/Relations/actions，Solved Content 保留 focused reading 与
未来 Mail reply 等真实业务交互。manual resize 仅是未选择的候选，不因 Vue Flow 支持而自动进入 MVP。

即便只采用 intrinsic variable sizing，incremental layout、collision 与 edge anchoring 也必须消费实际 measured
dimensions，而不是当前固定 `200 × 150`/constant collision radius 假设。当前 renderer contract 还存在直接证据：
Twitter `ContentTweet` 在完整 `SolvedContentRenderer` 内以“for graph view”为由截断内容，core `ContentText` 也固定
截断 100 字；相反 Mail `ContentEmail` 已含 materialize/download/navigation actions，未来还会增加 reply。说明
preview presentation 与完整、可交互 Solved Content 已被错误地合并。下一项 Technical question 是 Resolver 是否
应拥有独立、interaction-free 的 preview renderer contract，还是 GraphSurface 能从现有 Block-local projections
无损组合 preview；不能先假设复用完整 renderer。

D-350 已关闭这个问题：Resolver registration 拥有 `previewRenderer` 与 `solvedContentRenderer` 两个 presentation
contracts，但二者消费同一个 solved-content authority，不新增 `previewContent` projection。Graph node intrinsic
dimensions 来源于 preview DOM measurement，不由 Resolver 输出 canvas layout hints；preview loading 保持 lazy、
bounded 且 `materializeMissing=false`。该 preview contract 属于 InfoBase presentation，可由 future List view 复用，
不是 design-system 或 Graph-only abstraction。

D-351 进一步固定 retrieval result 为 presentation-free：只返回 persisted Blocks/Relations 与 operation-specific
navigation evidence。label、preview、solved content、node dimensions、focus/layout 以及相对 caller scene 的 delta
均由 InfoBase View 在 merge 后产生；Peer provider 不理解这些字段。

## External Research Synthesis

### Graph-theory problem families

- **Adjacency / one-hop**：取得 incident edges 与 neighboring vertices；D-344 已确认。
- **Traversal / reachability**：从一个或多个 anchors 以 BFS/DFS、方向和 depth bound 取得可达部分。
- **Path**：在已知 source/target 之间判断 reachability、返回一条/多条 shortest/simple path。
- **Pattern matching**：声明固定、quantified 或 non-linear graph shape，返回所有 bindings/paths。
- **Analysis**：degree、centrality、community、similarity 等；它们解释 graph 的全局/统计性质，不自动属于
  navigation retrieval。

### Primary product/query evidence

- [Neo4j Bloom scene](https://neo4j.com/docs/bloom-user-guide/current/bloom-visual-tour/bloom-overview/) 只包含用户经
  search/exploration 找到的 graph 部分，而不是默认加载整个 database。
- [Neo4j/Aura scene interactions](https://neo4j.com/docs/aura/explore/explore-visual-tour/scene-interactions/)
  把 immediate-neighbor expansion、按 relationship type/direction/target type 的 selective expansion、result limit、
  selected-node relationship reveal 与 path exploration 分成不同交互。
- [Cypher graph patterns](https://neo4j.com/docs/cypher-manual/current/patterns/) 区分 fixed/variable/non-linear
  patterns、shortest paths 与 path uniqueness；pattern 是查询 specification，path 是实际匹配结果。
- [Cypher variable-length path guidance](https://neo4j.com/docs/cypher-manual/current/patterns/variable-length-paths/)
  明确指出宽泛或上界过大的 quantified traversal 会产生巨大 path cardinality，应以有限上界、relationship/node
  predicates 与方向在遍历过程中 prune。
- [SPARQL property paths](https://www.w3.org/TR/sparql11-property-paths/) 将 sequence、inverse、alternative 与
  repetition 组合为 predicate-path expression，也指出 unanchored path 会搜索全图并产生大量结果。
- [NetworkX traversal reference](https://networkx.org/documentation/stable/reference/algorithms/traversal.html) 将
  bounded BFS/DFS、distance layers 与 edge traversal 作为不同图论 primitives；这些算法存在不代表都应成为
  InKCre MVP 产品能力。

### Current working judgment

1. D-344 one-hop expansion 是 Graph view 与 Agent 都需要的 atomic primitive。
2. unrestricted N-hop/ego graph 只是把 fan-out 风险藏进 `depth`，不应成为第二项 MVP primitive。
3. “连接两个已知 Blocks”有独立用户意图，并天然要求返回 path evidence；bounded shortest-by-hop path 是可解释
   的最低机制，但 hub shortcut 与 filter semantics 仍需讨论。
4. fixed/quantified graph pattern matching 很强，但会迅速要求 node predicate、Relation content grammar、variable
   binding、path uniqueness 和 result cardinality contract；当前直接实现等同于发明一个小型 Cypher/SPARQL。
5. centrality/community/recommendation 属于 graph analysis 或 future composite use，不因 Graph view 当前已有
   community detection 就自动进入 graph-navigation retrieval。

## Discussion Queue

Product/Technical discussion is no longer driven by an open-ended list。The next sequence is:

1. actual-client presentation inventory and narrow visual-state contract；
2. black-box Acceptance contract and authoritative corpus；
3. cross-repo implementation-plan probe with topology/sequence/branch simulation；
4. evidence preflight and calibration；
5. return to Product/Technical review only for a concrete contradiction，then freeze the Execution baseline。

This sequence should batch naturally connected findings；it must not manufacture one-at-a-time decisions when the accepted
contract already determines the answer。

## Evidence Already Established

- `RelationManager.get()` 只按一个 Block、direct in/out 与 exact content 查询；它没有 depth、path、result bound
  或 graph-shaped result contract。
- `Resolver.get_relations()` 缓存并消费相同 direct relations，owner 是 focal Block interpretation。
- `RelationManager.get_text()` 用两端 Block-local labels 投影一个 directed dynamic property；它证明 Relation
  本身具有可应用语义，但不是 traversal/query implementation。
- client-web GraphSurface 当前加载全量 Blocks/Relations；这是 visualization baseline 与 scaling/use pressure，
  不是 graph-navigation retrieval 的现成实现。
- `BlockManager.iterate_from_block()` 不是可保留的 traversal baseline：它只跟随 outgoing Relations、以一个全局
  mutable `depth` 穿过递归分支、没有 visited/cycle guard、没有 per-hop/result bound 或 deterministic ordering，
  并只返回 ID sets。它应作为失败证据 hard-cut，而不是包装成新的 manager。
- producer `GraphForm` 是 flat graph write command，负 ID 表达同批新实体 references；它不应被复用于 read
  result。Graph-navigation response 必须返回 persisted `BlockModel`/`RelationModel` authority，并另外表达 operation-
  specific evidence（例如 ordered path 或 continuation）。
- semantic retrieval 已建立 domain manager local/delegated split、exact capability、fixed inbound 和 validated
  Block/Relation DTO 的实现模式；graph navigation 可以复用该 Peer topology，但不能复用 vector-ranking payload。

### Working one-hop contract

- Block expansion returns the focal Block、a bounded deterministic page of incident Relations and every opposite endpoint
  Block；Relation expansion returns the addressed Relation and both endpoint Blocks。Every returned Relation therefore has
  both endpoints in the returned graph result。
- Block expansion uses explicit `in` / `out` / `both` direction，default `both`，default limit 20 / hard maximum 100，and
  stable Relation-ID-desc ordering with an exclusive nullable `next_cursor`。ID is ordering/continuation identity，not a
  claim of semantic recency。A page fetches `limit + 1` to distinguish complete from truncated results。
- Result does not need `frontier` or `new/existing` flags：all returned entities are addressable next steps，while caller
  scene identity merge determines which are new。
- Missing addressed entity is a meaningful not-found failure；an existing isolated Block succeeds with the focal Block and
  no Relations。Concurrent mutation remains best-effort，but one response must be endpoint-closed。
- An optional exact set of Relation `content` values has low implementation cost and supports selective expansion without
  inventing prefix/regex/JSONPath semantics over arbitrary string/JSON content。D-352 accepted this exact-content-only
  filter and the rest of the proposed contract。

### Working bounded-path contract

- `find_path(from Block, to Block)` returns at most one shortest-by-hop path under explicit bounds；it does not rank
  semantic relevance、return all equal paths or hide a general pattern query。Default traversal direction is `both` while
  retaining each Relation's persisted direction in evidence；caller may restrict to `out` or `in` and reuse exact content
  filtering。
- Working bounds are default `max_hops=4` / hard maximum 8 plus an explored-graph budget，tentatively default 1,000 Blocks /
  hard maximum 10,000。Hop bound alone cannot protect against one high-degree hub。Exact numbers remain preflight-tunable，
  but both dimensions are part of the public boundedness model。
- Result status is `found`、`not_found` within the requested bounds or `limit_reached` before exhaustive bounded search。
  Budget exhaustion is not silently reported as no path。Only a found result returns the final path graph；search working
  sets do not leak into InfoBase View。A source equal to target succeeds with one Block and zero Relations。
- Ordered evidence is a Block-ID sequence plus Relation-ID sequence with `len(blocks) = len(relations) + 1`，backed by an
  endpoint-closed persisted graph result。Actual Relation rows reveal whether a traversal step followed or opposed the
  stored direction；no duplicate orientation flag is needed。
- Do not special-case Source/Mailbox or penalize high-degree nodes in MVP。That would be a graph-ranking policy rather than
  path retrieval。Direction、exact content filters and search bounds are the honest controls；future ranked/alternative path
  capabilities can compose later。
- Technical hypothesis：application-owned bounded bidirectional BFS issues batched frontier queries through
  RelationManager/graph query helpers。Do not put traversal business logic into a PostgreSQL RPC or retain the broken
  `BlockManager.iterate_from_block()` recursion。Required `relations.from_` / `relations.to_` indexes belong to the migration
  preflight。

### Working manager / peer topology

```text
client-web InfoBase View
  -> @inkcre/core GraphNavigationRetrievalManager
  -> PostgREST Block/Relation fact queries
  -> local bounded traversal

core-py domain consumer
  -> core-py GraphNavigationRetrievalManager
  -> SQLModel Block/Relation fact queries
  -> local bounded traversal
```

- Previous working hypothesis mechanically copied semantic retrieval's Peer delegation。Repository evidence disproves that
  need：`@inkcre/core` already owns direct PostgREST Block/Relation access，and graph navigation requires no provider-local
  model、secret connection、background worker or other asymmetric capability。Forcing client-web through core-py would add
  network and availability dependencies without changing graph authority。
- Working correction：implement the same domain manager contract locally in TypeScript/PostgREST and Python/SQLModel。
  Do not add an exact Peer capability or HTTP inbound in MVP unless another actual consumer cannot access database authority。
  A future remote adapter may be added without changing the manager's domain methods。D-355 accepted this topology and
  requires parity proof over one shared behavioral corpus。
- Working common read shape is `GraphModel { blocks: BlockModel[], relations: RelationModel[] }`，the read-side counterpart
  to producer `GraphForm`。It enforces unique persisted IDs and endpoint closure；it is not a database row or a claim that the
  subset is the whole info-base graph。D-354 accepted this shape。
- Operation results wrap that graph with only their evidence：Block expansion has nullable `next_cursor`；Relation expansion
  needs no continuation；found path adds ordered Block/Relation IDs，while non-found/limit outcomes retain only addressed
  endpoint facts。
- Python request schema uses `from_` only as keyword-safe implementation spelling and serializes/accepts wire key `from`；
  TypeScript and product contracts use `from` / `to` directly。

### Working initial-scene modes

```text
open Graph overview
  -> mode: random focal -> one Block + bounded one-hop
  -> mode: random set   -> bounded Blocks as seed focus set
  -> mode: unresolved   -> compose external recall surface -> selected Blocks as seeds

open /graph/blocks/{id} or solved-content route
  -> if focal Block absent, bounded one-hop seed
  -> realize modeless route outlet over that scene
```

- Do not auto-load recent Blocks or all graph authority merely to avoid an empty canvas；recency is an arbitrary selection
  policy and does not make a graph overview。Random selection is explicit seed policy，not a relevance claim。
- Recall query/results remain owned by an application/recall component similar to Home。Graph View only consumes selected
  Block authority；using the component does not expand the View definition。Clear/remove remain scene-local controls；they
  do not delete graph authority。
- Existing InfoBase List results should gain an application-owned “explore in Graph” destination that opens the Graph Block
  route。Do not expand `InfoBaseRouter` into a surface registry merely to express this client-specific navigation。
- Recall/random seeds can be temporarily disconnected；Relations become visible when returned by expansion/path。Do not add an
  induced-subgraph primitive solely to decorate the initial search result。

### Working application Recall composition

```text
App-level Recall launcher (Ctrl/Meta+K)
  -> application Recall/Search composition
  -> lexical query/result
  -> active InfoBase View present/consume
  -> otherwise List View fallback

application Recall/Search
  -> composes generic ../design InkSearchBar
  -> owns InKCre query/routing behavior outside the design primitive
```

- D-358 fixes global launcher、default-List/current-View routing and application component reuse。GraphSurface does not own
  recall merely because it can consume selected Blocks in fallback/seed modes。
- `InkSearchBar` is a genuine promotion：domain-neutral accessible search input/submission/clear/loading presentation。
  It does not register global shortcuts、call retrieval or select an InfoBase View。Home's current raw search input must move
  to this visual contract rather than preserving a second local language。
- D-359 fixes URL `?q=` as the handoff authority。List replaces ranked results；Graph merges/focuses Block seeds；routes that
  host an InfoBase View opt in through application metadata。Do not add a synchronized global recall-result store or teach
  InfoBaseRouter lexical semantics。

### Relation route / Inspector

D-360 makes Relation an addressable InfoBase route。Graph edge selection and direct Relation routes realize a modeless
`RelationInspectorPopup` over an endpoint-closed scene；List can consume the same route later。Relation Inspector presents
from/content/to plus identity/timestamp and endpoint navigation，but Relation does not gain Resolver or Solved Content。
Block/Relation Inspectors remain explicit components rather than a speculative EntityInspector abstraction。

### Working Graph interaction language

This remains a review hypothesis，not a confirmed decision：

- Node preview content remains interaction-free。The node shell owns drag、selection and focus；hover changes visual emphasis
  only and never moves the camera。
- Selecting a Block may open the modeless `BlockInspectorPopup`，but D-361 keeps that Inspector entity-local。Changing focal
  entity invokes bounded one-hop exploration from the canvas itself rather than placing expansion actions in Inspectors or
  buttons in draggable nodes。
- The focal-scale hypothesis uses a small number of discrete scene budgets：each scale caps visible incident Relations and
  endpoint Blocks，while the camera frames the focal entity and currently admitted direct context。The exploration scale
  must remain distinct from free camera zoom so ordinary pan/pinch/scroll does not silently issue retrieval requests。
- D-362 fixes bounded active-scene replacement over a reusable session cache。Shared entities keep their measured positions；
  unrelated visited entities leave visibility instead of accumulating indefinitely。Returning to cached focal context may
  reuse retrieval and layout state without turning the cache into a second visible graph authority。
- D-363 separates activation from inspection。Single activation changes focal；a canvas-level `Inspect` action opens the
  entity-local Inspector，with double activation and `Enter` as shortcuts。Inspector close uses router `back()` without
  rolling back the already-established Graph scene。
- D-365 fixes one Graph View-level exploration scale with discrete Relation budgets。Compact/standard/broad begin visual
  calibration around `8/20/50` Relations；standard is the default，endpoint closure supplies Blocks，and exact numbers remain
  preflight-tunable rather than becoming durable retrieval-contract constants。
- D-364 removes path discovery from focal-canvas interaction。Application-owned Search may compose the bounded path
  primitive as its own operation；Graph may later realize a path result but does not call lexical Recall to manufacture a
  second endpoint。`not_found` and `limit_reached` remain retrieval outcomes without implicit retry or query broadening。
  Relation-content filtering remains an exact retrieval contract，but the UI does not need to expose a raw-string control
  merely because the API supports it。
- A client-web scene composable owns loaded entity maps、selection、focus、expansion continuations、layout measurements and
  camera intent。It is presentation/runtime state，not an `@inkcre/core` retrieval manager or a new domain manager。

### Layout / visual preflight evidence

- The current Graph view loads `Block.getAll()` and `Relation.getAll()`，runs Louvain community detection，then coordinates
  separate all-community MDS and topology-selected force/dagre/circular/radial/grid layouts。It repeatedly calls delayed
  `fitView()` after load、community selection、layout selection and force stabilization。
- The accepted focal one-hop scene has a much stronger topology：every admitted Relation is incident to the focal Block，so
  its visible graph is a star/multistar。Community detection and a user-facing generic layout selector do not improve that
  scene and should not remain as accidental product concepts merely because the old all-database canvas needed them。
- Existing radial layout ignores measured node dimensions；existing force collision uses one fixed radius；both conflict with
  intrinsic resolver previews。Layout must wait for Vue Flow/DOM measurements and admit variable node bounds rather than
  treating every Block as the same circle。
- Existing Relation Bezier edges share endpoint geometry，so parallel Relations can overlap labels and hit targets。The new
  edge presentation needs deterministic sibling lanes plus separate hover/active emphasis。
- Working direction：hard-cut the current focal-mode community/layout machinery，use a deterministic focal radial layout with
  one or more rings chosen by admitted density and measured node bounds，and animate only semantic scene changes。Manual drag
  overrides layout within the current session scene key instead of becoming durable Block authority。
- D-366 confirms that direction。Manual positions are cached per focal scene/exploration scale for the current Graph session，
  not persisted globally；parallel Relations receive sibling lanes，and reduced-motion users receive non-animated state
  transitions。

#### Rejected visual spike — do not use as implementation baseline

The first static full-screen spike was rejected by Sir and must not be referenced as the desired visual direction。It did
demonstrate structural focal/context、intrinsic node、Relation emphasis and modeless-outlet ideas，but failed the visual-system
contract for more fundamental reasons：

- it invented a cold developer-tool palette instead of beginning with InkCre's existing color palette、tokens and public
  components，violating the established design authority；
- it misread “restrained、cool、professional、sharp” as permission to replace the visual language，rather than criteria for
  refining the existing language；
- it exposed implementation/debug vocabulary (`focal_block`、direction status、modeless explanation) and redundant eyebrow/
  status copy that users did not need，making the interface explain its architecture instead of serving the interaction；
- it widened the experiment into invented app chrome、toolbar and copy，so state validation became a noisy redesign。

Corrective preflight must first inventory representative current client surfaces and the design repo's actual palette、type、
spacing、radius、icon and component grammar。A later study must be narrow—Node/Relation/focal/context/outlet states inside the
existing shell—with no explanatory/debug copy and no new token unless an observed generic gap earns it。

### Route-state conflict discovered by preflight

The current concrete `/info-base/graph/blocks/:block` route is read as the Graph focal Block and simultaneously mapped to
`InfoBaseRoute {name: "block"}`，which immediately mounts `BlockInspectorPopup`。After D-363，scene focal navigation and an
Inspector outlet are distinct states and cannot continue sharing one route authority。The route topology must preserve
surface-owned focal history while letting `InfoBaseRouter` realize an optional entity-local outlet over that scene。

D-367 resolves the conflict：Graph focal uses one role-named query reference (`focal_block` or `focal_relation`) on a stable Graph page path，while
concrete Block/Relation/Solved Content outlet paths preserve that query。Only focal identity is reconstructive URL authority；
scale、layout、camera、cursor and cache remain runtime scene projections。

### Resolver-preview loading pressure

- Current client Resolver exposes lazy cached `getSolvedContent()` and a presentation-neutral `solvedContentRenderer`，but no
  preview renderer yet。Current Graph bypasses this contract and truncates `Block.content` directly。
- A scale-bounded one-hop `GraphModel` is structural evidence，not a declaration that every focal or neighbor Relation has
  been loaded。Passing its Relation subset into Resolver as a complete relation cache would corrupt solved-content behavior。
  Graph preview Resolver instances must retain their own complete-context loading semantics。
- Working loading model：render structural Node shells immediately；resolve the focal first，then proactively resolve all
  admitted neighbors through a small concurrency pool and shared Resolver cache。Cancel queued work when a scene leaves，but
  do not add hidden retries or treat preview failure as graph-navigation failure。
- Resolver preview completion changes intrinsic dimensions。Batch `ResizeObserver` measurements per animation frame and
  recompute the deterministic scene layout；do not issue a camera fit for every Node completion。The shell has bounded min/max
  dimensions so progressive content does not make the canvas unbounded。
- D-368 confirms this Graph-specific orchestration without turning it into a shared List/Graph wrapper。Only the Resolver
  renderer/solved-content contract is shared。Graph retrieval itself is described as returning bounded structural evidence；
  navigability and loading speed remain consumer objectives rather than retrieval ownership claims。
- D-369 makes Graph direction a soft visual emphasis over the same scale-bounded `both` scene。Inactive-direction Relations
  and their otherwise-unemphasized endpoints remain clickable but dimmed；changing emphasis does not retrieve、relayout、fit
  camera or fork cache identity。Hard `in/out/both` remains available to other one-hop API consumers。
- D-370 keeps focal and context Node sizes intrinsic。Focus is established primarily through restrained hairline/optional
  halo、crisper incident Relations and reduced context contrast；elevation and z-index are not accumulated as ceremonial
  state signals。The target visual character is restrained、cool、professional and sharp，with exact tokens left to visual
  prototyping instead of frozen in prose。
- D-371 names role-specific `get_block_neighborhood` / `get_relation_neighborhood` manager methods and keeps UI `expand`
  outside the retrieval vocabulary。The public split exposes two coherent semantic operations while hiding endpoint closure、
  pagination and query mechanics；deep-interface quality is clarity and low caller knowledge，not minimal method count。
- D-372 fixes `find_path` as a discriminated `PathFound | PathNotFound | PathLimitReached` union。Only success carries final
  GraphModel and ordered Block/Relation paths；negative outcomes expose no working graph and cannot form nullable-field
  contradictions。
- D-373 keeps random-focal policy in Graph initialization and adds a singular random-row primitive to existing peer-native
  Block access (`BlockManager.get_random` / `Block.getRandom`)。Both use count + stable-order random offset；no all-Block
  browser transfer、Graph-retrieval method or database RPC is introduced。
- D-374 removes a public tie-break among equal shortest paths。Stable ID iteration may remain an implementation detail；
  Acceptance asserts exact paths only for unique-shortest graphs and otherwise validates semantic path properties，preventing
  UI or fixture convenience from promoting database identity into path-ranking authority。
- D-375 puts `Find path` in application-owned Search。Search selects exact/lexically suggested endpoint Blocks and hands off
  `path_from` + `path_to` as reconstructive Graph query state；Graph realizes the path outcome but owns neither the operation
  nor endpoint picking。Focal、path and `q` seed address forms remain mutually exclusive。
- D-376 fixes best-effort concurrent-read semantics：successful GraphModels stay endpoint-closed without a cross-statement
  snapshot claim。Neighborhood omits now-unresolvable Relations；path assembly reuses traversal-observed Relations and maps
  an endpoint-closure race to ordinary `not_found`，with no hidden retry or caller-visible internal inconsistency。

D-353 accepted this contract and corrected public endpoint names to `from` / `to`，matching Relation direction and avoiding
ambiguity with the upstream `Source` domain。Python-only syntax may use `from_`/aliases without changing the public term。

## Confirmed Decision References

- D-073/D-074：Resolver application-facing interpretation、controlled lazy materialization 与 effect vocabulary。
- D-075/D-196：exact Resolver、`get_text`/`get_label` 与 Block-local label boundary。
- D-078：semantic retrieval 返回持久 Blocks/Relations，不引入 transient chunks。
- D-094：Relation 作为 directed dynamic property 的 semantic projection。
- D-343：本 unit 选择以及与 Resolver interpretation 的明确区分。
- D-344：one addressed graph entity / one-hop atomic navigation primitive。
- D-345：bounded Block connection 与 aggressive Graph-view UI/UX scope。
