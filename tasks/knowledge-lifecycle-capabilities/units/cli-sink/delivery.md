# CLI 按 owner 交付

2026-09-14，Sir 已授权按依赖顺序合并、发布、从 PyPI 本地安装后连接生产 Core，全部通过后关闭 unit。
这取代此前的禁止合并限制。工具架构审查请求已撤回。没有跨 session 通信，没有提交其它 Organization 工作。

## 已合并与已交付

| Owner | PR / main revision | 实际结果 |
| --- | --- | --- |
| ext-reg | [#35](https://github.com/InKCre/ext-reg/pull/35) / `71cbf6b`；修正 #36 / `0f05bb2`、#37 / `006759a` | runtime 0.1.3 wheel/sdist 已正式发布 |
| Hub | [#25](https://github.com/InKCre/docs/pull/25) / `5d0d8d7` | 两个 Spoke 分别提交 shared ref，检查通过 |
| Core | [#102](https://github.com/InKCre/core-py/pull/102) / `10a5384` | CI/Preview、首发 production、stable admission 成功 |
| client-web | [#106](https://github.com/InKCre/client-web/pull/106) / `47fa3f6` | 新 stable 上的 CI/E2E、Pages production/smoke 成功 |
| Core Release | [#103](https://github.com/InKCre/core-py/pull/103) / `4143abe` | Core 0.3.0 生产与三个 Extension 补丁发布成功；CLI 0.1.0 上传失败 |

均采用 protected-main PR/squash，不直接推 main，不从 PR 发布 canonical package，不消费 PR CI 产物作为正式包。
这些是跨仓库交付依赖，不是 Git ancestry stack。

## 当前关闭条件

CLI 0.1.0 的 [发布 run 34834897814](https://github.com/InKCre/core-py/actions/runs/34834897814) 已成功选择版本、
独立检查并构建，但 PDM 未能经 PyPI OIDC 取得上传凭据。公开 PyPI 项目 JSON 仍返回 404。
正式 pip 安装和随后生产复验尚未发生，unit 不关闭。

需要在 PyPI 核验 pending Trusted Publisher：project `inkcre-cli`、GitHub owner `InKCre`、repository
`core-py`、workflow `cli-publish.yml`、environment `production`。已向 Sir 请求确认。Computer Use 遇到 Mac
锁定，未进入账号、未修改权限。恢复后重跑 CLI publisher，再执行 [production-acceptance.md](production-acceptance.md)
的安装与旅程。已有 [本地四条旅程](local-acceptance.md) 不能替代这一步。

client-web Native Extension release run 34834894118 在创建 Version PR 时被仓库设置拦住；只读查询确认
`can_approve_pull_request_reviews=false`。Pages 部署已独立成功。本轮未改仓库权限，另行向 Sir 报告。

## 交付过程中的修正

runtime #35 合并后，run 34831716076 的发布 job 被 commit-title prefix 条件跳过。#36 移除该条件，
由已准备版本和既有 Release 决定发布。随后 run 34832208751 暴露包发布错误依赖 Registry 数据库验收。
#37 保留包的静态/生成合同检查与本次独立构建；完整数据库验收仍在 CI。补充 PR 的完整 CI 通过后才合并；
最终 [run 34832733241](https://github.com/InKCre/ext-reg/actions/runs/34832733241) 发布成功。

Core 在 runtime 0.1.3 正式可下载后才更新 pin，PDM 锁文件仅改变该 package 和 content hash；wheel SHA-256：
`613b500183ffd8afa6a6dd560a226a8994e73e24148ad84d37536ec804023075`。正式依赖 head `e057cad` 的
CI run 34833041559、Preview run 34833038284 均成功后合并 #102。两个 Hub ref 分别独立提交，
pre-bump/pre-commit 检查通过。

Core 自动 production 按 Core version 变化选择。#102 合并后，先用既有 workflow_dispatch 交付精确 main
artifact；新 REST 生产通过后再合并 Release PR #103，避免 CLI 首发先于 provider，不新增永久发布依赖。
#103 只准备 Core 0.3.0、CLI 0.1.0、Mail 0.2.1、RSS 0.1.1、Twitter 0.3.1；另补正 CLI changelog 标题与
Towncrier 插入锚点。其 CI run 34834065898、Preview run 34834063697 均通过后合并。

client-web CI run 34834580025 明确选择 `10a5384` / `0794ff84…` stable，全部检查与两项 E2E 通过后才合并
#106。旧 Organization 收尾、共享 packet 中相应 delta 和未跟踪 Python skill 保持本地，未混入提交。
