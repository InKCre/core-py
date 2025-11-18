---
description: "When you read or update `app/business/extension.py`"
---

## ExtensionManager

### check_installed

> 遍历 `extensions/`，未在数据库中的插件则插入，在数据库中的插件则更新 nickname, version。
> 从而使得可以直接往 `extensions/` 中添加包即可完成插件安装，不需要再手动更新数据库。

Notes:
- 依赖于 `extensions/**/pyproject.toml` 来识别插件的元数据