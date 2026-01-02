## app/ - Application Core

应用程序核心层，包含 FastAPI 应用的基础设施和业务逻辑。

### 核心模块

- **settings.py**: 集中式配置管理 (pydantic-settings)
  - 数据库连接、JWT、LLM API 配置
  - 环境变量自动加载和验证
  - `get_settings()` 用作 FastAPI 依赖注入
  
- **engine.py**: 数据库引擎和会话管理
  - `SQLDB_ENGINE`: SQLModel 引擎实例
  - `get_db_session()`: 会话生命周期管理（FastAPI 依赖）
  
- **scheduler.py**: 后台任务调度
  - `scheduler`: AsyncIOScheduler 实例
  - 用于 source 采集、embedding 生成等周期任务
  
- **middleware.py**: 中间件
  - `LoggingMiddleware`: 请求日志和 trace_id 追踪
  - `JWTMiddleware`: JWT 认证
  - CORS 配置在 [run.py](../run.py) 中

### 目录结构

- **business/**: 业务逻辑层（按领域划分）
- **routes/**: FastAPI 路由注册（对外 API）
- **schemas/**: 数据模型和表定义（SQLModel）

### 依赖关系

```
run.py → routes/ → business/ → schemas/
         ↓
      engine.py ← settings.py
```

### 编码指引

- 新增配置项：在 `settings.py` 的 `Settings` 类中添加
- 数据库访问：使用 `get_db_session()` 或 `SessionLocal()`
- 后台任务：使用 `scheduler.add_job()` 注册
- 中间件：在 [run.py](../run.py) 中通过 `app.add_middleware()` 注册
