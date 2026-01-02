## business/ - Business Logic Layer

业务逻辑层，按业务领域划分模块。每个模块通常包含 Manager 类，提供该领域的核心功能。

### 领域架构

```
┌─────────────────────────────────────────────┐
│              Extension Layer                │
│  (增强 source/info-base/sink 能力)           │
└─────────────────────────────────────────────┘
          ↓                    ↑
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│   Source     │ →  │    Info-Base     │ →  │     Sink     │
│  (数据输入)   │    │  (核心信息管理)   │    │  (数据输出)   │
└──────────────┘    └──────────────────┘    └──────────────┘
                            ↓
                    ┌──────────────┐
                    │    Client    │
                    │  (客户端管理)  │
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
| `SourceManager` | Source 类型注册、采集任务管理 | [source/main.py](source/main.py) |
| `SourceCollectJobManager` | 采集任务执行调度 | [source/collect_job.py](source/collect_job.py) |
| `SinkManager` | RAG 等信息检索输出 | [sink/main.py](sink/main.py) |
| `EmbeddingManager` | Embedding 生成和检索 | [sink/embedding.py](sink/embedding.py) |
| `ExtensionManager` | Extension 生命周期管理 | [extension/main.py](extension/main.py) |
| `ClientManager` | 客户端注册和管理 | [client/main.py](client/main.py) |

### 模块依赖

- `info_base/` 是核心，被 `source/` 和 `sink/` 依赖
- `extension/` 通过插件机制扩展其他模块能力
- `client/` 管理分布式客户端信息

### 编码指引

- 新增业务逻辑：在对应领域的 `main.py` 或新建文件中添加
- Manager 类方法通常为 `@classmethod`，支持依赖注入
- 数据库操作：接受 `db_session` 参数或使用 `SessionLocal()`
- 读取各子目录的 AGENTS.md 了解具体领域的细节
