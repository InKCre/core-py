## extensions/ - Built-in Extensions (内置扩展)

内置扩展包目录，提供开箱即用的数据源和功能扩展。

### 扩展架构

每个扩展是独立的 Python 包：
```
extensions/
├── {extension_id}/
│   ├── __init__.py          # Extension 类定义
│   ├── pyproject.toml       # 依赖（可选）
│   ├── schema.py            # 数据模型
│   ├── resolver.py          # Resolver（可选）
│   ├── source.py            # Source（可选）
│   └── README.md            # 文档
```

### 内置扩展列表

| Extension ID | 功能 | Source | Resolver |
|--------------|------|--------|----------|
| [rss](rss/) | RSS/Atom 订阅源采集 | ✅ | ✅ |
| [mail](mail/) | IMAP 邮箱采集、Newsletter | ✅ | ✅ |
| [github](github/) | GitHub Stars/Repos | ✅ | ✅ |
| [telegram](telegram/) | Telegram 消息采集 | ✅ | - |
| [twitter](twitter/) | Twitter Bookmarks | ✅ | ✅ |
| [learn_english](learn_english/) | 英语学习材料组织 | - | ✅ |

### Extension 组成

**必需组件**:
- `__init__.py`: 定义 `Extension` 类，继承 `ExtensionBase`
- `schema.py`: 配置 Schema 和数据模型

**可选组件**:
- `source.py`: 实现 `SourceBase`，定义数据采集逻辑
- `resolver.py`: 实现 `ResolverBase`，定义内容解析逻辑
- `pyproject.toml`: 扩展专属依赖（会合并到主项目）

### Extension 发现和加载

1. **自动发现**: 应用启动时扫描 `extensions/` 目录
2. **同步到 DB**: `ExtensionManager.sync()` 写入数据库
3. **启动扩展**: `ExtensionManager.start_enabled()` 启动已启用的扩展

### 开发新扩展

参考 [app/business/extension/AGENTS.md](../app/business/extension/AGENTS.md)：

1. 创建目录：`extensions/my_extension/`
2. 定义 Extension 类：
```python
# __init__.py
from app.business.extension import ExtensionBase

class Extension(ExtensionBase, ext_id="my_extension", config_cls=MyConfig):
    @classmethod
    def _register_apis(cls, router):
        pass
```
3. 实现 Source/Resolver（如需要）
4. 重启应用自动加载

### 扩展安装

- **内置扩展**: 已在此目录，直接启用即可
- **第三方扩展**: 先通过受信构建流程加入制品；运行时不下载或安装代码

### 扩展配置

- 配置通过 Extension API 更新（`PUT /extensions/{ext_id}`）
- 配置 schema 在 `ExtensionModel.config_schema` 中定义
- 运行时通过 `Extension.config` 访问

### 编码指引

- Extension ID 使用 snake_case
- 避免与核心 API 路由冲突（Extension API 前缀：`/{ext_id}/`）
- Source/Resolver 注册在 `_init_sources()` / `_init_resolvers()` 中
- `_init_sources()` / `_init_resolvers()` 必须显式调用 manager 注册 API，以支持
  disable 撤销后在同一进程再次 enable；只写 import side effect 不足够。
- 持有 singleton 或连接的 extension 必须在成功 close 后重置引用，使 re-enable 创建新实例。
- extension 的依赖同时进入根 `pyproject.toml` 固定 profile 和根 lock

参考现有扩展代码了解最佳实践。
