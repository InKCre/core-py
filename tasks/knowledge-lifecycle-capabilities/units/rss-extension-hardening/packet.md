# RSS Extension Hardening

- **Unit ID**: `rss-extension-hardening`。
- **Track**: Collection。
- **State**: Closed；B0–B8 implementation/verification 与 Hub/core-py/client-web durable reconciliation 已闭合。
  Commit、push、Hub publication、shared-ref bump 与 production migration 仍等待各自授权，不是 unit close gate。
- **Objective**: 让一个配置好的 RSS 2.0 / Atom source 能可靠地把 feed-native information 收集为
  resolver-readable graph，并建立首份可信的
  `source instance → collect job → graph → resolver → source state` reference contract。
- **Guardrail**: hardening 是端到端产品/技术合同，不是“重构旧代码”或一次性清理所有 sources；
  不把 feed reader、organization、semantic retrieval、所有 RSS/Atom edge case 或通用 source framework
  偷渡进当前 unit。
- **Gate**: Sir 的 completion review；没有遗留 Product/Technical blocker。
- **Next Step**: owner-specific commit/publication decision，或由 program 选择下一个 implementable unit。

## Execution Progress

- **B0 complete — 2026-08-02**：root/RSS manifests and locks now freeze Pillow 12.3.0、PyAV 18.0.0、
  pypdf 6.14.2、puremagic 2.2.0、feedparser 6.0.14 and Trafilatura 2.2.0。Existing locked package versions were
  reused where compatible rather than opportunistically upgraded。
- The exact nine-ID case table and repository-owned generator live under `tests/assets/semantic-content/`；generated
  real PNG/WAV/MP4/PDF/EPUB/ZIP/text/HTML/file samples are Git-ignored and rebuilt by a shared pytest fixture，so no
  downloaded media is redistributed and a clean checkout does not depend on committed derived data。
- Local Python 3.12 imports and a production `python:3.12-slim` Dockerfile build/import probe succeeded。The temporary
  image was removed after proof；the remote Docker path avoided Mac main-disk use。
- Full `pdm run check` code/tests passed。Its formatter also reported pre-existing unrelated Markdown/Memos-test
  formatting drift；new B0 Python/task-plan files pass their targeted Ruff lint/format checks。
- **B1 complete — 2026-08-02**：`block.content` now stays inline content or an opaque pointer；both peers expose
  block-owned instance hydration with `refresh`，one generic bounded HTTP byte storage replaces semantic HTTP storage
  handlers，and PostgreSQL binary storage has pointer-stable C/R/U/D without querying blocks。
- The peer database contract is now `peer-database-runtime-v2` at migration head `d0e3f4a5b6c7`。Append-only
  migrations add raw create/read RPCs，RESTRICT storage deletion，move the trigger helper out of the exposed protocol
  schema，and add PostgREST 14's explicit `application/octet-stream` response domain。Readiness validates exact public
  function names、argument/return database types、set/volatility shape and ACLs rather than accepting any exposed
  function with the right privilege。
- A disposable development runtime passed complete contract readiness and a real authenticated PostgREST probe：
  create → byte-exact read → same-pointer update → refreshed byte-exact read → delete。Core-py then passed 266 tests
  with 6 environment skips；client-web passed its complete `pnpm check` including 47 unit/runtime tests、all workspace
  type checks and production builds。
- client-web's delivery pin intentionally remains on the last delivered core image/migration until B8 delivery
  ordering；the local v2 protocol projection is generated now，but a peer must not claim attachment to the new runtime
  head before that artifact is actually delivered。
- **B2 complete — 2026-08-02**：Python/TypeScript resolver bases now expose exact registration、typed unknown/
  unsupported outcomes、stable `refresh`/`materialize_missing` semantics and explicit core bootstrap。Embedding
  consumers skip supported-null/unsupported/retired unknown values without inventing text。
- **B3 complete — 2026-08-02**：both peers register the nine `core.<kind>.v1` contracts。core-py performs bounded
  real-format inspection；client-web owns local hydration/render/open handles and object-URL cleanup without exposing
  storage pointers。The bare IDs and semantic HTTP storage handlers are hard cut off。
- **B4 complete — 2026-08-02**：Memos attachment v2 is metadata → semantic content → PostgreSQL bytes。The guarded
  v1→v2 migration preserves metadata ID、blob UUID/bytes and ordered memo relations，and refuses irreversible/shared
  downgrade shapes。Real PostgreSQL Memos acceptance remains green after the shared writable-storage pointer seam。
- **B5 complete — 2026-08-02**：Twitter now emits a versioned root and relation-owned exact semantic attachments/
  links；webext producers emit exact core IDs。Static scans find no current bare semantic resolver or content-kind HTTP
  storage producer。
- **B6 complete — 2026-08-02**：RSS/Atom keep their durable source type IDs as thin wrappers over one bounded
  feedparser service。Manual and scheduled runs create ordinary collect jobs；claim is atomic。Exact feed/item
  reconciliation、per-item primary transactions、conditional requests、structured diagnostics、unidentified
  create/discard/watermark and retry residue are proven through a real HTTP double and PostgreSQL。
- **B7 complete — 2026-08-02**：default Trafilatura full text is a separate `full_text` semantic block and use-time
  preference；manual/automatic enclosure materialization uses resolver-instance commands、protocol-specific evidence
  order、writable storage and one idempotent `content` child。Real image/audio/video/PDF/EPUB/ZIP/file bytes and
  concurrent materialization are covered。
- **B8 complete — 2026-08-02**：core-py has zero Pyrefly diagnostics、293 passed/19 environment skips，migration head
  `e1f4a5b6c7d8` and 15 real PostgreSQL Memos+RSS cases；client-web complete `pnpm check` has 56 tests plus all builds。
  Replaceable live RSS/Atom smoke exists behind `INKCRE_LIVE_RSS_URL` / `INKCRE_LIVE_ATOM_URL` and is skipped when no
  endpoint is explicitly selected。Repository-wide format still reports pre-existing unrelated Markdown drift；all
  implementation-owned code surfaces are green。
- **B8 follow-up — 2026-08-02**：semantic-content generated samples are now ignored and rebuilt on demand；flat root
  tests were grouped by `app`、`deployment`、`info_base`、`extensions` and `libs` ownership without changing behavior。
- **Durable reconciliation — 2026-08-02**：Hub PRD/Product TDD、core-py RSS/Memos/business-pipeline/database/guides
  与 client-web peer-local info-base architecture 已按 owner 更新。Hub SVC integration reports `noop`，45 relative
  links exist，core-py owner docs pass Ruff format and repository lint，client-web complete `pnpm check` remains green。

## Confirmed Direction

- D-050：feed-authored title/summary/content 保持 canonical authority；抓取全文是独立 graph enrichment，
  use-facing text 可在存在时优先使用全文，enrichment failure 不使有效 feed item collection 失败。
- D-051：保留 `rss` extension identity，内部行为重写；旧 collector/state/resolver/graph/tests 仅作为
  evidence，不作为增量修改基础。
- D-052：full-text enrichment 属于本次 MVP 的第二个 vertical slice，默认开启、可按 source config
  关闭；不使用长度 heuristic，失败不影响 primary item，unchanged item 不无条件重复抓取。
- D-053：Atom ID → scoped RSS GUID → alternate link；exact match update/idempotent，不 fuzzy overwrite；
  provenance 在 canonical content，local identity 是 `block.id`。ID/link 均缺失时不使用 normalized-payload
  fingerprint；source config 可选择 create（默认，每次形成新 block）或 discard（带 diagnostic）。
- D-054：feed/channel-native information 是独立 block，item 通过 relation 关联它；source instance 只拥有
  collection config/runtime state，不替代 feed block，也不把 feed metadata 复制到每个 item root。
- D-055：feed identity 依次使用 Atom feed ID、feed-declared self link、source-instance-scoped configured
  feed URL；exact match 更新同一 feed block，无法证明 continuity 的 configured-URL change 创建新 block。
- D-056：unidentified item 的 `create` policy 使用 previous successful contentful snapshot observation time
  作为 source-time admission watermark；首次/无可信时间仍创建，较旧时间过滤，`304` 不推进；该 heuristic
  不是 identity/reconciliation，也不允许按 document order short-circuit。
- D-057：enclosure metadata block 是独立 block；RSS extension 提供 enclosure-block-input manual
  download endpoint，source config 也拥有 automatic download policy 与 target writable storage。resolver
  解释 block，application service 执行下载/存储/graph command，materialization 不覆盖 enclosure authority；
  下载结果按语义成为 audio/video/image/PDF/EPUB/ZIP，unknown/unsupported fallback 为带 MIME 的 file block，
  而不是按 storage bytes 命名为 binary block。
- D-058：不拆独立 media foundation unit；RSS vertical 发现的 core media/storage 与 Memos attachment 修正
  留在同一 unit loop，但分别保留 durable owner、Impact Handshake 与 regression boundary。
- D-059：MemosAttachment 保留为 attachment metadata block，并通过 content relation 指向 media/file
  semantic content block；ordered memo relation 与 unattached list/lifecycle 留在 metadata block，actual bytes 留在 semantic content block 的
  storage。该两层 shape 只在 source object 独立有用时采用，不机械套用。
- D-060：不增加 `storage_pointer` 或 `BlockRecord`；`content` 在 inline block 上保存实际内容，在
  storage-backed block 上保存 opaque pointer。`BlockModel.get_hydrated_content()` 统一延迟读取实际内容并
  缓存到非映射 `_hydrated_content`，持久 content/storage 变化时失效；storage deletion 改为 RESTRICT。
- D-061：storage semantics/pointer 是 shared protocol，handler 是 peer-local runtime capability；缺失 handler
  明确失败，不隐式委托 core-py。client-web 本轮必须在本地执行 PostgreSQL storage capability。
- D-062：storage type 只描述 opaque content bytes 的 access/persistence mechanics；resolver 根据 exact resolver ID
  与 graph/metadata 解释 image/video/audio/PDF 等信息类型。现有 content-kind-specific HTTP storage types
  需要重构，replacement naming/shape 尚未冻结。
- D-063：client-web `packages/core` 本轮完整支持 PostgreSQL bytes 的 create/read/update/delete；仍通过
  PostgREST 访问 admitted database surface，不委托 core-py。storage CRUD 只处理 pointer + bytes，不反向
  查询或修改 block；具体 raw-binary wire shape 在实现前冻结。
- D-064：`block.updated_at` 只表示 persisted block record 的更新时间，不保证 storage-backed actual content
  freshness。hydrated cache 是 instance-local snapshot；跨实例/peer freshness 与 derived-data reconciliation
  不由 storage CRUD 保证。
- D-065：core-py `get_hydrated_content(refresh=True)` 与 client-web
  `getHydratedContent({ refresh: true })` 显式绕过并替换 instance cache；默认读取复用 lazy snapshot，不增加
  TTL、polling、storage-version inference 或跨实例/peer invalidation。
- D-066：client-web PostgreSQL CRUD 使用 raw octet-stream RPC Create/Read + exact relation Update/Delete；
  Update 以 PostgreSQL hex bytea PATCH 同一 UUID，避免为双参数 raw body 发明 header/envelope。raw fetch 只在
  `packages/core` 承担认证与 `ArrayBuffer`，contract types 通过正常生成路径同步。
- D-067：protocol/source-authored metadata 留在 metadata block，storage mechanics 留在 opaque pointer/config，
  content kind 由 exact resolver ID 表达，byte-derived facts 由 resolver solved content 拥有，organization 只物化有长期 use
  value 的 derived facts。本轮不增加 `blocks.metadata`；Memos attachment 的 blob pointer 移入相关
  semantic content block。
- D-068：S3-compatible storage 的通用价值成立，但实现排入 future Nextcloud Files unit；RSS enclosure 先以
  PostgreSQL writable storage materialize，不把无法整体驻留内存的罕见大文件设为验收条件，也不为 future
  S3 提前增加 streaming storage abstraction。
- D-069：media classification policy 由理解 source protocol 的 extension adapter 拥有；core 只提供 MIME
  normalization/detection 与 registered resolver matching 等 opt-in `ResolverManager` mechanisms，不新增
  media module，也不在 `ResolverBase` 固定 global ladder。Memos `type`、RSS required enclosure `type/length`
  与 Atom advisory link `type` 具有不同合同。
- D-070：Memos adapter 要求/normalize `Attachment.type`，通过 `ResolverManager` 映射 exact resolver ID；unknown
  MIME fallback 为 file。attachment metadata block 保留声明并用于 native response；不做 mandatory byte sniff 或 mismatch reject。
- D-071：合法、具体的 RSS `enclosure.type` 是 resolver selection 的 primary evidence；unknown valid MIME → file，
  声明缺失/无效/泛化/不可映射时才使用 HTTP、filename/URL 或 optional byte detection，且不覆盖 metadata block。
- D-072：Atom materialization 先使用 specific HTTP Content-Type，再使用 advisory `link.type`，最后才调用
  extension-owned filename/URL/byte fallback；unknown → file，任何 observed/detected value 都不覆盖 metadata block。
- D-073：resolver 负责使 block + graph 可被 application 使用；text/embedding representation 是 optional
  capability。resolution 可按需调用 AI/organization 并持久化 missing graph，问题在于 effect policy/幂等/
  concurrency 不明确，而不是 read-triggered write 本身。
- D-074：ordinary resolver use 默认允许 materialize missing graph；显式 `materialize_missing=False` 是
  read-only attempt。`refresh` 只绕过/替换 local snapshot，不自行授权 materialization 或重新生成；
  `recompute` 属于 organization，`invalidate` 只丢弃缓存。`include_in/include_out` 固定 direct relation
  direction；new InKCre-owned API 不使用模糊 `force`。Legacy source-job `full` 不提升为 common contract。
- D-075：九个 common semantic content resolver IDs 使用 `core.<kind>.v1`，`v1` 是 resolver contract
  version；metadata block 通过 `content` relation 指向 semantic content block。`get_text()` /
  `get_str_for_embedding()` 保留 abstract methods，concrete resolver 必须返回 value/`None` 或显式抛
  `UnsupportedResolverCapability`；capability 在 resolver instance 上请求，不经 `ResolverManager`。裸
  `text/html/image/video` IDs hard cut-off，不保留 decoder 或 data migration。
- D-049：runtime acceptance black-box-first，结构性验证尽量交给 static mechanisms。
- 成熟协议库负责 parser/extractor；InKCre 只实现无法外包的 HTTP policy、canonical mapping、identity/
  reconciliation、graph、job/state 与 failure semantics。

## Why This Unit

Memos backend 验证了 extension-owned protocol collection，却没有经过传统 `SourceBase`、source instance、
collect job、source state 和 scheduler path。RSS/Atom 是开放、无账号、HTTP boundary 可控的 vertical，可以在
引入 CalDAV、Nextcloud Files、Apple Notes 前，以最低外部环境成本验证这条 collection path。

## Baseline Evidence (superseded by the completed rewrite)

重写前实现只能解析基本 RSS/Atom fields 并生成一个 `feed_item` root block，不能证明可靠 collection：

更完整的 media/storage 横向 evidence 见 [media-storage-evidence.md](media-storage-evidence.md)。
Exact resolver contract/solved-content proposal 见
[semantic-content-resolver-contracts.md](semantic-content-resolver-contracts.md)；它已由 D-075 确认。
Implementation dependency/cut-over preflight 见
[implementation-preflight.md](implementation-preflight.md)；它是在 formal plan 写成后对其地址、依赖顺序、
migration branches 和 runtime assumptions 所做的 validation report，不拥有 implementation sequence。
Formal batch/file/verification sequencing 见 [implementation-plan.md](implementation-plan.md)；它现在拥有 intended
implementation steps，preflight 只验证而不再冒充 plan。

- `seen_ids` 使已见 item 永久跳过，因此同一 native ID 的内容更新无法进入既有 block；`full=true`
  又绕过该状态，而默认 content-equality fetchsert 可能在内容变化时创建 duplicate block。
- RSS GUID 的 uniqueness scope 通常属于 feed；Atom ID 的 native contract 不等同于当前
  `(resolver, serialized content)` identity。当前 graph 没有 exact source-instance/native-ID
  reconciliation contract。
- 缺少 ID 与 link 的 item 在协议上仍可能出现，但实证上很少见：RFC 4287 要求合规 Atom entry 恰有一个
  `atom:id`；Hmedeh 等人在 8,155 个 RSS/Atom feeds 的八个月 corpus 中测得 item `link` 出现率为
  99.88%，所以该 corpus 中同时缺少 link 与 ID/GUID 的比例至多为 0.12%，实际更低。该 2011 corpus
  不是当前互联网的精确统计，只用于确认这是低频 fallback，而不是给出长期概率。
  Evidence: [RFC 4287](https://www.rfc-editor.org/rfc/rfc4287)，
  [Characterizing Web Syndication Behavior and Content](https://link.springer.com/chapter/10.1007/978-3-642-24434-6_3)。
- `seen_ids` 先进入 Python `set` 再截取 1000 项，顺序不稳定，也不表示最近确认的 1000 个 identities。
- graph commit 与 source state update 使用两个 transaction；失败/重试时的 primary effect、state advance
  和 duplicate 语义没有验收合同。
- core 已有 source-specific `SourceModel.state` 与 collect-job `started_at/closed_at`，但没有“feed snapshot
  被成功观察”的时间事实。若采用 time cutoff，应由 RSS source 在收到完整响应时捕获
  `snapshot_observed_at`，只在 collection 成功后推进到 source state；不能直接把 job completion time
  当作 feed observation time。
- 缺少 `feed_url` 时 `collect()` 正常 return，collect job 会被标记 FINISHED；job config 的 `full` 也没有
  typed validation。更根本的是，同名选项在 RSS/Atom、Mail、GitHub Stars 与 Twitter Bookmark 中分别混合
  incremental cutoff bypass、scan breadth、ordering 和 pagination effects，不能直接保留为 shared
  source-runtime semantic。
- scheduled source path 直接调 `collect`，没有创建/传入 collect job，与 `collect(job)` signature 和
  product job contract 冲突。
- enclosures 只是 root JSON 内的 URL tuple，没有检验它们是否应成为可独立 resolve/use 的 component
  blocks/relations；feed identity/title 也被逐 item 复制。
- core 已有 storage type/instance registry、`WritableStorage` 与 built-in PostgreSQL binary storage；所以
  source-configured target storage 不需要 RSS-specific storage switch。现有 write contract 接受整块 `bytes`
  且依赖同步 DB session，不足以证明大型 enclosure streaming 或 S3 external-object lifecycle。
- truncated-content heuristic 可能抓取 link 页面并用 readability text 替代 feed-authored content，原始
  fidelity、失败、rate limit 和 observable provenance 未定义。
- resolver ID `feed_item` 未 namespace/version；schema evolution、installed resolver retention 与 unknown
  resolver-ID behavior 未形成 feed contract。
- tests 主要覆盖 schema、resolver text helper、truncation helper 和独立 XML parsing，没有执行
  `collect → database graph → resolver → state/job`，也没有 update/idempotency/failure black-box proof。

## Proposed Hardening Contract Areas

### 1. Product and content fidelity

- feed-authored item 与 fetched full text 必须可区分；前者是 authority，后者是 independent enrichment。
- 本次 MVP 实际抓取全文；默认开启且可关闭，并作为 canonical feed collection 后的第二个 slice。
- 定义 RSS 2.0 / Atom 的 bounded supported shapes；unsupported/malformed item 不得伪装成功。
- 明确 enclosure、feed metadata 与 fetched article content 哪些是 independently useful graph components。

### 2. Native identity and change behavior

- D-053 已固定 RSS GUID / Atom ID / link ladder 与 native uniqueness scope fallback，并明确排除 payload
  fingerprint。
- 同一 exact identity 再次出现时 update existing canonical root；ID/link 均缺失时按 source config
  `create`（默认）或 `discard`。`create` 每次形成新 block，不声称 reconciliation；`discard` 暴露诊断。
- D-056：`create` 对拥有可信 source-native timestamp 的 unidentified
  item 使用前一次 successful snapshot observation time 作为 admission cutoff；首次 collect 或 timestamp
  缺失/不可解析时仍创建。该 watermark 只减少 duplicate，不升级为 item identity；不得依赖 document
  order 提前结束扫描。
- feed block identity 依次使用 Atom feed ID、declared self link、source-instance-scoped configured URL；
  无 exact continuity proof 的 configured-URL change 创建新 feed block。
- feed window 中 item 消失不表示 source deletion，不自动删除 block。
- config/feed identity 改变、`full` collect、conditional HTTP state 与 state truncation 必须有明确语义。

### 3. Canonical graph and resolver

- 选择 versioned, namespaced feed canonical resolver contract，不直接让 RSS 或 Atom 任一 wire shape 成为 family
  authority。
- feed/channel-native information 形成独立 block；source instance config/runtime state 不进入该信息 block，
  item 通过 relation 关联 feed block。
- root 只保存 item root facts；独立 components/associations 只存在 graph relations 中。
- resolver 从 root content + relations 产生 solved feed item，text/embedding input 不直接绕过 canonical
  interpretation。
- enclosure 是 metadata block。manual extension endpoint 与 automatic source policy 都以
  exact enclosure resolver interpretation 为输入；application service 执行有副作用的 materialization，
  downloaded block 通过 relation 连接 enclosure，不能覆盖原始 enclosure content。
- downloaded block 的 resolver 表达 media information kind（通常 audio/video/image），storage 只拥有 raw
  bytes/pointer。本次也建立 PDF/EPUB/ZIP 与 file fallback。现有 image/video resolver 的 storage
  assumptions，以及缺失的 audio/PDF/EPUB/ZIP/file resolver 属于 Technical preflight pressure，旧实现
  不自动成为新合同。
- Memos attachment 也必须迁移到该 semantic content path；其 0.29.1 protocol identity/attachment role 与
  media/file information 是否由一层或两层 block 承担，先在 Product gate 明确。

### 3A. Third-party library assessment

- **Recommended parser — `feedparser` 6.0.12**：2025-09 仍发布版本；覆盖 RSS/Atom variants、
  content normalization、namespaces、relative URI、encoding/date variants、enclosures、feed version 与
  malformed-feed `bozo` signal。Technical preflight 固定 exact compatible version。
- **Rejected as architecture — `reader` fat model**：它提供自己的 feed/entry persistence、read/important
  state、search、update scheduling 与 plugins；整体采用会建立 graph/source/application 之外的并行 authority。
  可以参考其 behavior，但不把它作为 InKCre feed domain owner。
- **Recommended future full-text extractor — `trafilatura`**：只对 InKCre HTTP client 已取得的 HTML 做
  main-text/Markdown extraction，不使用其 downloader/storage。Exact dependency 只有在 full-text scope 获批
  后进入 plan。
- **Transport**：继续由 InKCre async HTTP boundary 负责 timeout、redirect、conditional request、headers、
  response size 和 errors；把 response bytes、effective URL 与必要 headers 交给 parser。不要为了使用
  `feedparser.parse(url)` 把网络策略隐藏进 synchronous parser call。

### 4. Source runtime and configuration

- source config 与 job config 在持久/live effect 前 typed validate；missing/invalid feed URL 是失败而不是
  successful no-op。
- schedule 只创建普通 collect job，由同一 job runner 执行，避免第二条未跟踪 collection path。
- collect job 的 PENDING/RUNNING/FINISHED/FAILED 与 source state advance 对应可观察 primary effect。
- RSS 只推动交付所需的最小 shared source-runtime change；可复用 config update abstraction 需以 extension
  和 RSS 两个真实 pressure 校验后再提取。
- source config 必须提供 enclosure automatic-download policy 与 target writable storage ID；manual endpoint
  也必须有明确 target-storage selection。configured storage 不可写或 unavailable 时不得假装下载成功。

### 5. Failure, retry, and partial effects

- 分开 feed fetch/parse、optional article fetch、graph persistence、state update 的失败语义。
- 不预设 atomic complete graph；但 job success、state advance 和 retry 不得互相矛盾。
- transient HTTP failure、malformed feed、one malformed item、storage/resolver failure 和 process interruption
  都需要 black-box scenario 证明后果。

### 6. Acceptance and regression baseline

- acceptance 默认从 public/runtime boundary 驱动，不直接实例化 Pydantic schema、private helper、
  truncation predicate 或 BeautifulSoup parsing fragment。类型、签名、exhaustiveness 与结构错误尽量交给
  Pyrefly、Ruff 和其他 static checks；Pydantic runtime validation/serialization 由实际 collection path
  间接覆盖，不冒充 static proof。
- hermetic black-box double 通过真实 HTTP transport 提供 RSS 2.0 / Atom，并驱动真实 source instance →
  collect job → committed PostgreSQL graph → resolver solved value → source state。它覆盖 create、
  same-content replay、same-ID update、new item、missing old item、enclosure、malformed item 与
  conditional/no-change response。
- 至少增加 opt-in live RSS 与 live Atom smoke，消费真实网络 feed，只断言协议/collection invariants，
  不固定随时间变化的 exact items。Live endpoint selection 在 preflight 调研并记录可用性/失效替代。
- scheduler proof：scheduled trigger creates exactly one traceable collect job，不直接运行 source。
- failure proof：job status/error、graph residue、state advance 与 retry result 符合批准合同。
- repository-wide regression：其它 source types 不因 shared runtime change 而改变未批准行为。

### 7. Existing test replacement

- 当前 `tests/extensions/test_rss.py` 主要是 schema/default/serialization、resolver helper、truncation helper
  与直接 XML fragment parsing；它们不构成 collection acceptance。
- implementation 时删除这些低价值 white-box tests，以新的 black-box suite 和 static checks 取代，
  不是在 replacement 之前单纯降低 coverage。
- 只有无法从 public boundary 稳定观察、且 static analysis 不能证明的高价值 pure behavior 才保留
  targeted test；需要在 plan 中逐项说明为什么值得存在。

## Explicit Non-Goals

- 一次 harden Twitter、GitHub、Mail、Telegram 或所有 source classes。
- 构建 generic external-resource/source-binding table。
- 把 source `_organize` 或 resolver `breakdown` 当作 collection success 的一部分。
- 实现 feed reader UI、OPML management、semantic retrieval 或 recommendation。
- 仅因理论 SSRF/secret 风险禁止 owner 明确配置的 feed URL；安全边界按 repository security model 的
  concrete harm 与比例原则审查。

## Historical Design Probes (superseded by the approved implementation plan)

这些只是 design probes，不是 execution plan：

1. freeze product/content/identity black-box scenarios and live-smoke invariants；
2. `feedparser` adapter + versioned feed-family canonical；
3. exact reconcile/update + deterministic source state；
4. scheduler/job/config correctness；
5. enclosure/full-content graph mapping；
6. manual + source-policy enclosure materialization through resolver/storage；
7. Memos attachment semantic-media migration + exact backend regression；
8. replace legacy schema/helper tests with black-box + static verification；
9. failure/retry PostgreSQL integration；
10. compatibility hardening、durable promotion 与 regression。
