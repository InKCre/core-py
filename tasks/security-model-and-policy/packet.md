# Security Model And Policy

- **Objective**: 为 InKCre 建立能改善漏洞报告与安全判断质量的文档/执行表面；既让真实风险更容易被
  发现、报告和修复，也通过明确 threat model、trust boundaries 与 proportionality 避免无依据的
  security over-design。
- **Guardrails**:
  - 不把 `SECURITY.md` 默认建成所有安全事实的总 owner；能由代码、配置、测试、CI 或部署合同执行的
    事实仍由其原 owner 承载。
  - 区分 GitHub community security policy（外部报告/披露）与 Chrome-style security model
    （开发者/审计 agent 的边界与判定依据），在证据支持前不假定它们必须放在同一文件。
  - 安全要求必须能够回溯到 actor、asset、capability、trust boundary、harm 与 deployment assumption；
    不以“secret 不得持久化”“认证越多越好”等脱离场景的口号替代风险判断。
  - 不虚构 supported versions、报告邮箱、响应 SLA、奖励计划或 GitHub 私密报告能力。
  - 本 unit 先讨论与审查；除 task packet 外，任何 durable doc、代码、仓库设置或自动化修改都需要
    单独批准。
- **Verification**:
  - 每项被纳入的安全 claim 都有明确受众、owner、适用范围、失效条件与可复核依据。
  - 外部报告者可以找到真实可用的私密报告路径；maintainer/agent 可以据此区分 vulnerability、普通
    bug、hardening opportunity 与 accepted risk。
  - 至少用 PAT persistence/auth boundary 等已有案例反向演练，证明文档减少误判而不是只增加限制。
  - 与现有 JWT/database/runtime/extension 合同不冲突；可执行控制仍优先落在 code/test/CI/config。
- **Current Truth**:
  - `InKCre/core-py` 是 GitHub public repository；当前无 release tags，repository private vulnerability
    reporting 为 disabled，community profile 没有 security policy。
  - 仓库已有 dependency review，拒绝新引入的 high-severity development/runtime vulnerabilities；已有
    JWT、PostgreSQL roles/ACL、credential/runtime ownership 与 extension auth 的代码和部署合同，但没有
    统一 threat model、vulnerability intake policy 或 `SECURITY.md`。
  - GitHub 将根级 `SECURITY.md` 定位为 supported versions + vulnerability reporting instructions；
    repository security advisories/private reporting 是后续私下协作与披露机制。
  - Chromium 2026 的增量用法是在组件目录放置 `SECURITY.md`，向人和 agent 描述 security goals、
    attacker assumptions、trust boundaries、valid harms 与 non-bugs，以减少 AI security audit false
    positives；其全局 agent guide 明确不等同于 VRP/reporting policy。
  - Sir 已确认采用“一份安全模型、两类入口”：root `SECURITY.md` 是外部 policy/router；local Unit TDD
    security model 是 core-py 的 actor/asset/boundary/harm/proportionality owner。Scoped `SECURITY.md` 只在
    component 有实质不同 security boundary 时增加。
  - `SECURITY.md`、`docs/30-unit-tdd/security-model.md` 与 README/CONTRIBUTING/docs/AGENTS navigation
    已落地；GitHub private vulnerability reporting 已启用并由 API 读回 `enabled=true`。
  - PAT persistence worked check 已证明模型会区分 persistence 与 boundary violation，并明确列出会让
    结论失效的新 actors/boundaries。
- **Next Step**: Sir 复审当前结果；之后决定是否把 shared product security assumptions 提升到 Hub，及
  是否让其它 InKCre repositories 分别增加自己的 reporting policy / repo-specific security model。

## Confirmed Structure

- **S-001 — One model, two entry surfaces**: root policy 服务 reporter；local security model 服务
  maintainer/agent。两者相互链接但不复制 owner facts。
- **S-002 — Honest reporting contract**: pre-1.0、无 supported release tags；只说明 current `main` / canonical
  deployment 的处理方向，不承诺 backport、SLA、bounty 或 CVE。
- **S-003 — Real private channel**: 使用 GitHub private vulnerability reporting；其它 InKCre repo 无私密
  channel 时允许以本 repo form 作为安全 fallback，但报告必须标明实际 affected repository。
- **S-004 — Local security owner**: core-py security model 位于 local Unit TDD；code/test/CI/deployment docs
  继续拥有执行事实。Shared Hub 只在跨 repo assumptions 稳定后接收 promotion。
- **S-005 — Scoped files are earned**: 不预先在 `app/`、`extensions/` 等目录铺设 `SECURITY.md`；只有局部
  attacker model/trust boundary 明显不同且根模型无法简洁表达时才创建。

## Implementation Evidence

- Added: `SECURITY.md`、`docs/30-unit-tdd/security-model.md`。
- Navigation updated: `README.md`、`CONTRIBUTING.md`、`docs/index.md`、root `AGENTS.md`。
- GitHub repository state: private vulnerability reporting `false -> true`，read-back verified。
- Repository validation: full `pdm run check` passed：migration checks `22 + 22`、Ruff lint/format、Pyrefly
  `0 diagnostics`、`258 passed, 6 skipped`；`git diff --check` passed；all relative owner links were resolved
  against existing files。
- Full gate initially exposed that the already-authorized Memos commit had passed Ruff lint but not repository
  format-check；20 exact Memos/graph files were mechanically formatted and amended into the same authorized commit
  (`304a5c8`) before final verification。No security documents entered that commit。
- Reverse case: Memos PAT persistence classified as acceptable under current single-owner/database trust boundary；
  config authorization、comparison、revocation 和 non-disclosure remain real controls；untrusted DB readers、
  independent backups、multi-user/delegated admin/compliance would reopen the result。

## Shared-Doc Pressure

- Browser/native safe rendering、cross-repo content-to-command boundaries、organization-level reporting fallback
  和 product-wide privacy/provider assumptions 可能形成 Hub Product TDD security model，但 core-py 的当前
 证据不足以替整个产品冻结它们。本 unit 不修改 `docs/_shared`。

## Evidence Horizon

- GitHub repository/community/profile 与 private-vulnerability-reporting API：2026-08-01 read-only probe。
- GitHub Docs：security policy 用于 supported versions 与 vulnerability reporting；security advisories 用于
  私下协作、修复和发布 disclosure。
- Google Security Blog, 2026-07-30；Chromium `Security for Agents` 与 AI-generated security bugs FAQ：
  component `SECURITY.md` 用于帮助 agent 理解 threat model/security boundaries 并过滤 invalid reports。
- Local repository：root/docs/CI/auth/database/runtime/extension surfaces 的 read-only audit。

## SVC Note

Installed SVC/corpus 是 `11.0.1`，repository adopted version 是 `10.0.1`，status 为 `adoption-pending`；
本 unit 不执行 `svc adopt`。Task packet 只使用当前 root-owned minimum control surface，不把新的 SVC corpus
内容复制为项目 truth。
