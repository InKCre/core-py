# 独立项目、依赖与协议复用

状态：2026-09-13 按 [D-598](../../decisions/D591-D600.md) 确认，并纠正为 core-py 仓库内的独立 PDM project；
CLI 信任 Core REST 的业务返回，只做必要转换，不建立响应再校验层。产品源码实施与发布尚未授权；
2026-09-14 已按关键准备授权，在隔离临时项目完成依赖安装、构建与独立安装实验，没有新增自动化测试。

## 独立分发，不导入 Core runtime

CLI 放在当前仓库的 `cli/`，拥有自己的 `pyproject.toml`、`pdm.lock` 和开发环境；distribution 与 executable
均为 `inkcre-cli`，Python import package 为 `inkcre_cli`。不新建仓库，不创建第二份 unit packet。
独立安装与依赖边界不要求独立 Git 仓库。

```text
core-py/cli/
  pyproject.toml
  pdm.lock
  src/inkcre_cli/
    commands/       # 按已有命令组组织；不是动态 CLI plugin registry
    ...             # 本机连接、REST 接入、输入与输出按真实职责组织
  docs/             # 安装、命令用法、CLI 维护与发布
```

Core 的 REST 实施仍归服务端。CLI 是公开协议的消费者，安装后的运行不依赖 core-py checkout、数据库模型或
Extension runtime；也不通过 sys.path 或本地 path dependency 绕过这一边界。同仓库可以在同一 PR 中修改
协议提供方与消费者，但 CLI 仍有独立的依赖、构建产物和版本。发布顺序需先使 Core 新接口可用，再发布使用
它的 CLI。不因两个项目都是 Python 就另建第三个合同包。

本轮采用普通嵌套 PDM project，不配置 workspace。PDM 2.28.0 已有 experimental workspace：成员共享根环境
和 lock，并被视为根项目的隐式 editable dependencies；它主要帮助需要一起解析本地包依赖的 monorepo。
Core 与 CLI 没有 Python package 依赖，独立解析更直接，也能防止完整 Core 环境掩盖 CLI 缺少安装依赖。
workspace 本身不必然破坏分发隔离，只是目前没有需要它解决的问题。

从仓库根显式选择子项目即可使用 PDM 的现成能力：

```sh
pdm install -p cli
pdm run -p cli inkcre-cli --help
pdm build -p cli
```

以上为产品实施后的命令。当前 PDM 2.28.0 的 -p、独立环境路径与 wheel 安装已在临时探针项目验证；
见 [工具链预演](preflight-toolchain.md)。没有在产品 cli/ 创建代码，也没有复用父环境来证明依赖完整。

## 库选型

| 职责 | 选择 | 具体收益与边界 |
| --- | --- | --- |
| 命令树、argv、help | Click | 原生 command/group、可组合 option decorators 与调用上下文，适合多组管理命令；不自制命令解析框架 |
| 本机配置与输入 | Pydantic 2 | 在 CLI 自有输入边界使用；不借响应 DTO 再校验 Core 返回，不复制动态 Extension 业务校验 |
| HTTP | HTTPX 的同步 Client | 统一连接配置、超时、响应及资源清理；一次 invocation 复用 Client，Job wait 不反复新建连接 |
| JWT 签发 | PyJWT | 按 D-581 复用现有 JWT wire contract，不导入依赖 settings 的 Core middleware，也不自己实现 JWT |
| JSON、文件、接收端 MIME | 标准库 json / pathlib / tempfile / email.parser | 复用格式与文件能力，只保留 InKCre 自己的呈现和 multipart 字段关联 |
| 开发与构建 | PDM 2.28 + pdm-backend | 独立 src-layout package，产出 wheel / sdist；最终安装者不需要 PDM |

CLI 直接运行依赖因而是 Click、Pydantic、HTTPX、PyJWT；标准库不形成安装依赖。建议 Python 下限 3.12，不把
Core 的 `<3.13` runtime 上限复制过来。依赖具体范围与 Python 3.12.10 的干净安装已在预演验证；其它版本和
OS 未作运行验证。不能把当前工作环境里的传递依赖当作独立 wheel 已声明完整。

argparse 可以完成该 CLI，SVC 也实际使用它；没有功能性缺陷需要否定。这里推荐 Click，是因为本 unit 已有
多级命令组和重复公共选项，Click 的组合与 dispatch 可以直接使用，避免各命令自行管理 Namespace/调用分派。
Typer 同样可行，Extension Toolkit 已在使用；但本 CLI 的主要业务输入是 JSON 和动态 schema，Python 函数
注解转 argv 的收益较小。公共选项复用及既定错误呈现会直接使用 Click 的接口，因此建议直接依赖 Click。
这不是组织级库统一，也不是对 Typer 的兼容性否定。

共同选项在实际 leaf command 上可用，保持既有示例 `job list --json`；`--connection` 等连接选项也应保持这种
可发现性，不只定义在 root callback 后要求调用者换位置。选项通过少量普通 decorators 复用，不生成新的参数
DSL。没有具体需要时不承诺任意 argv 位置等价。

Click 的默认退出和错误打印不等于 D-597：入口使用公开的 main(standalone_mode=False)，让库处理 help/Exit，
调用方收口实际错误。2026-09-14 的[独立安装预演](preflight-toolchain.md) 发现手动 context/invoke 容易遗漏
正常 Exit，已用该原生路径复验。`--schema` 可以在没有业务输入时返回、`--help` 不执行 callback、UsageError
可以交由入口处理；完整产品错误和中断路径仍由实现验收覆盖。业务输入只在执行分支加载；help 不读取连接、
不连接 Core。公共输出模式不能通过扫描业务 JSON 字符串里的 `--json` 来判断。

HTTPX 使用同步 Client 即可承接当前请求响应与有界轮询；本轮不增加 async CLI framework。Recall 的独立模式
与部分结果按 D-594/D-597 实现，不为选 HTTP 库额外承诺并行执行或改变等待/超时合同。

## 复用 REST 合同，不复制领域 owner

```text
CLI commands ──→ CoreRESTClient ──→ Core REST ──→ 既有领域 owner
      └────────→ CLI 结果呈现 / 文件交付
```

`CoreRESTClient` 集中 base URL、JWT 签发、HTTP 生命周期、响应状态与 Content-Type 解码；command 保留对象选择、
method/path 与 CLI 输入的映射。它不是 Peer outbound，也不为只有 REST 的当前实现增加 TransportBase。
避免为每个 REST 方法再写一层只转发一次请求的 service。

Core Pydantic forms 与其 OpenAPI 是静态 HTTP 合同的 authority；Source/Job/Resolver/config 的 owner schema
通过已设计的发现接口提供动态合同。CLI 的 `--schema` 消费这些表示，不把 Extension schema 编译成 Python
classes，也不复制 Extension 方法清单。准确到 JSON 输入位置的 schema 投影仍归已确认 D-577 的实现工作。

Pydantic 保留在 CLI 的连接配置和自身输入边界。Core REST 已拥有业务返回合同，CLI 不再对响应调用
model_validate / TypeAdapter.validate_python 或增加 JSON Schema 校验。Job wait 等需要读取 id/status 的
代码可使用普通已解码结构与 TypedDict 等静态描述，不为了类型检查重新构造一套运行时响应校验器。

JSON/MIME 解码、multipart 字段关联、日期展示和 bytes 落文件是协议或呈现转换，不是业务合法性复核。
`--json` 保留完整返回值，不经只声明少数字段的模型重新 dump，避免删字段、注入默认值或规范化 raw content。
HTTP 错误与实际解码失败仍正常报告；信任返回不是把无法解析的内容当作成功，也不要求自行猜测、修复或重发。
不为本来不需要的响应模型另造通用无校验构造器。

已查阅 datamodel-code-generator 的 OpenAPI → Pydantic 能力；本轮不选择生成整套 SDK 或抽取共享模型包。
两者并非技术不可行，而是当前没有请求/响应 Python 对象跨进程直接复用的需要，也无法替代动态 schema 与
multipart 关联。后续若稳定静态 DTO 的维护确实成为成本，再按消费范围采用现成生成器，不先建自有生成框架。

## multipart：发送与读取分别选适合的公开接口

沿用 [内容 HTTP 表示](content-transport.md) 的已确认合同。Core 侧建议显式声明当前已由传递依赖安装的
aiohttp，使用公开 `MultipartWriter("related")`；JSON root 固定第一项，binary 使用 Content-ID，
`await writer.as_bytes()` 交给 FastAPI Response。它不引入 aiohttp server，也不改变 Core 的 FastAPI 入口。

CLI 用 HTTPX 取得响应，再用标准库 `email.parser.BytesParser` 读取 MIME；不需要随之安装 aiohttp。
不同库实现同一 wire contract，不要求两端导入同一 Python encoder/decoder。双方仍需实现且仅实现 InKCre 的
JSON Pointer 与 binary part 关联、结果形状选择及本地文件呈现。Core 要声明直接使用的 aiohttp 依赖，不能依赖
另一个包恰好安装它。

本轮局部证据：

- Python 3.12 的 `EmailMessage(policy=policy.HTTP)` 配合 `cte="binary"` 再 `as_bytes()` 会把 payload 内
  单独 CR/LF 规范化为 CRLF，实际 bytes 改变。因此不能把这个标准库序列化路径用作 HTTP raw binary writer。
  这不否定其 parser 对本合同的可用性。
- urllib3 2.7.0 的公开 RequestField / multipart encoder 加标准库 parser 能保持 bytes；但它的外层声明是
  form-data，需要另行适配 related。本轮不推荐为此再选一套 encoder，保留为调查证据。
- aiohttp 3.14.3 `MultipartWriter` → FastAPI 0.139.2 Response → HTTPX 0.28.1 ASGI → BytesParser
  已在内存中往返全部 256 个 byte 值、CR/LF/CRLF、空 bytes、Unicode JSON、普通 null 与 Content-ID。
  未使用 Base64，也未增加 D-585 已排除的 start 参数。

这些只验证候选库的接合和 byte 保真，不是实际 Core/Resolver 的端到端验收，也不证明完整 JSON Pointer
关联、模型序列化或大结果文件交付已完成。当前 producer 已把内容驻留内存，不增加“端到端 streaming”的承诺。

## 分发与下一步

```sh
python -m pip install inkcre-cli
inkcre-cli --help
```

这是拟议的最终使用方式，不表示包已经发布。安装者取得普通 Python wheel，不携带 FastAPI、数据库 driver、
AI runtime 或 Extension runtime。CLI 的版本独立于 Core，不要求两个版本号相等；本轮验收记录具体兼容的 Core
版本与 CLI 构建，不添加调用前版本握手、版本相等 gate 或历史兼容矩阵。

同仓库的 release/version 接合已按 D-599 确认，见[发布方案](release-and-distribution.md)；各查询的长输出
续读覆盖已按 D-600 确认，随后进入整体验收、实现计划与 preflight。
PyPI publication authority 是后续实际交付前置项；本轮查询 inkcre-cli 返回 404 不等于保留名称或已有发布权限。
无需新仓库配置。main 发布权限、feature branch → PR → main 和同次 release 构建遵循组织规范；CLI 不属于
Extension 发布矩阵，复用既有版本准备流程而独立发布，不复制一套 Core release controller。

## 依据

本地核验：core-py `pyproject.toml` 的 `distribution=false` / `build-backend="none"`、
`app/middleware.py` 的 JWT 签发、`scripts/generate-openapi.py`；
`../ext-reg/toolkit/pyproject.toml` / `src/inkcre_extension_toolkit/cli.py`；
`/Volumes/WorkSSD/Development/svc/svc_cli/pyproject.toml` / `src/svc_cli/cli.py`；
`../.github/GOVERNANCE.md` 与 `CONTRIBUTING.md`。组织内存在 argparse、Typer 和不同 build backend，
未发现一条要求所有 Python CLI 采用同一解析库的规范。

一手资料：

- [Click 的命令组合](https://click.palletsprojects.com/en/stable/complex/) 与
  [异常/退出接口](https://click.palletsprojects.com/en/stable/exceptions/)。网站当前为 8.5.x，局部实验为已安装 8.4.2；
  只采用二者已有的公开机制，未宣称已验证未安装的新版本。
- [Typer callback 的参数作用域](https://typer.tiangolo.com/tutorial/subcommands/callback-override/)、
  [HTTPX Client](https://www.python-httpx.org/advanced/clients/)。
- [aiohttp Multipart](https://docs.aiohttp.org/en/stable/multipart.html)、
  [Python MIME parser](https://docs.python.org/3.12/library/email.parser.html)、
  [urllib3 Multipart](https://urllib3.readthedocs.io/en/stable/reference/urllib3.fields.html)。
- [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator)、
  [PDM backend](https://backend.pdm-project.org/build_config/)、
  [Python CLI packaging](https://packaging.python.org/en/latest/guides/creating-command-line-tools/)。
- [PDM workspace](https://pdm-project.org/latest/usage/workspace/) 与
  [虚拟环境](https://pdm-project.org/latest/usage/venv/)；本机 PDM 为 2.28.0，root pyproject 未配置 workspace。

ponytail 在本轮用于排除没有实际收益的共享包、自制协议实现与生成框架；Python backend 技能用于区分 HTTP
合同 owner、CLI 消费模型与 runtime 依赖。两者不替代本任务的 review / implementation gate。
