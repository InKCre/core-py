## business/ - Business Logic Layer

业务逻辑层，按业务领域划分模块。每个模块通常包含 Manager 类，提供该领域的核心功能。

如果改动跨 `extension/source/info_base/application` 多个子树，先读 [docs/30-unit-tdd/business-pipeline-and-authority.md](../../docs/30-unit-tdd/business-pipeline-and-authority.md)；局部 tripwire 再回到各自目录的 `AGENTS.md`。

### 领域架构

```
┌─────────────────────────────────────────────┐
│              Extension Layer                │
│  (增强 source/info-base/application 能力)    │
└─────────────────────────────────────────────┘
          ↓                    ↑
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│   Source     │ →  │    Info-Base     │ →  │ Application  │
│  (数据输入)   │    │  (核心信息管理)   │    │  (使用能力)   │
└──────────────┘    └──────────────────┘    └──────────────┘
                            ↕
                    ┌──────────────┐
                    │     Peer     │
                    │ (能力发现/委派) │
                    └──────────────┘
```

### 核心 Manager 类

| Manager | 职责 | 位置 |
|---------|------|------|
| `InfoBaseManager` | 子图插入、Block/Relation 协调 | [info_base/main.py](info_base/main.py) |
| `BlockManager` | Block CRUD、内容解析 | [info_base/block.py](info_base/block.py) |
| `RelationManager` | Relation CRUD | [info_base/relation.py](info_base/relation.py) |
| `StorageManager` | Block 内容存储后端 | [info_base/storage/main.py](info_base/storage/main.py) |
| `ResolverManager` | Block 内容解析器注册 | [info_base/resolver/main.py](info_base/resolver/main.py) |
| `SourceManager` | Source 类型注册、实例状态与 lazy graph anchor | [source/main.py](source/main.py) |
| `JobManager` | global typed Job registry、claim、execution 与 closure | [job.py](job.py) |
| `CronManager` | database-owned Cron occurrence materialization | [cron.py](cron.py) |
| `AIManager` | AI dialect catalog、Provider/Model routing、typed embedding/chat execution | [ai/main.py](ai/main.py) |
| `AgentManager` | Persisted Agent definition、typed Tool binding、Thread/Turn execution | [agent/main.py](agent/main.py) |
| `SemanticRetrievalManager` | Semantic projection、EmbeddingRecord maintenance、exact ranking | [semantic_retrieval/main.py](semantic_retrieval/main.py) |
| `LexicalRetrievalManager` | Block-local lexical projection、derived-record maintenance、exact feature ranking | [lexical_retrieval/main.py](lexical_retrieval/main.py) |
| `OrganizationManager` | Explicit focal-Block rumination、Agent composition、graph-aware Tools | [organization.py](organization.py) |
| `ExtensionManager` | Extension 生命周期管理 | [extension/main.py](extension/main.py) |
| `PeerManager` | Peer identity、capability/lease discovery、delegation | [peer/main.py](peer/main.py) |

### 模块依赖

- `info_base/` 是核心，被 `source/` 和 application/use capability 依赖
- `ai/` 是 graph-blind execution module；不得 import Block/Relation/Resolver
- `agent/` composes AI chat with caller-owned typed Tools；不得拥有 organization/Resolver/graph policy
- `semantic_retrieval/` 是 use owner；只通过 Resolver/RelationManager projection 消费 graph，并把 typed vectors 交给 AIManager
- `lexical_retrieval/` 是 use owner；只通过 Resolver 的 Block-local lexical projection 消费 graph，独占 lexical records
- `organization.py` 组合 focal graph context 与 caller-owned Agent Tools；仅 `submit_graph` 可写 graph，不建立 approach registry/job
- `extension/` 通过插件机制扩展其他模块能力
- `peer/` 管理 equal Peer facts and heterogeneous runtime delegation；不理解 business capability payload

### 编码指引

- 新增业务逻辑：在对应领域的 `main.py` 或新建文件中添加
- Manager 类方法通常为 `@classmethod`，支持依赖注入
- 数据库操作：接受 `db_session` 参数或使用 `SessionLocal()`
- 读取各子目录的 AGENTS.md 了解具体领域的细节
