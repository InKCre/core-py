## libs/ - Shared Libraries (共享库)

项目内部共享库，提供可复用的基础功能模块。

### 模块结构

```
libs/
├── ai.py                # AI/LLM 相关功能（Embedding, Chat）
└── obsrv/               # 可观测性（日志、监控）
    ├── main.py          # 日志系统入口
    ├── setting.py       # 可观测性配置
    ├── log_record.py    # 日志记录和上下文
    ├── log_handler_logtail.py   # Logtail 日志处理器
    └── log_handler_postgresql.py  # PostgreSQL 日志处理器
```

### ai.py - AI/LLM 模块

**核心类**:
- `Embedding`: 向量嵌入生成（使用 OpenAI API）
  - `embed(text: str) -> Vector`: 生成文本嵌入
  - 支持模型：`text-embedding-v3`, `text-embedding-ada-002`
  
- `Chat`: LLM 对话管理
  - `one_chat()`: 单轮对话
  - `multi_chat()`: 多轮对话
  
- `Message`: 消息封装（user/assistant/system/tool）
- `Prompt`: 从文件加载 prompt 模板（`data/ai/prompts/`）
- `MessageContent`: 消息内容基类

**配置**:
- `llm_sp_ak`: LLM API Key（环境变量）
- `llm_sp_base_url`: LLM API Base URL（环境变量）
- 使用 OpenAI SDK，兼容 OpenAI-compatible API

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

**使用 AI 模块**:
```python
from libs.ai import Embedding, Chat, Message

# 生成 embedding
embedding = Embedding("", "text-embedding-v3").embed("hello")

# LLM 对话
response = await Chat(messages=[
    Message(role="user", content="hello")
]).complete()
```

**使用日志**:
```python
from libs.obsrv.main import get_logger

logger = get_logger()
logger.info("message", extra={"key": "value"})
```

- AI 模块依赖：OpenAI SDK
- 日志模块依赖：logtail-python (可选)
- 所有 LLM 调用应处理 API 错误和超时
