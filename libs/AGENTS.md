## libs/ - Shared Libraries (共享库)

项目内部共享库，提供可复用的基础功能模块。

### 模块结构

```
libs/
└── obsrv/               # 可观测性（日志、监控）
    ├── main.py          # 日志系统入口
    ├── setting.py       # 可观测性配置
    ├── log_record.py    # 日志记录和上下文
    ├── log_handler_logtail.py   # Logtail 日志处理器
    └── log_handler_postgresql.py  # PostgreSQL 日志处理器
```

### obsrv/ - 可观测性模块

**日志系统**:
- 统一日志接口，支持多后端（控制台、Logtail、PostgreSQL）
- Trace ID 追踪（通过 contextvars）
- 结构化日志记录

**核心函数**:
- `setup_obsrv()`: 初始化日志系统（在 [run.py](../run.py) 调用）
- `get_logger()`: 获取 logger 实例

**配置** (在 [app/settings.py](../app/settings.py)):
```python
obsrv:
  log:
    console: bool          # 控制台输出
    backend: bool          # 后端存储（PostgreSQL/Logtail）
    backend_type: str      # "postgresql" 或 "logtail"
    backend_token: str     # Logtail token（如果使用）
```

### 编码指引

**使用日志**:
```python
from libs.obsrv.main import get_logger

logger = get_logger()
logger.info("message", extra={"key": "value"})
```

- 日志模块依赖：logtail-python (可选)

AI 不属于 `libs/`：canonical contracts 位于 `app/schemas/ai/`，共享 facts 和 peer-local execution 位于
`app/business/ai/`。不要重新引入 process-global client 或 environment-owned model/provider authority。
