# storage/ Local Guide

本文件只描述 `app/business/info_base/storage/` 的局部事实与风险边界。更上层的 ingestion mechanics 看 [app/business/info_base/AGENTS.md](../AGENTS.md)；跨模块结构看 [docs/30-unit-tdd/business-pipeline-and-authority.md](../../../../docs/30-unit-tdd/business-pipeline-and-authority.md)。

## 何时阅读

在以下情况进入本目录前先读这里：

- 修改 `StorageManager` 或 `Storage`
- 新增 / 删除 storage type
- 修改 built-in storage setup 或 storage ID 约定
- 修改 storage 与 resolver 的责任边界

## 局部执行规则

- storage 只负责“按 pointer 取 raw content”，不要把语义解释塞进 storage。
- built-in storage ID 保持负数；不要把用户可创建的 storage 和 built-in ID 空间混在一起。
- 若改动会影响 import-time 注册、dynamic import fallback、或 built-in setup，先读 `main.py` 与 `__init__.py`，不要只看单个 storage 实现。

## 关键文件

- `app/business/info_base/storage/main.py`: `StorageManager`、`Storage` 基类、built-in setup
- `app/business/info_base/storage/http.py`: built-in HTTP storages
- `app/business/info_base/storage/__init__.py`: built-in storage import side effect

## 当前稳定事实

### Registry Side Effect

- `Storage.__init_subclass__()` 只把 storage class 注册到
  `StorageManager._STORAGE_CLASSES`。
- `StorageManager.sync_storage_types()` 在显式 runtime bootstrap 中同步
  `storage_types` 记录；import 本身不得连接数据库。
- storage 可用性仍依赖 import-time 内存登记，但不依赖 import-time 外部写入。

### Built-In Storage IDs

当前 built-in storage ID 约定：

- `-1`: `http_image`
- `-2`: `http_video`
- `-3`: `http_html`

这些 negative IDs 的目的是和用户自定义 storage 避免冲突。

### Fetch Responsibility

- `StorageManager.get_storage()` 先按 `storage_id` 读取 `StorageModel`，再决定使用已注册 class 还是 dynamic import。
- storage 返回的是 raw content，不负责 block identity、resolver semantics、embedding ownership。

## 局部风险

- built-in storage types 当前是短字符串（如 `http_image`），不是 dotted import path。
- 这意味着如果 built-in class 没有先被 import 注册，`get_storage()` 的 dynamic import fallback 并不能正确恢复它们。
- 所以 `storage/__init__.py` 的 import side effect 不是装饰品，是 built-in 可用性的前提。

## 编辑指引

- 新增 built-in storage 时，同时更新 negative ID 约定与 `setup_builtin_storages()`。
- 新增非 built-in storage 时，先想清楚它是靠 import-time 注册，还是必须支持 dotted-path dynamic import。
- 若某个变化会把 raw-content fetch 和语义解释揉在一起，优先判定这是不是 resolver 责任，而不是继续加 prose。
