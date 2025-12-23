# `app/business/extension.py` coding guide

## 插件元数据

可以通过插件文件夹下的这些文件读取元数据：

### `pyproject.toml`

```toml
[project]
name = "inkcre-ext-mail"  # the name publish to PyPI
version = "0.1.0"  # as extension.version

[tool.inkcre-ext]
id = "mail"  # optional since folder name is already the extension id
nickname = "Mail" 
```

### `inkcre-ext-<extid>-<version>.dist-info/metadata.json`

```json
{
  "name": "inkcre-ext-<extid>",
  "version": "0.1.0",

  "extensions": {
      "inkcre-ext": {  // corresponds to `tool.inkcre-ext`
         "nickname": "",
         "id": ""  // optional
      }
  }
}

```

## 下载插件

对应实现：`ExtensionManager.download`

任务：安装插件到本地（`extensions/`中）

Notes:
- 从PyPI下载：访问 `https://pypi.org/pypi/inkcre-ext-<extid>/json` 查询文件链接列表，找到对应版本的 `packagetype` 为 `bdist_wheel` 的链接而后下载
- 解压：解压下载的wheel文件到 `extensions/` 中（解压后需要进行结构转换）：

  ```
  extensions/
    <extid>/
      __init__.py
      ... other extension source files ...
      pyproject.toml
      inkcre-ext-<extid>-<version>.dist-info/
        metadata.json
  ```

  - `extensions/inkcre-ext-<extid>/<extid>/**` -> `extensions/<extid>/**`
  - `extensions/inkcre-ext-<extid>/inkcre-ext-<extid>-<version>.dist-info/**` -> `extensions/<extid>/inkcre-ext-<extid>-<version>.dist-info/**`

## 同步安装情况

对应实现：`ExtensionManager.sync`

任务：
- 遍历 `extensions/`，未在数据库中的插件则插入，在数据库中的插件则更新 nickname, version
- 检查数据库中记录的插件是否下载到了 `extensions/` ，如果没有则下载

从而使得：
- 可以直接往 `extensions/` 中添加包即可完成插件安装，不需要再手动更新数据库
- 在 Heroku, Cloudflare Worker 等没有持久性存储（每次重启、重新部署就擦除数据）的环境中不会出现数据库有记录但是没有实际下载代码的情况

Notes:
- 依赖于 `extensions/**/pyproject.toml` 来识别插件的元数据
