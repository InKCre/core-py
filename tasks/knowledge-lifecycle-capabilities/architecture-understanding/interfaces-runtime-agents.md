# Interfaces Runtime Agents

> Architecture-understanding provenance shard. See [index](index.md).

- **U-009 — A plan can be a design probe before it is executable**: 代码地址、依赖和可验收纵切可以
  在 Technical/Acceptance 阶段暴露遗漏合同；只有上游获批且分叉关闭后，才冻结为 execution
  baseline。
- **U-010 — Client base URL participates in route compatibility**: protocol annotations 的 relative
  path 必须与 client 对 configurable host path 的保留/拼接一起判断；不能只看到 `api/v1` 就推断
  server-root mount。MoeMemos 可用 `/memos/` base URL 复用当前 extension namespace。
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
- **U-026 — Disclose dynamic schemas progressively**: Agent 初始上下文只提供完成语义选择所需的 compact exact
  identities 与 descriptions；大型、稀疏使用或 runtime-dependent 的具体 input schemas 通过领域专用查询 Tool
  按需取得。不要把所有可选能力的联合 schema 固定注入每次模型调用，也不要为此建立万能反射服务。
- **U-028 — Separate discovery、proposal and commit by effect**: schema/capability discovery、non-persisting proposal
  construction 与 durable mutation 使用不同的窄 Tool 边界；写入集中到唯一明确 command，但不扩大成通用
  capability invocation、通用事务或 delegation job。
- **U-030 — Models choose semantics；code enforces mechanics**: LLM/Agent 负责需要语义判断的能力选择、关系表达和
  是否提交；领域模块负责 exact routing、schema validation、identifier allocation、结构不变量与持久化。不要
  用模型处理可确定的机械转换，也不要让通用 runtime 接管领域判断。
- **U-031 — Runtime boundary turns raw input into ordinary typed input**: 接收外部/模型 raw payload 的
  framework/runtime boundary 负责把它反序列化、验证为 typed input；随后被调用的函数接收普通 typed/domain
  input，不再用 `validated_input` 命名、`Validated[T]` wrapper 或额外状态重复表达“边界已经验证过”。这不取消
  各层独有的不变量：Pydantic model 继续拥有自身结构约束，后续模块仍可检查自己拥有的不同约束，数据库继续
  拥有 referential integrity。`submit_graph` 与 `draft_graph → Resolver.create_graph` 是当前 reference pressure。
- **U-038 — Keep protocol identity separate from protocol parameters**: protocol 回答“使用哪套通信合同”，
  parameters 回答“如何构造/进入该合同的一个具体 endpoint”；两者 authority、schema 与 consumer
  不同，不应展平或混合在同一 object namespace。Protocol 字段应当判别 parameters schema，但 protocol
  identity 必须忠于其真实 authority：可以是 InKCre-owned exact/versioned Peer wire contract，也可以是公开
  IMAP/POP3 standard，不因结构复用而强行内部化。Peer D-123/D-124 与 Mail D-275/D-276 是当前
  reference pressure。该分离不要求 typed protocol vocabulary 预先列举已知但未支持的标准；Mail D-277
  将当前有效值收窄为 `Literal["imap"]`。
- **U-039 — Bind external-resource lifetime to a domain command with native language scope**: factory 只构造对象、
  不产生 I/O；领域 command 通过语言原生 resource scope 取得、使用并释放外部连接。这使 exception、
  cancellation 和 normal completion 共享一个清理 authority，调用者无需理解 partial connection state；也不应
  在没有实测回报前扩张成 cross-command cache/pool/lifecycle manager。Mail D-279 是当前 reference
  pressure，Python async context manager 是其当前 concrete mechanism。
- **U-050 — Deep interfaces optimize caller understanding，not method-count minimalism**: 把不同语义、参数集合和
  outcome 的操作塞进一个 generic method，只会把 discriminator、合法组合与分支知识推给每个 caller。优先暴露
  少量但角色清晰、语义内聚的入口，由深模块隐藏查询、路由、分页和结构不变量。Graph 的 Block/Relation
  neighborhood methods 是当前 evidence；这不是鼓励为每个细节拆方法，而是以 caller 需要理解多少为判断标准。
