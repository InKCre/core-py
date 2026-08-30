# Graph Resolver Storage

> Architecture-understanding provenance shard. See [index](index.md).

- **U-002 — Attachment position**: association 默认无序；显式 inline reference 才拥有位置。
- **U-003 — Ordered slots are not linked lists**: `root --slot--> component` 是 slot mapping；
  当前 relation fetchsert identity 也不直接支持只换 `to_` 的 slot semantics。
- **U-004 — Text storage can carry a grammar**: JSON/text 并非天然无结构，但也不会自动获得
  canonical identity、typed query 或统一解释；resolver 不是 relation content 的唯一消费者。
- **U-005 — No historical support is not no version architecture**: 当前 target 已固定 0.29.1；
  future breaking generation 仍需要显式 adapter/generation boundary。
- **U-006 — Family canonical is not a god object**: CanonicalMemo 属于 memo extension，且就在
  graph root content 内；它不与 info-base 竞争 authority。
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
- **U-022 — Writable storage owns pointer serialization**: application/extension command 只应提交 actual bytes 并
  得到可直接持久化到 `block.content` 的 opaque pointer string；storage handler 自己拥有 internal key → pointer
  grammar。调用者硬编码 PostgreSQL `blob_id` JSON 会让 future S3/Nextcloud storage 反向泄漏进 source domain。
  Python 的低层 caller-session write 可以保留 storage-native key，但 common create seam 应与 client-web 一样
  返回 pointer string。
- **U-027 — Domain owners produce the canonical downstream command**: 领域实现拥有其输入 schema、description 与
  语义转换，并直接产生下游 authority 接受的 canonical command。Agent/runtime 只提供注册、路由和 typed
  validation；不要复制领域 schema，也不要增加只为跨 Tool 转换而存在的中间 DTO。Resolver-owned
  StarsGraphForm authoring 通过一个领域拥有的 normalizer 产生 canonical GraphForm，而非交给 LLM 转换，是当前
  reference pressure。
- **U-029 — Do not persist or transmit derivable authority twice**: 当一个值可以通过稳定、低成本且无歧义的不变量
  从同一 command/result 推导时，不再添加第二个字段表达它。Resolver draft 的 `id_start` 已固定为 star Block ID，
  因而额外 `entry_id` 只会制造可分歧的重复 authority。
- **U-032 — Batch-local identity solves mutually referencing creation**: 普通 creation Form 不携带数据库生成的
  identity、timestamps 或其他 database-managed state。当一个批量 command 必须同时声明待创建实体并让同批关系
  引用它们时，command envelope 可以引入仅在该 command 内有效的 identity namespace；对于 bigint row identity，
  InKCre 使用非零 signed ID：负数声明待创建实体，正数引用已有实体，零无效。该 exception 属于批量引用机制，
  不把数据库生成字段重新泄漏进所有 base Forms。GraphForm 是当前 reference pressure。
- **U-040 — Resolve common Source materialization policy through explicit → deployment default → built-in fallback**:
  外部 bytes 的目标 Storage 是 Source-domain local policy，不是具体协议参数。显式 Source 选择优先，其次是
  deployment-scoped 默认 writable Storage；二者均缺失时使用一定可用的内置 PostgreSQL binary Storage。只有
  “未配置”才能进入下一层；已配置但不存在或不可写必须暴露配置/能力错误，不能被 fallback 静默掩盖。Mail
  D-282 是第一个 reference pressure；D-283 将 per-Source explicit reference 提升为 nullable
  `sources.storage`。D-284 进一步确认 code/catalog 能力一致性属于 Storage registry/bootstrap 系统边界，而不是
  通过每次使用时的 defensive getter 重复发现。D-285 将 derived capability projection 固定为
  `storage_types.writable`；Source reference 只能选择其 type 可写的 Storage instance。
- **U-041 — Resolver solving exposes semantic completion，not internal command status**（candidate Product TDD / Unit TDD）：
  `get_solved_content` 返回调用者需要的 use-facing solved content；内部 lazy materialization 是 create、reuse、race
  还是 fetch，不应自动扩大成 public outcome。只有该事实本身属于领域 solved semantics 时才暴露。这个浅完成合同
  应由 Resolver base docstring 与 peer-equivalent contract 拥有，让调用者无需理解深模块内部状态代数。Mail D-288
  是当前 reference pressure。
- **U-042 — Do not let tolerated residue shape the common API**（candidate Product TDD / Unit TDD）：低概率、低损害、
  best-effort 容忍的冗余或竞态残留不是受鼓励的领域行为；不要为了让它“更可预测”而在高频路径散布稳定选择、
  duplicate-aware 分支或专用 utility，否则会把妥协提升成事实上的公共合同。公共深接口应表达正常 use operation：
  例如 InfoBaseManager 的 singular related-Block read 只返回任一满足关系谓词的 Block，不承诺 uniqueness、order 或
  repeat-read stability；use-facing output 的 cardinality 继续服从领域语义，而不是被持久化冗余改写；需要观察全部
  graph facts 的调用者仍使用普通多值查询。该原则不适用于 identity reconciliation/mutation：后者继续要求
  U-034 的 exact-one resolution。Mail D-289/D-291 是当前 reference pressure。
- **U-047 — Derive implementation-owned capabilities once，then enforce durable references at the data boundary**
  （candidate Product TDD / Unit TDD）：当能力由注册的实现类拥有、而持久 reference 的合法性依赖该能力时，
  registry/bootstrap 将实现 contract 投影到 catalog，数据库约束保证引用不会进入不可能状态，普通 use path
  直接依赖这个已建立的不变量。不要让每个 caller 反复 rediscover `isinstance`，也不要让可编辑 catalog 反过来成为
  代码能力的 authority。`WritableStorage → storage_types.writable → sources.storage` constraint 是当前 reference
  pressure（D-284/D-285/D-290）。
