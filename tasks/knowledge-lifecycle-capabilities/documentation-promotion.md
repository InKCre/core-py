# Durable Documentation Promotion Plan

## Control

- **Mode**: accumulate only；本文件记录候选更新，不修改 Hub、`docs/_shared`、Spoke-local docs
  或其他仓库。
- **Apply gate**: 相关 unit contract 获批并形成内聚 batch 后，先做 Impact Handshake；只有 Sir
  明确“开始”才执行。
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

以下是这轮讨论已证明需要审查的纠错方向；Hub 原文仍要在 promotion preflight 精确定位：

| Existing pressure | Intended correction |
| --- | --- |
| collection 被描述为产生 blocks/relations，同时 organization 又像是把 collected information 转成 blocks/relations | collection 为了持久化 source information 可以拆成 graph；organization 打理**已经存在**的 info-base，以改善 use |
| collection / organization / use 容易被读成信息状态或固定 lifecycle | 三者是对信息执行的能力动作，不新增未经需求证明的 lifecycle |
| breakdown/merge/linking 容易被当成 organization 的完备枚举 | 它们只是已知能力，目标始终是为 use 优化 info-base |
| indexing 容易被归入 organization | indexing 只作为 application/retrieval 支撑 |
| source-native objects 可能被误解成 graph 之外的持久模型 | Tweet/GithubRepo/FeedItem 等通过 blocks/relations 持久化；不建立通用 collected god object |

## Candidate Hub PRD Batch

### Program-level product truth ready for later review

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

### Memos extension and backend MVP truth ready for later review

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
- organization 和三类 retrieval 的完整可观察行为与质量门槛。

## Candidate Hub Product TDD Batch

### Cross-unit contracts ready for later review

- block 是基本持久信息单元；resolver 联合 raw content 与 local relations 得到 solved/use-facing
  interpretation，storage 只负责取得 raw content。
- source-specific input 通过 extension mapping 持久化为 block/relation graph；`SubGraphForm`
  是 write form，不是完整信息模型。
- memo root content 直接保存 memo-family `CanonicalMemo`；attachments、parent、references 只由
  graph components/relations 表达，backend read 只消费 resolver solved result。
- attachment relation 默认无序；正文内显式 attachment reference 是位置 authority。Memos 0.29.1
  是已证明的 source-defined order exception，应在现有 relation payload 中保留，不推动通用
  relation schema 变化。
- comment 复用 memo root mapping，并通过 parent relation 连接。
- product API generation 与 canonical content generation 是正交版本轴；CanonicalMemo decoder
  由 versioned resolver identity 选择，不在 payload/BlockModel 重复 schema version。
- info-base local memo identity 是 `block.id`；不建立 generic `resource`、`source_key` 或 source
  binding table。
- future collector 采用 best-effort exact reconciliation；匹配不足宁可产生可整理 duplicate，
  不得 content/time fuzzy overwrite。
- D-039 已关闭 deployment-scoped Memos PAT：ordinary raw extension-config lifecycle、generic validated
  update ordering、exact public profile/v0-status-404 与 immediate replace/revoke。
- D-041/D-042/D-043/D-044 已关闭 partial-graph boundary、CanonicalMemo v1、PostgreSQL binary storage
  与 Memos relation grammar；D-045 要求单独修复 client-web config path；D-046/D-047/D-048 关闭
  owned cleanup、exact fixtures 与 family/product/access-mode extensibility seams。

### Remaining implementation truths before promotion

- versioned resolver generations 的 registry retention、unknown resolver failure 与
  core-py/client-web parity must be proven by implementation/tests before durable promotion。
- D-047 exact fixtures and D-046 deletion behavior are approved task truth but still need executable
  evidence。
- implementation-plan preflight 证明 existing `/{extension_id}` route 可由 MoeMemos pathful base URL
  直接复用；不足的是 route-auth wiring、hot lifecycle correctness、mutable graph commands 与
  read-only storage。当前证据不支持 top-level mount 或通用 extension/resolver registry redesign。

### Deferred technical scope

- collector scan/webhook/export、cursor、external identity 与 reconciliation。
- flomo/其他 memo product adapters 及其 fidelity contract。
- feature/semantic/graph navigation、index/projection invalidation 与 retrieval UI。

## Candidate Spoke Unit TDD Batch

等 Memos Technical/Acceptance gates 获批后，core-py local Unit TDD 只记录本仓内部实现
architecture，例如：

- memo extension package、route/service/resolver/storage/transaction boundaries；
- graph mutation 与 solved result 的 internal contracts；
- auth/config 的 local wiring；
- Memos extension 的 0.29.1 backend adapter 对 missing `updateMask` 的 raw-JSON key-presence
  inference 与 negative
  cases；
- tests、migrations 与 failure/residue handling 的实现真相。

当前代码观察只作为 preflight evidence，不直接 promotion：一个 block 只有一个 content/storage
pointer；`RelationManager.fetchsert` 当前按 `(from_, to_, content)` 匹配；relation content 还被
query、embedding、LLM prompt 与 client-web 直接消费；部分 convenience write paths 会独立
commit。若 intended design 改变它们，代码、tests 和 Unit TDD 必须同步形成唯一 authority。

## Architecture Understanding Log

这些发现值得保留，但只有通过 Promotion Test 才进入 durable docs：

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

## Apply Checklist

1. 冻结本 batch 的 confirmed decisions、open exclusions 与 acceptance evidence。
2. 对每个 durable owner 准备 Address/Object、`From → To`、blast radius、invariants、
   verification 与 uncertainty。
3. 在 Hub source repo 修改共享 PRD/Product TDD，不编辑本仓 `docs/_shared`。
4. Hub source 独立验证后，再按 shared-doc workflow 更新 Spoke ref。
5. core-py/client-web local docs 各自在自己的 repo/commit 处理。
6. 验证没有重复 authority、broken links 或把未获批 unit 草案投影成 durable truth。
