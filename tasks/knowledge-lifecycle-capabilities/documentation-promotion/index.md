# Durable Documentation Promotion Plan

## Navigation

- [Known corrections](known-corrections.md)
- [Candidate Hub PRD batch](hub-prd.md)
- [Candidate Hub Product TDD batch](hub-product-tdd.md)
- [Spoke Unit TDD promotion](spoke-unit-tdd.md)
- [Architecture understanding provenance](../architecture-understanding/index.md)

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
