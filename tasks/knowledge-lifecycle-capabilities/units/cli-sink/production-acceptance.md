# CLI 正式交付与生产验收记录

2026-09-14。正式发行包与生产 REST 的验收证据记录如下。

## 正式交付

- Core `10a5384`：artifact run 34833831468、production run 34834061508 成功。数据库从 `143c4f4adc85`
  迁移到 `d41cc84db0c5`；Core/PostgREST、Peer 广告、smoke、stable 均成功。镜像 digest：
  `sha256:0794ff84eac929a8f373029b5feb8b9ddb2fd0480eaf0e55b0c13c01c997bdf0`。
- Core 0.3.0 / `4143abe`：[production run 34835045453](https://github.com/InKCre/core-py/actions/runs/34835045453)
  成功，stable digest `sha256:b5271a7ed351f26218b11a7ea52d6ea9dc7e90472b509ad1e9d7e96f472586f1`。
- client-web `47fa3f6`：[Pages run 34834894157](https://github.com/InKCre/client-web/actions/runs/34834894157) 成功；
  deployment `f838f37e-6b8a-4e6b-a67d-d9bc92f931b9`，发布 URL 与 `https://app.inkcre.dev` smoke 均通过。
- [Extension publication run 34834897847](https://github.com/InKCre/core-py/actions/runs/34834897847) 成功发布
  Mail 0.2.1、RSS 0.1.1、Twitter 0.3.1；其它版本未改写。

## 补充实测，不冒充 PyPI 安装

沿用原来独立安装的候选 CLI wheel 0.0.0，从 checkout 外经真实 REST 请求生产 Core，不导入 Core。
JWT 来自系统 Keychain；connection check（含受保护读取）、peer get/list、有界 wake 均退出 0。

生产原先未安装任何 Extension。实际通过 CLI 安装已发布的 Mail 0.2.1、enable、发现 Source types/schema、
读取 Extension 记录成功，证明正式 wheel 的 installed record/finalize 问题已闭合。没有创建邮箱 Source 或
读取用户邮件。随后 disable、uninstall 成功，安装列表恢复为空；不是卸载用户原有安装。

脚本与结果位于 ignored `.runtime/cli-production.GlB7a0/`，使用 `candidate-*` 文件名区分来源。
`accept.py` 不进入 CI，连接文件含本机验收凭据、不提交。共享开发数据库没有 reset 或升级。

## PyPI 正式安装

CLI PyPI run 34834897814 首次在上传阶段报告 OIDC token 获取失败。Sir 配置 Trusted Publisher 后，
第二次 attempt 于 2026-09-14 13:19 UTC 成功上传 `inkcre-cli 0.1.0`，没有改为手工 token 兜底。

独立环境 `/Volumes/WorkSSD/Development/InKCre/.tools/inkcre-cli` 使用
`pip install --index-url https://pypi.org/simple inkcre-cli==0.1.0` 安装正式 wheel；依赖清单没有
Core/FastAPI/SQLAlchemy。`~/.local/bin/inkcre-cli` 链接到该环境的命令，安装数据保留在 WorkSSD。
生产连接配置使用默认 `~/.inkcre/cli/connections.json`，凭据来自系统 Keychain。

首次复验记录了一次 readiness 超时与一次 TLS EOF；受保护的 Peer 读取仍成功。保留 `pypi-*` 失败证据，
后续独立复跑使用 `pypi-recheck-*`，不添加产品重试逻辑。复跑 connection check、wake、peer get/list 全部退出 0。

`accept.py roundtrip` 完整通过：动态 catalog/schema、提交 Python asyncio 官方原文与说明 Block、
raw/hydrated 读取、Resolver get_text、neighborhood/path/components、Block/Relation 原地更新；
lexical maintenance Job `3` 创建并经有界 wait 返回 finished，`CancelledError` 检索命中本次 Block `4`。
批量 get 混合存在与不存在实体时返回部分结果并退出 1，符合合同。最后删除本次 Block `4`、`5`，
连带 Relation 清理；保留已完成的 Job 记录。脚本退出 0，unit 关闭条件满足。

## 本轮方法

shared ref 按 edit-svc-shared-docs 的 Hub-first、独立提交方式更新。ponytail 将 runtime 发布修正收敛到既有
检查/构建与原生 Release 行为，不新增 controller。computer-use 仅尝试查看 PyPI 账号前置，因 Mac 锁定停止，
没有执行账号或发布权限修改。
