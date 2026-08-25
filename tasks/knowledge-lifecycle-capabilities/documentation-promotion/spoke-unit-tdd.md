# Spoke Unit TDD Promotion Applied

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

