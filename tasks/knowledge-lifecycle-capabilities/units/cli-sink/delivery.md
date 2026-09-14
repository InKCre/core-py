# CLI 按 owner 交付

2026-09-14，Sir 授权自由提交、推送和创建 PR，但明确禁止合并。继续使用 feature → main；不启用 auto-merge，
不从 PR 发布 canonical package，不借授权改写 shared main。没有跨 session 通信。

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

- [ext-reg #35](https://github.com/InKCre/ext-reg/pull/35)：`f22641d`，runtime 0.1.3 候选，等待 review/CI。
- [Hub #25](https://github.com/InKCre/docs/pull/25)：`f84d9ed`，只含两个跨单元合同增量，等待 review/CI。
- Core 源码提交 `a2d2f93`；client-web 源码提交 `83a60ce`，PR 创建后在此补齐链接。

原有 Organization 收尾、共享 packet 中相应旧 delta 和未跟踪 Python skill 保持本地。只有 CLI 对共享
control 文件的行级变化进入本 unit；不为清空工作区提交其它任务。

## 剩余关闭条件

四条本地旅程见 [local-acceptance.md](local-acceptance.md)。它们不替代正式 runtime/Registry 安装、
Core/client-web Preview 与 production、CLI 0.1.0 的 Release PR/PyPI 安装，以及 CLI 消费实际云端冷启动。
PyPI Trusted Publisher 首次配置仍需确认。当前不合并任何 PR。
