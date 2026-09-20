# Durable Documentation Promotion Plan

## Navigation

- [Agent Query 文档 authority 纠正](../units/agent-query-sink/documentation-authority.md)：D-631 纳入本 unit，
  包括消费者越权定义、旧合同副本与长期判断准则；尚未应用，新增 Hub meta 影响面。

- [Known corrections](known-corrections.md)
- [Candidate Hub PRD batch](hub-prd.md)
- [Candidate Hub Product TDD batch](hub-product-tdd.md)
- [Spoke Unit TDD promotion](spoke-unit-tdd.md)
- [Organization 交付后的待提升项](organization.md)：本地实现/TDD 与生产交付已完成，Hub reconciliation 尚未执行。
- [Architecture understanding provenance](../architecture-understanding/index.md)
- [Agent Tool common patterns](../common-patterns/agent-tools.md)：已确认的 task-level 模式；后续按验证与 owner 进行
  durable promotion，当前不直接改 shared Hub。D-597 补充各查询的长输出分页，以及独立批次的成果/完成度分离；
  通用原则候选归共享技术设计指南，CLI 的 cursor、退出码与文件表示留在 CLI/Core 各自的接口文档。
- [校验边界指南](../common-patterns/validation-boundaries.md)：D-590/D-598 的 task-level 指南，包含可信 Core REST
  返回的消费边界；待 CLI 实现验证后归入
  共享技术设计指导，具体配置实现留在 Spoke，不在此复制另一份规则。
  D-602/D-603 的 Pydantic 使用指南属于 Python 后端工程指导，不进入 PRD 或语言无关的 Hub 合同；
  随实现落入 Spoke 的 Python 后端指导，并在 python-backend-code skill 的 validation 指导中引用/应用。
  内容应具体说明 Form 已校验后的 typed 传递、PATCH 合并后单次校验、GET 不额外重验、复杂模型恢复的允许
  边界与 model_construct 的局限，不只提升为抽象的“使用成熟库”原则。
  从“所有读回只转换、零校验”修正为“无类型恢复需求时不重验；需要时接受一次成熟库构造的附带约束”，
  保持写入 owner、CLI 可信响应和使用时能力判断不变。不因此建立新的文档权威或把整份 skill 提升为 Hub truth。
  CLI 实施后：Spoke `business-pipeline-and-authority.md`、`rest-interface.md` 与 `app/schemas/AGENTS.md`
  已落地/引用该边界；CLI 开发文档明确可信 REST 返回只转换。Hub 的跨语言边界和 Job 停止合同候选位于
  `../.worktrees/cli-sink-docs`，已提交为 `f84d9ed` 并创建 Hub PR #25，尚未合并；不提前改 Spoke shared ref。
  原有未跟踪 skill 保持独立。

## Control

- **Mode**: Memos/RSS/Mail and semantic/feature/graph retrieval shared promotion has been published or consumed through
  owner-separated Hub/Spoke batches。Mail PRD/Product-TDD truth is Hub `067c60a`；
  core-py `8e07da8` and client-web `056c265` consume that exact published head through pure shared-ref commits。The Mail
  implementation/local-doc owners remain separately committed as core-py `d3cded7` and client-web `1e69938`。
- **Apply gate**: unresolved discussion pressure remains here；stable design + verified implementation triggers
  durable projection during unit completion。Commit、push、Hub publication、shared-ref bump 与 production mutation
  remain separately authorized operations。
- **Owner rule**: Hub source、Spoke shared-ref、core-py Unit TDD 与 client-web docs 分属不同
  owner/operation，不混入一个 commit，也不在 `docs/_shared/**` 直接编辑。
- **Organization**：D-562 关闭的是已生产交付的 unit，不隐含完成 Hub promotion；具体差异与边界由上述独立条目
  保留。Parent 的 durable-truth 完成条件仍未因此关闭，但不把本项默认为每个下一 unit 的前置任务。

## Promotion Test

候选内容必须同时满足：

1. 已从讨论假设升级为获批、稳定且可复用的产品或技术合同；
2. 有一手产品事实、当前实现证据或 acceptance fixture 支撑；
3. 唯一 owner 已确定，不复制同一事实；
4. 不把某个 Spoke 的偶然类名或临时 workaround 升级为共享合同；
5. 与已有 durable claim 冲突时明确写出 `From → To`，不静默叠加。

## Architecture Understanding Log

Detailed architecture-understanding provenance has moved to [architecture-understanding/index.md](../architecture-understanding/index.md).

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
8. **Info-base retrieval projected and verified** — semantic、feature/lexical and graph-navigation retrieval have each closed
   through their unit packets, implementation evidence, preview/production acceptance and owner-separated durable projection。
