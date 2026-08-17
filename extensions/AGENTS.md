# extensions/ - First-party native wheels

这里保存七个 first-party Extension 的生产源码，但 Core application image 不复制本目录。
每个子目录是一个独立 PEP 420 wheel producer。

## 必须满足的 wheel 形状

- `pyproject.toml` 使用标准 build backend，并完整声明所有直接外部依赖。
- 禁止 `extensions/__init__.py`；wheel 贡献 `extensions.<extension_id>` namespace package。
- entry point group 固定为 `inkcre.core.extensions`，每个 wheel 恰好一个 entry point。
- `[tool.inkcre-extension]` 声明 namespaced product name、nickname、`core-py` Host SDK 与 NPM
  SemVer range。
- Extension class 继承 `ExtensionBase`，可直接 import `app`、`libs`、`utils` 等 Core API。
- `_init_sources()` / `_init_resolvers()` 必须可被同一进程的 disable/re-enable 撤销和重建。

## 发布与版本

`scripts/extension_distribution.py` 构建期核对 wheel metadata、完整依赖、entry point、PEP 420
形状及 producer metadata。`scripts/extension_release.py` 自动发现本目录的 producer，并检查 Changie、
changelog、project version 与 Git transition。`.github/workflows/extension-publish.yml` 仅在 exact-main
checks 成功后，为 new or changed Release version 独立 prepare、上传、publish。Release name/version
不可复用；artifact input 变化必须先通过 Changie 提升该 Extension 版本。

本目录当前 producer：`github`、`learn_english`、`mail`、`memos`、`rss`、`telegram`、`twitter`。
