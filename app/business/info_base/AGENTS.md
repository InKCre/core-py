## info_base/ - Information Base (核心信息管理)

核心信息存储和管理模块，采用图结构（Block + Relation）组织信息。

### 核心概念

- **Block**: 信息单元（文本、图片、视频等），有 ID、类型、内容
- **Relation**: Block 间的有向关系，形成信息图
- **SubGraph**: Block + 其入边/出边，用于批量插入
- **Storage**: Block 内容存储后端（DB/HTTP 等）
- **Resolver**: Block 内容解析器（根据类型解析成文本）

### 模块结构

```
info_base/
├── main.py              # InfoBaseManager - 子图插入协调
├── block.py             # BlockManager - Block CRUD 和解析
├── relation.py          # RelationManager - Relation CRUD
├── storage/
│   ├── main.py          # StorageManager - 存储后端管理
│   └── http.py          # HTTP 存储实现
└── resolver/
    ├── main.py          # ResolverManager - 解析器注册
    ├── text.py          # 文本解析器
    ├── html.py          # HTML 解析器
    ├── image.py         # 图片解析器
    └── video.py         # 视频解析器
```

### 核心流程

**插入子图** (`InfoBaseManager.insert_subgraph`):
1. fetchsert Block（存在则获取，不存在则创建）
2. 递归处理 in_arcs 和 out_arcs
3. 创建 Relation
4. 返回插入的 Block 和 Relation

**Block 内容解析** (`BlockManager.get_content_as_text`):
1. 根据 storage_type 从对应 Storage 获取内容
2. 根据 block_type 找到对应 Resolver
3. 解析成纯文本返回

### 数据模型

见 [app/schemas/info_base/](../../schemas/info_base/) 目录：
- `BlockModel` - Block 表模型
- `RelationModel` - Relation 表模型
- `SubGraphForm` - 子图插入表单

### 编码指引

- 新增 Block 类型：无需代码改动（存储在 DB enum 中）
- 新增 Resolver：继承 `ResolverBase`，注册到 `ResolverManager`
- 新增 Storage：继承 `StorageBase`，在 `StorageManager.setup_builtin_storages()` 注册
- Block 唯一性：通过 `identity` 字段保证（由 Source 或 Extension 决定）
