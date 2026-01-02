## sink/ - Information Output (数据输出)

信息使用和输出模块，提供 RAG、搜索等功能，将 info-base 的信息以各种方式提供给用户。

### 核心概念

- **Sink**: 信息输出接口（当前主要是 RAG）
- **Embedding**: Block/Relation 的向量表示，用于语义检索
- **RAG**: Retrieval-Augmented Generation（检索增强生成）
- **Retrieve Modes**: embedding（向量检索）、reasoning（LLM 推理）、feature（特征检索）

### 模块结构

```
sink/
├── main.py              # SinkManager - RAG 入口
└── embedding.py         # EmbeddingManager - Embedding 生成和检索
```

### 核心流程

**RAG 流程** (`SinkManager.rag`):
1. **Retrieve**: 根据 query 检索相关 Block
   - `embedding` 模式：向量相似度搜索（默认）
   - `reasoning` 模式：LLM 推理查询
   - `feature` 模式：特征匹配（待实现）
2. **Rerank** (可选): 使用 reranker 重排检索结果
3. **Generate**: 使用 LLM 基于检索内容生成回答

**Embedding 生成** (自动周期执行):
- Scheduler 每 60s 调用 `check_and_create_missing_embeddings()`
- 为没有 embedding 的 Block/Relation 自动生成
- 使用 `text-embedding-v3` 模型（见 [libs/ai.py](../../../libs/ai.py)）

### API 参数

`/sink/rag` 端点参数:
- `query`: 用户查询
- `context`: 额外上下文字符串
- `context_blocks`: 额外上下文 Block ID 列表
- `retrieve_mode`: 检索模式（embedding/reasoning/feature）
- `use_reranker`: 是否使用 reranker
- `num_retrieve`: 初始检索数量（默认 20）
- `num_rerank`: Rerank 后保留数量（默认 5）

### 数据模型

见 [app/schemas/sink/](../../schemas/sink/) 目录：
- `BlockEmbeddingModel` - Block embedding 表模型
- `RelationEmbeddingModel` - Relation embedding 表模型

### 编码指引

- **新增检索模式**：在 `SinkManager.rag()` 中添加 `elif` 分支
- **新增 Sink 类型**：创建新的 Manager 类，注册路由
- **Embedding 更新**：Block 内容变化时调用 `EmbeddingManager.upsert_block_embedding()`
- **向量搜索**：使用 `EmbeddingManager.retrieve_blocks()` 进行语义检索
