## client/ - Client Management (客户端管理)

客户端注册和管理模块，支持分布式部署场景下的客户端发现和通信。

### 核心概念

- **Client**: InKCre 实例（单机/分布式部署中的一个节点）
- **Client ID**: UUID v4 唯一标识（来自 `settings.client_id`）
- **REST API URL**: 客户端对外可访问的 API 地址（可选）

### 模块结构

```
client/
└── main.py              # ClientManager - 客户端注册和查询
```

### 核心功能

**自注册** (`ClientManager.register_self()`):
- 应用启动时自动调用（见 [run.py](../../../run.py)）
- 使用 PostgreSQL `ON CONFLICT DO UPDATE` 实现 upsert
- 更新客户端名称和 REST API URL

**查询**:
- `get(client_id)`: 获取指定客户端
- `get_all()`: 获取所有注册客户端
- `get_current_client_id()`: 获取当前客户端 ID

### 配置项

在 [app/settings.py](../../settings.py) 中配置：
- `client_id`: 客户端唯一 ID（默认自动生成 UUID v4）
- `client_name`: 客户端名称（默认 "core-py"）
- `client_base_url`: REST API 访问地址（可选，不可访问时为 None）

### 数据模型

见 [app/schemas/client/](../../schemas/client/) 目录：
- `ClientModel` - Client 表模型
- 字段：`id`, `name`, `rest_api_url`, `created_at`, `updated_at`

### 使用场景

- **分布式部署**: 多个 InKCre 实例共享同一数据库
- **客户端间通信**: 通过 `rest_api_url` 发现和调用其他实例的 API
- **Extension 关联**: Extension 可关联到特定客户端（见 [schemas/extension/](../../schemas/extension/)）

### 编码指引

- 客户端配置通过环境变量管理（`.env` 文件）
- 新增客户端信息：扩展 `ClientModel` 和 `register_self()` 方法
- 客户端间通信：通过 `rest_api_url` + HTTP 客户端实现
