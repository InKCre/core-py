# Known Corrections to Existing Hub Truth

以下纠错已在 Hub source worktree 中按 owner 应用；本表保留 From → To 的 promotion provenance：

| Existing pressure | Intended correction |
| --- | --- |
| collection 被描述为产生 blocks/relations，同时 organization 又像是把 collected information 转成 blocks/relations | collection 为了持久化 source information 可以拆成 graph；organization 打理**已经存在**的 info-base，以改善 use |
| collection / organization / use 容易被读成信息状态或固定 lifecycle | 三者是对信息执行的能力动作，不新增未经需求证明的 lifecycle |
| breakdown/merge/linking 容易被当成 organization 的完备枚举 | 它们只是已知能力，目标始终是为 use 优化 info-base |
| indexing 容易被归入 organization | indexing 只作为 application/retrieval 支撑 |
| source-native objects 可能被误解成 graph 之外的持久模型 | Tweet/GithubRepo/FeedItem 等通过 blocks/relations 持久化；不建立通用 collected god object |
| resolver 的 `v1` / `v2` 轴被叫作 `generation` | 按开发者惯例叫 `resolver contract version`；这是一致性/自解释修正，不是声称 `generation` 在其他上下文均错误 |
| graph 中的 source/protocol object 被叫作 `wrapper` | 它是普通 block；在拥有与关联 semantic content 有关的 protocol/source-authored facts 时按职责叫 `metadata block`，不新增 wrapper type |

