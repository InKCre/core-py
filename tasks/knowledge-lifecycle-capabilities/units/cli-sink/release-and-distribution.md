# CLI 版本与发布接合

状态：2026-09-13 按 [D-599](../../decisions/D591-D600.md) 确认。项目位置与协议边界沿 D-598；本页不增加
实施、commit、push 或 PyPI 发布授权。

## 同一版本准备流程，独立的发布产物

CLI 作为 scripts/release.py 中的独立 ReleaseProject，key 为 cli；它不是 Core，也不是 Extension。
复用现有 Towncrier 25.8.0、root towncrier.toml 与单一 release/next PR，不增加 CLI release controller。

| 项目 | 版本 / changelog / pending fragments | 发布目标 |
| --- | --- | --- |
| Core | root pyproject.toml / CHANGELOG.md / .changes | 既有 Core 镜像与部署 |
| CLI | cli/pyproject.toml / cli/CHANGELOG.md / cli/.changes | PyPI inkcre-cli wheel / sdist |
| 各 Extension | 各自目录内的同名文件 | 既有 Extension Registry |

```text
feature PR：源码 + 所属项目的 fragments
  → main：现有 controller 更新 release/next
    → Release PR：只准备有 pending intent 的项目版本和 changelog
      → main：各发布入口独立选择自己的新版本，重新构建并发布
```

只改 CLI 不提升 Core 或 Extension 版本；跨 Core REST 与 CLI 的实际变更各自提供 release intent。同一个
Release PR 可以包含多个项目，但版本号不必相同，也不以共同发布成败建立多产物事务。

CLI fragments 使用已有 added/changed/deprecated/removed/fixed/security 类型与 maturity-aware bump 规则。
初始开发版本为 0.0.0，由首个 added fragment 经正常 Release PR 产生 0.1.0，不在 feature PR 手动准备
首个正式 changelog。项目刚加入仓库不等于已准备发布；新的 PyPI 路径不因 base 中尚无 CLI 就上传开发版本。

## release.py 的必要调整

当前 ReleaseProject 已按 directory 访问 version、fragments 和 changelog，prepare 也逐项目执行 Towncrier，
大部分准备逻辑可以直接复用。实际不通用的部分是：

- _project_from_pyproject 的非 Extension 分支硬编码 key=core；需要让普通项目明确自己的 key/目录，不能
  把 cli 当成 Core 的别名。
- discover_projects 目前只列 root Core 和 Extension directories；加入 cli 这个明确项目即可，不扫描任意
  pyproject 或增加通用 package dependency graph。
- Release PR 的允许路径目前写成 root + extensions；按已发现项目的 directory/changelog/fragments 推导，
  不另抄一套 cli 路径列表。
- 新项目的初始 CHANGELOG 文件不能被误认成 feature PR 已经准备一次 release。当前 check 会把新增文件
  也算作 changelog_changed，需要结合 base 是否已有该项目区分初始文件与已有版本的 changelog 修改；
  不能为了通过检查省去 prepare 所需的文件，或增加迁移名称特判。
- affected_projects 要识别 CLI 交付源码及影响安装/入口的声明，同时保留各项目的责任。不能把 cli/** 的
  任意改动都当作必须发版；task、测试、贡献指南与纯工具链调整不虚构 CLI release note。依赖声明与开发配置
  的区别在实现预演中核对，不为此建立新的 CLI 专属 gate 或两次构建比较框架。

--extensions-only 继续只返回真正 Extension；CLI 不进入 extension-wheels、Extension preview inventory、
Registry metadata/prepare/upload/publish，也不把 CLI sources 加进 Core runtime 的安装依赖。
release tooling 本身在仓库根运行，不等于 CLI wheel 依赖 root package。

本轮不借加入 CLI 重写已有 SemVer 算法或 Extension 发布协议。现有事实不等于已验证本项扩展完成；修改范围
进入后续 implementation plan，并用现有命令和隔离的准备演练检查，不新增 helper/schema 自动化测试。

## CLI 的检查与正式发布

PR 检查新增独立的 inkcre-cli checks，选择 cli/ 的 PDM project，检查 lock、lint、静态类型和 wheel/sdist 构建。
不靠装有完整 Core 的环境证明 CLI 依赖完整；干净环境安装、实际命令与真实 REST 的黑盒验证由验收脚本承担，
不在本轮提升为自动化 E2E。Core 原有检查继续负责其变化，不把 CLI 检查伪装成 Extension wheel 检查。

新增 .github/workflows/cli-publish.yml。自动路径只选择已经存在的 CLI 项目在 main 上发生的 version 变更；
普通 feature merge、文档变化和首次加入开发版本均不发布。它从明确 main SHA 自行执行 CLI 检查与构建，
上传这一 release run 的产物，不消费 PR CI 上传的 wheel，也不从 Core image 中取 wheel。

```sh
# 下列是实施后的命令形状，本轮未执行。
pdm install -p cli --frozen-lockfile
pdm run -p cli check
pdm build -p cli
pdm publish -p cli --no-build
```

构建与上传分开，避免验证过产物后再次隐式重建。使用 PDM 已有 Trusted Publishing 支持；不手写 GitHub OIDC
换 token，不增加新的发布 SDK。Actions 只拥有触发、并发、环境、工具设置及调用；选择和构建逻辑放可独立
运行的仓库命令。上传 job 使用现有 production environment 与标准 id-token: write 配置。

同一 CLI 发布入口串行，不取消正在上传的 run；保留 main-only 的 workflow_dispatch 作为恢复入口。不照搬
Extension Registry 的 INITIAL_ONLY / Release association 协议。重复/部分上传使用 PyPI 与 PDM 的标准机制，
必要时显式 --skip-existing 续传缺失文件并报告跳过项；不自制 hash 对账或后台补发服务。准确的恢复操作在
preflight 与发布文档中说明，不能把不同 run 的重新构建声称为 byte-identical。

CLI 的常态发布不永久等待 Core deployment workflow，也不读取 Core 数据库、Peer advertisement 或要求两边
version 相等。若某个 CLI 版本新增了对新 REST 的依赖，在对应变更的交付顺序与兼容说明中体现。

## 首发顺序和实际前置条件

本 unit 按先 provider、后 consumer 的顺序安排首次交付：先合入并发布 Core REST / Job 等增量，再合入
CLI 首发代码与发布入口，最后由 CLI 的正常 Release PR 发布 0.1.0。两者仍属于同一 unit，可以在开发和
preview 中联合验收；这只是同仓库 PR/发布的顺序，不新增 implementable unit 或通用跨项目 release scheduler。
如 implementation plan 选择先合入 CLI 开发代码，也必须保留首次 PyPI 发布在 Core 接口实际可用之后的人工
交付顺序，不能为此把永久 CI/CD 依赖硬编码到 CLI 发布路径。

PyPI 需要配置 inkcre-cli 的 pending Trusted Publisher：GitHub owner InKCre、repo core-py、workflow
cli-publish.yml、environment production。首次正常上传可创建项目；不必先在本机手工上传一个版本。
该配置仍需账号 owner 的实际操作与发布授权；目前没有读取或修改 PyPI 账号，也没有证明发布权限已具备。
pending publisher 不保留包名，名称状态在真正发布前再确认。

首发闭环包括：Core 新接口可用 → CLI 独立构建与真实 REST 验收 → 正式 PyPI 发布 → 从 PyPI 在干净环境
安装指定版本并重复关键旅程。具体 journey 仍由下一阶段验收合同冻结，不把发布 HTTP 成功等同于产品验收。

## 依据与后续检查

已读取 scripts/release.py、scripts/automation/release_pr.sh、extension_publication.sh、repository_check.sh，
以及 .github/workflows/release-pr.yml、extension-publish.yml、production-deploy.yml、ci.yml；CONTRIBUTING.md、
docs/40-deployment/native-extension-distribution.md 与组织 GOVERNANCE.md。当前 Root Towncrier 已固定 25.8.0。

Dockerfile 当前采用显式 COPY，尚未复制 cli；新增 .dockerignore 的 cli/ 排除可避免把无关开发文件发入构建
context。Root Pyrefly 使用显式目录列表，CLI 检查应留在自己的环境；Ruff/pre-commit 的扫描范围需要在
实施预演核对，防止父子项目重复执行不同配置。这些都是接合检查，不扩展成仓库 cleanup。

一手资料：[PDM Build and Publish](https://pdm-project.org/latest/usage/publish/) 确认 Trusted Publishing 与
--no-build；本机 PDM 2.28.0 publish help 确认 -p、--no-build、--skip-existing。
[PyPI pending publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/) 说明首发创建与
名称不被预留；本轮没有执行这些外部写入。

ponytail 在本轮收敛了复用范围：现有版本准备 controller、现成 PDM uploader，新增 CLI 所需的项目身份与
PyPI 交付路径；不新增发布框架。查询续读后已获 D-600 确认，后续交付验证纳入 [Acceptance](acceptance.md)。
