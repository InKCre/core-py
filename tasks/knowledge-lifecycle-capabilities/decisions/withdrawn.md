# Withdrawn Frames

> [Decision register index](index.md)


- 以 `observation`、audit、replay 或“图准入”组织任务。
- O-017 top-level protocol mount：MoeMemos 2.0.4 的 Retrofit endpoints 是 relative paths，登录
  host 保留 path，attachment URL 也在 host path 后追加 `file/...`；配置
  `https://<deployment>/memos/` 即可复用现有 `/{extension_id}` routes。原先“必须占用根级
  `/api/v1`/`/file`”的前提不成立。
- 把 collection / organization / use 建模成信息生命周期。
- 把 block / relation / resolver / storage 联合模型升级为独立前置主线。
- 为了讨论依赖而将 application 移到 organization 之前。
- 把 `SubGraphForm` 当作完整产品模型或 collection 产品产物。
- 把 CanonicalMemo 仅建模为 transient normalized / solved model，而不持久化到 block
  content。
- 为 source-native identity 建立通用 `resource`、opaque `source_key` 或
  `source_block_bindings` 持久模型。
- 把公开 IMAP/POP3 protocol 建模为 versioned InKCre adapter ID，并为一个当前 closed、one-implementation-
  per-protocol 的集合引入 `MailManager`、runtime adapter registry 或 persisted adapter catalog。Protocol 是
  Source 配置的外部标准事实；adapter 是代码实现机制。
- 在 `MailAdapter` 上暴露 `collect()` / `MailCollectRequest` / `MailCollectBatch`。`collect` 是 Source 将外部信息
  带入 InfoBase 的领域 command；Adapter 只暴露 canonical Mail 级别的远端读取/变更流与 part fetch。
- 为防御 Storage catalog 与实现类不一致而增加 `StorageManager.get_writable_storage()`。该一致性属于 Storage
  registry/bootstrap 系统边界；每次使用时重新发现同一能力既没有独立领域语义，也会泄漏 registry 复杂度。
- 将“先读 durable completion fact 再重建生产路径”（原候选 U-043）、“共享 matching mechanics 而 evidence
  precedence 归领域 owner”（原候选 U-045）以及“semantic completion 不由底层副作用拥有”（原候选 U-046）提升为
  project-wide common patterns。它们在 Mail MIME materialization 内仍是有效设计解释，但 D-292 复审认为其跨单元
  决策杠杆不足，不值得增加 durable vocabulary。
