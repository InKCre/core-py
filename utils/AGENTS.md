## utils/ - Utility Functions (工具函数)

通用工具函数库，提供跨模块使用的辅助功能。

### 模块结构

```
utils/
├── datetime_.py         # 日期时间工具
├── sql.py              # SQL/数据库工具
├── types_.py           # 类型定义和工具
└── base.py             # 基础工具函数
```

### datetime_.py - 日期时间工具

**核心函数**:
- `get_datetimez()`: 获取带时区的 datetime（推荐）
  - 支持 RFC3339、ISO8601、timestamp 输入
  - 默认东八区（UTC+8）
  
- `get_datetime()`: 获取不带时区的 datetime（不推荐）
- `get_timezone(delta)`: 获取时区对象
- `to_timestamp()`: datetime 转时间戳
- `format_datetime()`: 格式化日期时间

**使用示例**:
```python
from utils.datetime_ import get_datetimez

# 当前时间（东八区）
now = get_datetimez()

# 从 RFC3339 字符串
dt = get_datetimez(rfc3339="2024-11-10T12:00:00+08:00")

# 从时间戳
dt = get_datetimez(timestamp=1699603200.0)
```

### sql.py - SQL/数据库工具

SQL 查询构建和数据库操作辅助函数：
- `build_where_clause()`: 构建 WHERE 条件
- `paginate()`: 分页查询
- 其他 SQLModel/SQLAlchemy 辅助函数

### types_.py - 类型定义

项目通用类型定义：
- Type aliases
- Custom types
- Type guards

### base.py - 基础工具

其他通用工具函数：
- 字符串处理
- 数据结构转换
- 等等

### 导出管理

常用工具在 `__init__.py` 中导出：
```python
from utils import get_datetimez, build_where_clause
```

### 编码指引

- **新增工具函数**：根据功能放入对应文件（datetime/sql/types/base）
- **命名约定**：使用 snake_case，描述性命名
- **文档**：为每个函数添加 docstring（参数、返回值、示例）
- **导出**：常用函数在 `__init__.py` 中导出便于使用
- **避免循环依赖**：utils 不应导入 app/ 或 business/ 模块

### 依赖关系

```
utils/  →  (被其他所有模块使用)
  ↑ 不依赖任何业务模块
```

工具函数应保持纯粹和可复用，不包含业务逻辑。
