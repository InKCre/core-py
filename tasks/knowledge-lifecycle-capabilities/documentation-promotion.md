# Durable Documentation Promotion Plan

## Control

- **Mode**: Memos/RSS/semantic-retrieval shared promotion published。Hub `95c4023` contains the shared batch；core-py
  `cc8f90a` and client-web `8324293` consume that exact published head through pure shared-ref commits。Final verification
  found client-web remote main already at `8324293` through an external/automatic push not issued by this workflow；
  core-py implementation/docs/ref commits remain local until separately authorized for push。
- **Apply gate**: unresolved discussion pressure remains here；stable design + verified implementation triggers
  durable projection during unit completion。Commit、push、Hub publication、shared-ref bump 与 production mutation
  remain separately authorized operations。
- **Owner rule**: Hub source、Spoke shared-ref、core-py Unit TDD 与 client-web docs 分属不同
  owner/operation，不混入一个 commit，也不在 `docs/_shared/**` 直接编辑。

## Promotion Test

候选内容必须同时满足：

1. 已从讨论假设升级为获批、稳定且可复用的产品或技术合同；
2. 有一手产品事实、当前实现证据或 acceptance fixture 支撑；
3. 唯一 owner 已确定，不复制同一事实；
4. 不把某个 Spoke 的偶然类名或临时 workaround 升级为共享合同；
5. 与已有 durable claim 冲突时明确写出 `From → To`，不静默叠加。

## Known Corrections to Existing Hub Truth

以下纠错已在 Hub source worktree 中按 owner 应用；本表保留 From → To 的 promotion provenance：

| Existing pressure | Intended correction |
| --- | --- |
| collection 被描述为产生 blocks/relations，同时 organization 又像是把 collected information 转成 blocks/relations | collection 为了持久化 source information 可以拆成 graph；organization 打理**已经存在**的 info-base，以改善 use |
| collection / organization / use 容易被读成信息状态或固定 lifecycle | 三者是对信息执行的能力动作，不新增未经需求证明的 lifecycle |
| breakdown/merge/linking 容易被当成 organization 的完备枚举 | 它们只是已知能力，目标始终是为 use 优化 info-base |
| indexing 容易被归入 organization | indexing 只作为 application/retrieval 支撑 |
| source-native objects 可能被误解成 graph 之外的持久模型 | Tweet/GithubRepo/FeedItem 等通过 blocks/relations 持久化；不建立通用 collected god object |
| resolver 的 `v1` / `v2` 轴被叫作 `generation` | 按开发者惯例叫 `resolver contract version`；这是一致性/自解释修正，不是声称 `generation` 在其他上下文均错误 |
| graph 中的 source/protocol object 被叫作 `wrapper` | 它是普通 block；在拥有与关联 semantic content 有关的 protocol/source-authored facts 时按职责叫 `metadata block`，不新增 wrapper type |

## Candidate Hub PRD Batch

### Program-level product truth projected to Hub source

- collection、organization、use 的动作边界，以及 indexing 的归属。
- memo-like 是独立、多端、低摩擦的 collection surface，用于记录想法、周围事物与零碎
  信息，不承担 info-base 的查阅/use。
- 长期产品方向允许 memo extension 分别支持 backend 与 collector，但两者是独立产品关系、
  独立 deliverable，不共享一个含混的“同步”合同。
- Memos 是首个 memo → graph reference product。
- 当前 InKCre 不建立 terminal-user、tenant 或 per-user ownership/ACL；deployment 是单一
  user/owner context，多 runtime `client` 是 peers 而不是人类用户。external account/user 只在
  source/protocol 边界拥有其原生语义。
- Extension APIs default to core peer authentication, but an extension may explicitly own its protocol
  route-auth composition；Memos uses an auth-neutral root with separately classified public and
  protocol-protected child routers。This does not create a core User and does not require a Memos
  administration API。Promoted technical documentation must retain a minimal code-shaped example of
  this topology instead of reducing it to prose-only “self-auth mode”。
- Memos credential is deployment-scoped and long-lived by default until explicit replacement/revocation；
  it is ordinary raw extension config with validated merge/persist/live-apply ordering；no refresh-token、
  session or Memos-specific secret lifecycle is introduced。
- Extension enable/disable normally changes route availability in the running single-process deployment；
  restart is not the ordinary activation boundary。

### Memos extension and backend MVP truth projected to Hub source

- implementable ownership unit 是 Memos extension；CanonicalMemo、graph mapping、resolver 与
  product/generation adapters 由该 extension 拥有。Memos-compatible backend 只是首个 MVP
  delivery scope。
- 当前 MVP 是 Memos 0.29.1-compatible backend，MoeMemos Android 2.0.4 是 compatibility
  acceptance client 而非 API authority。
- backend 只实现目标 journey 所需的最小 write/read surface，不复刻完整 Memos server。
- 客户端显示 write 成功代表 primary memo mutation 已持久化；D-041 不保证 graph completeness，
  failure 可留下 orphan/stale components。先行成功上传的 unattached attachment 是独立资源。
- comment 是独立 memo，并以 parent relation 连接；comments 需要独立 fixture，即使当前 APK
  core sync 不调用它。
- flomo backend、collectors、Memos 0.30/older generations、social/share/explore 默认不属于该
  unit。
- Memos current-user/settings 是 deployment-scoped compatibility projection，不新增 User/tenant
  tables，也不把 `ClientModel` 当人类用户。

### Product truth still blocked

- 当前 backend MVP 没有剩余 Product blocker；其余未决项属于 Technical/Acceptance gates。
- 其他 collection units 的用户可见 partial success、delay、delete 与 compatibility semantics。
- feature retrieval 与 graph-navigation retrieval 的完整可观察行为与质量门槛。Semantic retrieval MVP 已形成
  稳定合同、real-provider 实现证据和 Hub source projection，不再与另外两类 retrieval 捆绑。

### Semantic retrieval batch projected to Hub source

- semantic retrieval 返回按相似度排序的现有 Blocks/Relations 与 score metadata，不生成 answer、transient chunk
  或 Chat/RAG product behavior；
- organization 保持为改善 use 的 graph mutation；本 MVP 的 explicit rumination 围绕一个 focal Block 反刍，
  可以 additive no-op/增图，但不替代或删除原 Block；
- embedding records 是 profile-scoped、可重建的 use support，information authority 仍是 graph；candidate maintenance
  与 retrieval 分离，stale records 在显式 maintenance 前不可用；
- exact capability discovery 与 invocation 分离；Peer advertisement 只陈述 capability/inbound/lease，业务 facade
  通过 PeerManager 做 opaque delegation，provider inbound 必须进入 non-delegating local path；
- generic capability invoke endpoint、delegation job、readiness advertisement、persistent Agent Thread/checkpoint、ANN/
  HNSW、pagination 和 transient segment layer 均不属于本 MVP；
- Acceptance authority 是经过真实 Memos/RSS/Atom/HTML/storage/rumination 边界形成的 pinned corpus graph；可读 alias
  只属于测试 harness，不进入 production model/API。Deterministic vectors 证明 control flow，不替代 credentialed
  provider semantic-quality authority。

## Candidate Hub Product TDD Batch

### Cross-unit contracts projected to Hub source

- block 是基本持久信息单元；block hydration 隐藏 inline/pointer 分支，resolver 联合 hydrated content 与
  local relations 得到 solved/use-facing interpretation，storage 只负责按 pointer 取得 actual content。
- source-specific input 通过 extension mapping 持久化为 block/relation graph；`SubGraphForm`
  是 write form，不是完整信息模型。
- memo root content 直接保存 memo-family `CanonicalMemo`；attachments、parent、references 只由
  graph components/relations 表达，backend read 只消费 resolver solved result。
- attachment relation 默认无序；正文内显式 attachment reference 是位置 authority。Memos 0.29.1
  是已证明的 source-defined order exception，应在现有 relation payload 中保留，不推动通用
  relation schema 变化。
- comment 复用 memo root mapping，并通过 parent relation 连接。
- product API version 与 CanonicalMemo resolver contract version 是正交版本轴；CanonicalMemo decoder
  由 versioned resolver identity 选择，不在 payload/BlockModel 重复 schema version。
- info-base local memo identity 是 `block.id`；不建立 generic `resource`、`source_key` 或 source
  binding table。
- future collector 采用 best-effort exact reconciliation；匹配不足宁可产生可整理 duplicate，
  不得 content/time fuzzy overwrite。
- 复杂度投入应由边际效益而不是理论完备驱动：先识别仍未解决的问题造成的实际损失，再选择能以最低
  dependency/obscurity 成本消除主要损失的机制，并在新增机制的边际收益不再覆盖其维护与错误成本时停止。
  D-056 是 reference pressure：content fingerprint 试图制造更强 identity，却带来 normalization/stability
  成本；独立 source-time watermark 以更弱、显式的保证取得足够的 duplicate reduction。具体 heuristic
  仍不得被描述为 identity、reconciliation 或 correctness proof。
- Cache/effect controls use stable，orthogonal vocabulary across peers：`refresh` bypasses and replaces an existing
  local snapshot from current authority；`materialize_missing` permits creation only when a required derivation is
  absent；`recompute` is an explicit organization command that regenerates an existing derivation；`invalidate`
  discards a cache without reading a replacement。`refresh` itself neither grants AI/graph mutation nor requests
  recomputation。Python uses snake_case and TypeScript uses camelCase。
- New InKCre-owned APIs do not use `force` or `reload` as aliases for `refresh`。Protocol-owned names remain exact，
  including a third-party `force` query parameter。Legacy source-job `full` is not a stable cross-source contract and
  must not be promoted before its mixed scan/reconciliation/order/pagination effects are separated。
- Direct relation selection uses `include_in` / `include_out`（TypeScript `includeIn` / `includeOut`）relative to the
  subject block：incoming has the subject as `to_`，outgoing has it as `from_`；neither option implies recursive graph
  traversal。
- D-039 已关闭 deployment-scoped Memos PAT：ordinary raw extension-config lifecycle、generic validated
  update ordering、exact public profile/v0-status-404 与 immediate replace/revoke。
- D-041/D-042/D-043/D-044 已关闭 partial-graph boundary、CanonicalMemo v1、PostgreSQL binary storage
  与 Memos relation grammar；D-045 要求单独修复 client-web config path；D-046/D-047/D-048 关闭
  owned cleanup、exact fixtures 与 family/product/access-mode extensibility seams。

### Implementation evidence used for promotion

- installed extension decoder retention、unknown resolver explicit failure、core-py route/config runtime
  与 client-web config path 已由 implementation/tests 证明。
- D-047 exact fixtures、D-046 deletion behavior、PostgreSQL binary storage、partial cleanup residue 与
  official MoeMemos APK journey 均有 executable evidence。
- existing `/{extension_id}` route 已由 MoeMemos pathful base URL 复用；route-auth composition、hot
  lifecycle、caller-session graph commands 与 writable storage 已实现。证据仍不支持 top-level mount、
  generic resource binding 或通用 extension/resolver registry redesign。

### Deferred technical scope

- collector scan/webhook/export、cursor、external identity 与 reconciliation。
- flomo/其他 memo product adapters 及其 fidelity contract。
- feature/semantic/graph navigation、index/projection invalidation 与 retrieval UI。

## Spoke Unit TDD Promotion Applied

core-py local Unit TDD promotion 已应用，只记录本仓内部 implementation architecture，例如：

- memo extension package、route/service/resolver/storage/transaction boundaries；
- graph mutation 与 solved result 的 internal contracts；
- auth/config 的 local wiring；
- Memos extension 的 0.29.1 backend adapter 对 missing `updateMask` 的 raw-JSON key-presence
  inference 与 negative
  cases；
- tests、migrations 与 failure/residue handling 的实现真相。

具体 ownership 已投影到 `docs/30-unit-tdd/memos-extension.md` 与更新后的
`business-pipeline-and-authority.md`；临时 implementation observation 未被提升为共享合同。

## Architecture Understanding Log

这些发现保留为 provenance；已通过 Promotion Test 的内容现在由对应 durable owner 陈述，不以本 log 作为
并行 authority。U-009 仍只属于 task/workflow evidence：

- **U-001 — Joint graph semantics**: block/relation/resolver/storage 共同决定信息如何保存与解释。
- **U-002 — Attachment position**: association 默认无序；显式 inline reference 才拥有位置。
- **U-003 — Ordered slots are not linked lists**: `root --slot--> component` 是 slot mapping；
  当前 relation fetchsert identity 也不直接支持只换 `to_` 的 slot semantics。
- **U-004 — Text storage can carry a grammar**: JSON/text 并非天然无结构，但也不会自动获得
  canonical identity、typed query 或统一解释；resolver 不是 relation content 的唯一消费者。
- **U-005 — No historical support is not no version architecture**: 当前 target 已固定 0.29.1；
  future breaking generation 仍需要显式 adapter/generation boundary。
- **U-006 — Family canonical is not a god object**: CanonicalMemo 属于 memo extension，且就在
  graph root content 内；它不与 info-base 竞争 authority。
- **U-007 — Upstream needs evolve core contracts**: 具体 source/use pressure 可以传导到
  info-base、collection、organization、application 与 extension，但必须保留证据链。
- **U-008 — Persistence time and authored time differ**: block row time、memo-authored/source time、
  collection observation time 不得互相替代。
- **U-009 — A plan can be a design probe before it is executable**: 代码地址、依赖和可验收纵切可以
  在 Technical/Acceptance 阶段暴露遗漏合同；只有上游获批且分叉关闭后，才冻结为 execution
  baseline。
- **U-010 — Client base URL participates in route compatibility**: protocol annotations 的 relative
  path 必须与 client 对 configurable host path 的保留/拼接一起判断；不能只看到 `api/v1` 就推断
  server-root mount。MoeMemos 可用 `/memos/` base URL 复用当前 extension namespace。
- **U-011 — Complexity follows marginal utility**: 不以理论上还能更完整为继续设计的充分理由；比较
  unresolved harm、机制覆盖率、dependency/obscurity 与长期维护成本。选择足够有效的低成本机制后停止，
  同时把剩余风险与弱保证写清楚。D-056 的 time watermark 是实例，不是这条方法本身。
- **U-012 — Storage representation is not information kind**: storage 可以把 audio、video、image 或其他
  information 的 actual content 都保存为 bytes；这不使它们成为 `binary block`。block/resolver 按信息语义
  命名和解释，storage 只按 pointer 保存/取得 actual content。RSS enclosure 与 Memos attachment 已形成两个
  当前 reference pressures；PDF/EPUB/ZIP 使用 concrete generations，unknown/unsupported 使用带 MIME 的
  file fallback。
- **U-013 — Metadata block can describe related content**: 当 protocol/source object 拥有可独立使用的
  identity、metadata、role 或 lifecycle 时，使用 `metadata block → semantic content block → storage-backed content`
  分离 provenance、信息语义与物理保存；resolver 联合 graph 投影 native/use-facing value。这两者都是普通
  block 的职责命名，不新增 wrapper 类型；没有独立意义的 input 不机械增加 metadata block。RSS
  enclosure 与 Memos attachment 是当前 reference pressures。
- **U-014 — One block read contract hides conditional persistence**: `block.content` 在 inline block 上是
  actual content，在 storage-backed block 上是 opaque pointer；通用 consumer 通过
  `get_hydrated_content()` 取得 actual content，不自行解释 storage。hydration 可缓存在 ORM 非映射的
  private state，但绝不能覆盖 mapped pointer。该 read contract 取代含混的 real/raw content 双重命名，
  也不为追求字段纯粹性提前增加第二套 block representation。
- **U-015 — Storage mechanics do not define content semantics**: storage type 只描述如何按 pointer
  定位、读取或写入 opaque content bytes；stream 是 bytes 的 execution representation。resolver 才根据
  exact resolver ID、graph 与 metadata 把内容解释为 image/video/audio/PDF 等信息。实现 backing table 不是
  storage type 或 semantic block；不要按 media kind 复制 HTTP/S3/PostgreSQL storage families。
- **U-016 — Metadata follows authority, not a generic container**: protocol/source-declared filename/MIME/length/URL/time
  留在 metadata block canonical content；storage retrieval mechanics 留在 opaque pointer/config；
  content kind 由 exact resolver ID 表达，byte-derived facts 由 solved content 拥有；只有确有长期 use value 的
  derived facts 才由 organization 物化为 graph enrichment。不要仅因 storage-backed block 的 `content`
  被 pointer 占用，就增加无边界的通用 block metadata JSON。
- **U-017 — Effect words name orthogonal controls**: `refresh`、`materialize_missing`、`recompute` 与 `invalidate`
  分别拥有 cache replacement、missing derivation permission、existing derivation regeneration 与 cache eviction
  语义；不能用 `force`/`reload` 把这些 effect 压回一个模糊 boolean。该合同只约束确实提供相应能力的 API，
  不要求所有方法机械增加同一 options bag。
- **U-018 — Relation direction is subject-relative**: `include_in` / `include_out` 是相对 subject block 的 direct
  relation selectors，并在 Python/TypeScript 仅做 casing 投影；它们不是 graph traversal depth/mode。
- **U-019 — Repeated spelling is not yet a common contract**: 多个 source 的 `full` 共享拼写，却混合扩大扫描、
  绕过增量 cutoff、改变顺序与延续分页等效果。Promotion 以稳定语义而非出现次数为准；`full` 当前是待拆解
  vocabulary debt，不是应被固化的 common parameter。
- **U-020 — Conventional version language beats a new synonym**: 当一个轴表达 API、persisted shape 或 resolver
  contract 的 breaking evolution 时，优先使用通行的 `version`，并用限定词说明是哪一种 version；不再用
  `generation` 创造项目内同义词。现有 task packet 中把 product/API/canonical `generation` 当作 `version`
  使用的历史段落属于待批量纠正的 terminology debt，不构成新的领域概念。
- **U-021 — Readiness proves the executable wire contract**: database protocol readiness 不能只检查 schema、
  relation/function names 与 ACL；对 admitted RPC 还要验证 argument names/types、return database type、set/
  volatility shape 和 media-type transport。PostgREST 14 的 raw `bytea` response 需要显式
  `application/octet-stream` domain，而 raw request 只要求 single unnamed `bytea` parameter；这两者不是同一
  capability。内部 trigger/helper function 必须留在 internal schema，不能因为 authenticated peer 需要
  EXECUTE 就进入 public protocol schema。
- **U-022 — Writable storage owns pointer serialization**: application/extension command 只应提交 actual bytes 并
  得到可直接持久化到 `block.content` 的 opaque pointer string；storage handler 自己拥有 internal key → pointer
  grammar。调用者硬编码 PostgreSQL `blob_id` JSON 会让 future S3/Nextcloud storage 反向泄漏进 source domain。
  Python 的低层 caller-session write 可以保留 storage-native key，但 common create seam 应与 client-web 一样
  返回 pointer string。
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
- **U-026 — Disclose dynamic schemas progressively**: Agent 初始上下文只提供完成语义选择所需的 compact exact
  identities 与 descriptions；大型、稀疏使用或 runtime-dependent 的具体 input schemas 通过领域专用查询 Tool
  按需取得。不要把所有可选能力的联合 schema 固定注入每次模型调用，也不要为此建立万能反射服务。
- **U-027 — Domain owners produce the canonical downstream command**: 领域实现拥有其输入 schema、description 与
  语义转换，并直接产生下游 authority 接受的 canonical command。Agent/runtime 只提供注册、路由和 typed
  validation；不要复制领域 schema，也不要增加只为跨 Tool 转换而存在的中间 DTO。Resolver-owned
  StarsGraphForm authoring 通过一个领域拥有的 normalizer 产生 canonical GraphForm，而非交给 LLM 转换，是当前
  reference pressure。
- **U-028 — Separate discovery、proposal and commit by effect**: schema/capability discovery、non-persisting proposal
  construction 与 durable mutation 使用不同的窄 Tool 边界；写入集中到唯一明确 command，但不扩大成通用
  capability invocation、通用事务或 delegation job。
- **U-029 — Do not persist or transmit derivable authority twice**: 当一个值可以通过稳定、低成本且无歧义的不变量
  从同一 command/result 推导时，不再添加第二个字段表达它。Resolver draft 的 `id_start` 已固定为 star Block ID，
  因而额外 `entry_id` 只会制造可分歧的重复 authority。
- **U-030 — Models choose semantics；code enforces mechanics**: LLM/Agent 负责需要语义判断的能力选择、关系表达和
  是否提交；领域模块负责 exact routing、schema validation、identifier allocation、结构不变量与持久化。不要
  用模型处理可确定的机械转换，也不要让通用 runtime 接管领域判断。
- **U-031 — Runtime boundary turns raw input into ordinary typed input**: 接收外部/模型 raw payload 的
  framework/runtime boundary 负责把它反序列化、验证为 typed input；随后被调用的函数接收普通 typed/domain
  input，不再用 `validated_input` 命名、`Validated[T]` wrapper 或额外状态重复表达“边界已经验证过”。这不取消
  各层独有的不变量：Pydantic model 继续拥有自身结构约束，后续模块仍可检查自己拥有的不同约束，数据库继续
  拥有 referential integrity。`submit_graph` 与 `draft_graph → Resolver.create_graph` 是当前 reference pressure。
- **U-032 — Batch-local identity solves mutually referencing creation**: 普通 creation Form 不携带数据库生成的
  identity、timestamps 或其他 database-managed state。当一个批量 command 必须同时声明待创建实体并让同批关系
  引用它们时，command envelope 可以引入仅在该 command 内有效的 identity namespace；对于 bigint row identity，
  InKCre 使用非零 signed ID：负数声明待创建实体，正数引用已有实体，零无效。该 exception 属于批量引用机制，
  不把数据库生成字段重新泄漏进所有 base Forms。GraphForm 是当前 reference pressure。

## Apply Checklist

1. **Memos/RSS implementation done** — confirmed decisions、exclusions 与 acceptance evidence 已冻结。
2. **Hub source projected and published** — PRD claims/workflows、knowledge capability contract、authority/topology
   与 claim matrix 已吸收 Memos、RSS 及 common patterns；`48b069f` 已作为 published `95c4023` 的 ancestor 到达
   Hub main。
3. **Core-py local projected and committed** — Memos/RSS Unit TDD、business pipeline、database runtime v2 与最近
   local guides 已和 implementation reconcile；commit `835f89a` 未编辑 `docs/_shared`。
4. **Client-web local projected and committed** — peer hydration、exact semantic resolvers、PostgreSQL CRUD 与
   safe browser handles 已进入 local architecture；commit `765b22f` 未编辑其 `docs/_shared`。
5. **Verification complete** — Hub `git diff --check` + SVC noop；45 relative links resolved；core-py owner docs
   Ruff-format/repository-lint green；client-web complete `pnpm check` green。Core-py full formatter only retains four
   unrelated pre-existing guide drifts。
6. **Owner-separated publication complete** — Hub 先发布 `95c4023`；core-py `cc8f90a` 与 client-web `8324293`
   随后各自只提交 `docs/_shared` gitlink。client-web remote 后续被观察为已同步；core-py push 与 production
   migration 仍是独立 operation。
7. **Tactical guides repaired** — retired semantic HTTP IDs、raw-content domain terminology、scheduler dual-path、
   Memos attachment v1 与 client-web pointer-rendering docs 已修正。
8. **Semantic retrieval projected and verified** — core-py `semantic-retrieval.md`、business-pipeline and runtime/
   development docs，client-web Peer/runtime architecture，and the Hub source PRD/Product TDD match I0–I8 implementation。
   Credentialed DashScope Acceptance is 6/6；Hub links/diff/SVC noop are green。Hub publication and both exact Spoke
   shared-ref commits are complete without mixing owners。
