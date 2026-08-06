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
