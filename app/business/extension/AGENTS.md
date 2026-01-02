## extension/ - Extension System (扩展系统)

扩展系统，允许插件化扩展 InKCre 的功能（Source、Resolver、API 等）。

### 核心概念

- **Extension**: 扩展包，位于 `extensions/` 目录
- **ExtensionBase**: 扩展基类，定义生命周期钩子
- **Extension Lifecycle**: start → running → close
- **Extension 能力**: 注册 Source、Resolver、API 路由等

### Extension 结构

每个扩展是一个独立的包：
```
extensions/
├── {ext_id}/
│   ├── __init__.py          # 定义 Extension 类
│   ├── pyproject.toml       # 扩展依赖（可选）
│   ├── schema.py            # 数据模型
│   ├── resolver.py          # Resolver（可选）
│   └── (source.py, sink.py) # Source/Sink（可选）
```

### Extension 定义

```python
from app.business.extension import ExtensionBase, EmptyConfig

class Extension(ExtensionBase, ext_id="my_ext", config_cls=MyConfig):
    @classmethod
    def _register_apis(cls, router: fastapi.APIRouter):
        # 注册 API 路由
        router.get("/hello")(lambda: {"msg": "hello"})
    
    @classmethod
    def _init_sources(cls):
        # 导入 Source 类（自动注册）
        from .source import MySource
    
    @classmethod
    def _init_resolvers(cls):
        # 导入 Resolver 类（自动注册）
        from .resolver import MyResolver
```

### Extension 生命周期

1. **安装**: `ExtensionManager.install()` - 从 URL/本地安装到 `extensions/`
2. **同步**: `ExtensionManager.sync()` - 扫描 `extensions/` 写入数据库
3. **启动**: `ExtensionManager.start()` - 加载并调用 `on_start()`
4. **运行**: Extension API、Source、Resolver 可用
5. **关闭**: `ExtensionManager.close()` - 调用 `on_close()`，保存配置

### 管理器方法

| 方法 | 用途 |
|------|------|
| `sync()` | 扫描 extensions/ 目录，同步到数据库 |
| `start_enabled()` | 启动所有已启用的扩展 |
| `start(extid)` | 启动指定扩展 |
| `close(extid)` | 关闭指定扩展 |
| `install()` | 从 URL/本地安装扩展 |
| `get_installed()` | 获取已安装扩展列表 |

### 数据模型

见 [app/schemas/extension/](../../schemas/extension/) 目录：
- `ExtensionModel` - Extension 表模型
- 包含 `id`, `config`, `config_schema`, `enabled` 等字段

### 编码指引

**创建新 Extension**:
1. 在 `extensions/` 创建目录，命名为扩展 ID
2. 定义 `Extension` 类，继承 `ExtensionBase`
3. 实现 `_register_apis()` 注册 API（如需要）
4. 实现 `_init_sources()` 和 `_init_resolvers()` 初始化插件
5. 启动应用时自动发现和加载

**配置管理**:
- 配置通过 `config_cls` 参数定义 schema
- 运行时通过 `cls.config` 访问
- 关闭时自动保存到数据库

参考现有扩展：[extensions/](../../../extensions/)（rss, mail, github, telegram 等）
