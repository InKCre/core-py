# sink/ Local Guide

本文件只描述 `app/business/sink/` 的局部事实、职责边界和变更风险。跨 `extension/source/info_base/sink` 的慢变量结构，先读 [docs/30-unit-tdd/business-pipeline-and-authority.md](../../../docs/30-unit-tdd/business-pipeline-and-authority.md)。

## 何时阅读

在以下情况进入本目录前先读这里：

- 修改 `SinkManager` 或 `EmbeddingManager`
- 修改 embedding 生成、补全、查询或 rerank 逻辑
- 修改 sink 与 info-base 的责任边界

## 局部执行规则

- sink 拥有 retrieval semantics 与 embedding lifecycle；不要因为 info-base 会触发 upsert，就把 embedding owner 写回 info-base。
- 若改动会影响 block 取文、resolver 文本化、embedding 生成路径，先核对 [app/business/info_base/AGENTS.md](../info_base/AGENTS.md)。
- `feature` retrieve mode 当前未实现；不要把它写成稳定可用能力。

## 关键文件

- `app/business/sink/main.py`: `SinkManager.rag()` 与 retrieve-mode 分流
- `app/business/sink/embedding.py`: embedding upsert / background maintenance / similarity query
- `app/schemas/sink/`: block / relation embedding 模型
- `app/business/info_base/block.py`: info-base 侧触发 embedding upsert 的接点

## 当前稳定事实

### Ownership Boundary

- sink 负责：
  - embedding 模型
  - embedding 生成与补全
  - retrieval / rerank 语义
  - RAG 输出组装
- info-base 可以在 block 写入时触发 `EmbeddingManager.upsert_block_embedding()`，但这不改变 owner。

### Retrieval Modes

- `reasoning`: 当前走 `BlockManager.query_by_reasoning(...)`
- `embedding`: 当前走 `EmbeddingManager.query_blocks_by_embedding(...)`，可选 rerank
- `feature`: 当前抛 `NotImplementedError`

如果要改 mode contract，先分清楚是“局部实现变化”还是“整个 unit 的检索结构变化”。

### Context Assembly

- `context_blocks` 会通过 `BlockManager.get_resolver()` 拿 resolver，再调用 `get_text()` 组装额外上下文。
- 这意味着 sink 对“如何把 block 转成可消费文本”依赖 resolver contract，而不是直接解释 block content。

### Background Embedding Maintenance

- `EmbeddingManager.check_and_create_missing_embeddings()` 会补全缺失的 block / relation embeddings。
- `EmbeddingManager.refresh_all_block_embeddings()` 是重建路径，不等于常规在线写入路径。
- 这些都是 sink 责任，即便触发点不一定都在 `sink/` 目录里。

## 局部风险

- `EmbeddingManager.query_blocks_by_embedding()` 才是当前实际查询 API；不要在文档或调用点里继续写不存在的 `retrieve_blocks()`。
- 改 embedding 生成字符串时，实际依赖的是 resolver 的 `get_str_for_embedding()`；不要在 sink 里偷偷复制 resolver 语义。
- 若改动把 retrieval 和 persistence 搅在一起，通常是设计退化，不是文档没写够。

## 编辑指引

- 改 embedding ownership 表述时，同时检查 `app/business/info_base/block.py` 与本文件是否仍一致。
- 改 retrieve mode 时，优先补 tests 或 runtime guard，而不是只补 prose。
- 若新变化跨到整个 business pipeline，再上升到 `docs/30-unit-tdd/`；局部算法或 mode 细节仍留在这里。
