# CLI 按 owner 交付

2026-09-14，Sir 最新授权按依赖顺序合并本组 PR、确认 CLI 发布到 PyPI、本地安装连接生产 Core，验收通过后关闭
unit；这取代此前的禁止合并限制。继续使用 feature → main，不从 PR 发布 canonical package，不直接推 shared main。
没有跨 session 通信。上一条工具架构审查请求已撤回，没有因此修改源码。

## 批次

| Owner | 分支 | 内容 | 合并前依赖 |
| --- | --- | --- | --- |
| ext-reg | feat/cli-sink-runtime | Python runtime typed config/state 传递；按现有 Changie 准备 0.1.3 | 独立 review/CI；随后由 Sir 合并并触发既有发布 |
| Hub | feat/cli-sink-contract | 跨 Peer Job 停止、观察预算与可信记录读取边界 | 独立 review/CI；不含具体 Extension 或 CLI 实现 |
| Core | feat/inkcre-cli | 独立 CLI、普通 REST、Job 控制、校验边界、Extension publisher finalize、文档与本 unit packet | runtime 0.1.3 发布后更新 pin；Hub 合并后单独 shared-ref 提交；候选 Preview |
| client-web | feat/cli-sink-job-control | 两端 Job 协议的浏览器 worker；生成数据库类型与 Changeset | Core 新数据库/执行合同交付并通过当前 stable admission；Hub ref 单独更新 |

这些是跨仓库依赖，不是同仓库 ancestry stack。Core/client-web 在外部依赖未交付时保留 draft，PR body 明确
前置项；不得合并后再补 runtime pin 或两端 worker 验证。

## 已推送 PR

- [ext-reg #35](https://github.com/InKCre/ext-reg/pull/35)：源码 `f22641d`，补格式 `82a0b69`；runtime 0.1.3 候选，等待 review。首轮 CI 的 Changie Markdown 格式问题已按 Prettier 修正并推送。
- [Hub #25](https://github.com/InKCre/docs/pull/25)：`f84d9ed`，只含两个跨单元合同增量；Website contract 已通过，等待 review。
- [Core #102](https://github.com/InKCre/core-py/pull/102)：源码 `a2d2f93`，实施记录 `a206c99`；保留 draft，等待 runtime/Hub 前置交付。独立 inkcre-cli checks 首轮已通过。
- [client-web #106](https://github.com/InKCre/client-web/pull/106)：`83a60ce`；保留 draft，等待 Core stable 合同与 Hub ref。

四个 PR 均 base main、未合并、未启用 auto-merge。所有 PR body 已互相链接并写明跨仓库依赖和验收残余。
CI/Preview 的最新状态以各 PR 的 GitHub checks 为准，不将创建时的 pending 快照当作永久失败或通过。

原有 Organization 收尾、共享 packet 中相应旧 delta 和未跟踪 Python skill 保持本地。只有 CLI 对共享
control 文件的行级变化进入本 unit；不为清空工作区提交其它任务。

## 剩余关闭条件

四条本地旅程见 [local-acceptance.md](local-acceptance.md)。它们不替代正式 runtime/Registry 安装、
Core/client-web Preview 与 production、CLI 0.1.0 的 Release PR/PyPI 安装，以及 CLI 消费实际云端冷启动。
PyPI Trusted Publisher 首次配置仍需确认。

## 正式交付进展

- ext-reg #35 已 squash merge 为 `71cbf6b`；Hub #25 已 squash merge 为 `5d0d8d7`。
- Core Preview run 34827581213 已成功。Core/client-web 的 Hub ref 分别以独立提交更新到 `5d0d8d7`。
- runtime release run 34831716076 整体成功，但 publication job 被 commit-title prefix 条件跳过，0.1.3 尚未发布。
  补充 PR 只移除这个错误触发条件，保留已存在的版本检查、main 构建、已发布 Release 跳过逻辑；不新增发布框架。
- PyPI 首发需要 pending Trusted Publisher：InKCre/core-py、cli-publish.yml、production。已向 Sir 请求确认，
  其余交付并行推进，不把权限前置项写成发布通过。
- runtime 触发修正 #36 已合并为 `0f05bb2`；首次实际发布 run 34832208751 进一步暴露 package lane 调用
  Registry 数据库验收、缺少 `REGISTRY_TEST_DATABASE_URL`。#37 保留包的静态/生成合同检查与独立发布构建，
  不把 Registry 服务数据库变成独立包发布的前置；完整 PR CI 已通过后合并，等待新发布结果。
- Core 生产自动路径按 Core version 变化选择。#102 合并后的首发将用既有 workflow_dispatch 交付其精确
  main artifact，确认新 REST 可用后再合入生成的 Release PR，避免 CLI 首发先于 provider；不添加长期依赖 gate。
- runtime #37 合并为 `006759a`；正式发布 run 34832733241 成功。`runtime-core-py-v0.1.3` 的 wheel/sdist 已可下载，
  Core 更新到该发布 URL；锁文件除 content hash 外仅改变这个 package，wheel SHA-256 为
  `613b500183ffd8afa6a6dd560a226a8994e73e24148ad84d37536ec804023075`。
