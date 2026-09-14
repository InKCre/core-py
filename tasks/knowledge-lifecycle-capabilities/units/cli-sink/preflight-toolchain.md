# 独立 CLI 构建与安装预演

2026-09-14；对应计划 P4/P5 的独立项目与入口机制。结论：工具链与所选依赖可以支持当前方案。
这不是 inkcre-cli 产品实现或 REST 验收，实验未发布任何包，也未修改根 pyproject、lock 或业务源码。

## 隔离范围

在 WorkSSD 的忽略目录 `.runtime/cli-preflight.uxX70u/cli` 创建独立 PDM project，发行名明确为
`inkcre-cli-preflight-probe` / 0.0.0，只提供最小的输入/schema/JSON 探针；不用真实 inkcre-cli 包名冒充首发。
依赖仅 Click、Pydantic、HTTPX、PyJWT，构建后端 pdm-backend，src layout。

使用 PDM 2.28.0 显式选择系统 Python 3.12.10，并设置 PDM_IGNORE_ACTIVE_VENV=1。实测 PDM 在该子项目
创建自己的 `.venv`，run 使用这个解释器，不复用根 Core 环境。依赖约束和本次解析结果为：

| 直接依赖约束 | 本次解析版本 |
| --- | --- |
| click >=8.1,<9 | 8.5.0 |
| pydantic >=2.10,<3 | 2.13.5 |
| httpx >=0.28.1,<0.29 | 0.28.1 |
| PyJWT >=2.10,<3 | 2.14.0 |

Python 声明为 >=3.12，没有继承 Core <3.13 的 runtime 上限。本次只证明 macOS arm64 / Python 3.12
实际安装，不宣称其他 Python/OS 组合已跑过。正式项目使用自己的 lock；不复制整个实验 lock 作为 Core 依赖。

## 已执行的安装链

```text
pdm use -p <probe>/cli --no-version-file <system-python3.12>
pdm install -p <probe>/cli
pdm lock --check -p <probe>/cli
pdm build -p <probe>/cli
  → sdist → 从 sdist 构建 wheel
system-python3.12 -m venv <probe>/consumer
<consumer>/bin/python -m pip install <wheel>
<consumer>/bin/python -m pip check
```

安装后的 executable 从 `/Volumes/WorkSSD`（仓库外）以普通 subprocess 调用；没有设置 PYTHONPATH。
consumer 环境不能导入 app、FastAPI、SQLAlchemy 或 PDM。探针实际导入四个直接依赖、构造 Pydantic 输入、
创建/关闭 HTTPX Client、用非凭据的本地常量完成 JWT round-trip；没有向 Core 或外部服务发送业务请求。
pip check 无缺失或冲突。

## Click 入口预演的修正

第一版手动 make_context/invoke 只捕获 ClickException，导致 --help 的正常 Exit 被当成未捕获异常。
改用 Click 原生 `command.main(..., standalone_mode=False)`，由库处理 help/Exit，调用方仍可接收并格式化
ClickException。这样不必自建一套 Exit 分派；它不是改变 CLI 输出合同。

重新构建并替换 consumer 中的探针 wheel 后，以下 subprocess 检查通过：

| 调用 | 可观察结果 |
| --- | --- |
| --help | exit 0，stdout help，stderr 空；无需连接或业务输入 |
| --schema | exit 0，stdout 单个 JSON schema；无需业务输入 |
| --input-json '{"value":"probe"}' --json | exit 0，单行 JSON，确认 Core 不可导入 |
| --json（缺业务输入） | exit 2，stdout 空，stderr 为可解析 JSON 错误 |
| --unknown | exit 2，stdout 空，stderr 为可解析 JSON 错误 |

这是入口和依赖隔离证据，不是完整 CLI 的 JSON 错误呈现实现；HTTP timeout、文件输出、多命令层级与真实
REST 仍按实现及已确认 Acceptance 验证。已有 JSON/bytes/multipart 设计实验不由本页替代。

本轮只在临时项目运行手工脚本，没有增加自动化测试、永久 demo command 或新的库封装。实验环境与构建
产物在结果记录后清理，避免在 WorkSSD 累积额外 virtualenv。

## Release PR 准备的隔离预演

完整 preflight 在 `.runtime/cli-complete-preflight.m9huoV/release-spike/` 复制现有 release.py、Towncrier
配置，创建最小的 Core/Mail/CLI 三项目副本。CLI discovery 仅在探针内接入现有 ReleaseProject；调用真实
`prepare(("cli",))`，不用另写 version/changelog 实现。Towncrier 25.8.0、PDM 2.28.0。

CLI 的 added fragment 使 0.0.0 变为 0.1.0，fragment 被消费，CHANGELOG 更新；Core/Mail 的 pyproject
和 CHANGELOG 均未变化，探针 Git index 的前后 bytes 一致。`extensions_only` 不包含 CLI。
这是编排可复用与 index 隔离证据，不表示实际仓库的 CLI discovery、allowlist 或 bootstrap 已实现。

实施落点已经定位：release.py 显式发现 cli/、给普通项目传正确 key；affected_projects 只纳入实际
artifact inputs；Release PR path allowlist 从项目目录得到；新项目尚无 base 时不因 version comparison
自动发布 0.0.0。继续一个 release/next controller，不另建 CLI controller。

根 Ruff/对应 pre-commit 排除 cli/ 并给 CLI 独立 checks；根 Pyrefly 的显式 source paths 不扩入 CLI。
Dockerfile 和远程 build context 已使用显式目录，保持不复制 CLI；普通 Docker context 也排除 cli/。
CLI 的 PDM lock、lint/type/build 独立，不能以根 gate 通过替代。

client-web 声明 Node 22.22.3、pnpm 11.11.0。实际 project exec 得到 Node v22.22.3，显式执行 pnpm@11.11.0
得到相同版本；不误用全局 Node 24 / pnpm 11.20。Playwright 的实际浏览器通路见环境页。
Core 现有 `pdm run check:foundation` 已通过（lock、基础环境、shell、migration manifest），未运行或新增
本 unit 的自动化测试矩阵。完整 gates 随实现候选运行。

已核对 PDM publish 原生支持 --no-build / --skip-existing；正式发布采用原生 Trusted Publishing。
没有调用 publish，也没有以“命令可用”替代 PyPI 权限验证。
