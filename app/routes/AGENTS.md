## routes/ - API Routes (REST API 路由)

FastAPI 路由注册层，将业务逻辑暴露为 REST API 端点。

### 核心概念

- **Router**: FastAPI APIRouter，按领域组织路由
- **路由注册**: 在 [run.py](../../run.py) 中通过 `app.include_router()` 注册
- **依赖注入**: 使用 `get_db_session()` 获取数据库会话

### 路由模块

| 文件 | 前缀 | 业务模块 | 主要端点 |
|------|------|---------|---------|
| [block.py](block.py) | `/blocks` | BlockManager | GET, POST, PUT, DELETE |
| [relation.py](relation.py) | `/relations` | RelationManager | GET, POST, PUT, DELETE |
| [source.py](source.py) | `/sources` | SourceManager | GET, POST, PUT, DELETE |
| [extension.py](extension.py) | `/extensions` | ExtensionManager | GET, POST, PUT, DELETE, /install |

### 其他路由

定义在 [run.py](../../run.py) 中：
- `/heartbeat` - 健康检查
- `PUT /graph` - 插入子图（`InfoBaseManager.insert_subgrpah`）
- `GET /sink/rag` - RAG 端点（`SinkManager.rag`）

### 路由结构

典型 CRUD 路由：
```python
ROUTER = fastapi.APIRouter(prefix="/resources", tags=["resource"])

@ROUTER.get("/")
async def list_resources() -> list[ResourceModel]:
    return ResourceManager.list_all()

@ROUTER.post("/")
async def create_resource(data: ResourceForm) -> ResourceModel:
    return ResourceManager.create(data)

@ROUTER.get("/{resource_id}")
async def get_resource(resource_id: ResourceID) -> ResourceModel:
    return ResourceManager.get(resource_id)
```

### 编码指引

- **新增路由文件**：在此目录创建，定义 `ROUTER`，在 [run.py](../../run.py) 注册
- **数据验证**：使用 Pydantic model 作为请求/响应 schema
- **错误处理**：使用 FastAPI 的 `HTTPException` 抛出 HTTP 错误
- **认证**：JWT 认证在中间件中处理（见 [app/middleware.py](../middleware.py)）
- **避免重复逻辑**：业务逻辑在 `business/` 层，路由层只负责参数解析和调用

### 路由注册顺序

在 [run.py](../../run.py) 中的注册顺序：
1. Middleware（CORS, Logging, JWT）
2. Core routes（block, relation, source, extension, sink）
3. Extension routes（动态注册）

### API 文档

- OpenAPI 文档：启动后访问 `/docs` 或 `/redoc`
- 生成 OpenAPI JSON：运行 `python scripts/generate-openapi.py`
