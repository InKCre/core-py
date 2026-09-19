# Core 0.2.0 生产交付

当前状态：Core 0.2.0 生产发布及只读核验完成，unit 已按 [D-562](../../decisions/D561-D570.md) 关闭。
Parent task 保持 active，任务资料继续保留。

## 已完成的合并与版本准备

- [PR #100](https://github.com/InKCre/core-py/pull/100) 的最终 head 为 `d7ed6fc`，Preview 和三个 required checks 均成功，
  2026-09-13 01:52:31（Asia/Shanghai）squash 合入 main，提交 `915be5a7751381426d86522df89de9e93b217032`。
- 自动生成的 [Release PR #101](https://github.com/InKCre/core-py/pull/101) 仅将 Core 从 0.1.5 升至 0.2.0，
  生成 changelog 并消费 `.changes/100.added.md`；没有运行代码、依赖或 Extension 版本变更。
  两个待批准的 CI workflow 在审查后获准执行，三个 required checks 均成功。
- #101 于 2026-09-13 01:57:24（Asia/Shanghai）squash 合入 main，发布提交为
  `b3ccb00ca2e235bfcc9b9f4f4cc17948c59ef54a`。

## 生产证据边界

#100 合并后的 [生产 workflow](https://github.com/InKCre/core-py/actions/runs/34709605869) 虽为 success，实际执行
“Core version unchanged” no-op，部署与 stable 接纳步骤均 skipped；它不是本 unit 的生产发布证据。
真正交付必须来自 #101 的 exact-main 发布链，并核对镜像身份、生产探针和 stable 接纳。

[0.2.0 镜像发布](https://github.com/InKCre/core-py/actions/runs/34709745029) 已成功，exact-main 为 `b3ccb00`，
不可变镜像是 `ghcr.io/inkcre/core-py@sha256:0484fea8c37596379b030d3bc3889e7826e84496f2468e1b8d2f65811b89d4fc`。
[对应生产部署](https://github.com/InKCre/core-py/actions/runs/34709831934) 于 2026-09-13 02:04:12（Asia/Shanghai）
成功结束。`Deliver production` 与 `Move production-admitted stable channel` 均为 success，no-op 步骤 skipped。

| 交付对象 | 核对结果 |
| --- | --- |
| exact-main source | `b3ccb00ca2e235bfcc9b9f4f4cc17948c59ef54a` |
| Core Heroku release | `inkcre-core-production`，`v109` |
| PostgREST Heroku release | `inkcre-postgrest-production`，`v50` |
| 转移到 Heroku 的本地镜像 ID | `sha256:687ce554d6875ee667c8327c77b782fa54f1c15e55770e3044650c2b5188648e` |
| stable 推送 digest | `sha256:0484fea8c37596379b030d3bc3889e7826e84496f2468e1b8d2f65811b89d4fc`，与候选镜像一致 |

部署工作流中的数据库 readiness、Core liveness/readiness 和既有 PostgREST 读写/拒绝/探针清理路径通过，
随后才更新 stable。独立公开读回中，Core `/livez` 为 200 / ok（1.303 秒），`/readyz` 为 200 / ready（12.229 秒）。
只读 Job 目录确认七个新的 automatic Organization 类型已出现，原 media interpretation 类型仍在。
发布后 `core.organization.*` 配置仍为空，配置摘要与发布前一致；没有默认启用新行为，也没有新增模型运行。

PR #100 和 Release PR #101 的 Preview 应用清理均成功，数据库分支清理也成功；本机工作目录已切回与发布提交
一致的 main，用户未跟踪的 skill 目录保持未改动。最终 task-control 记录留在当前工作目录，未为关闭记录另开代码
PR；关键交付回执同时记录到已合并 PR。

发布前首次读取生产 PostgREST 的 organization config 收到 503；随后 Core liveness/readiness 均返回 200，
PostgREST 匿名访问返回 401。只读重试已取得配置基线：`core.organization.*` 配置为空；排序后的配置 JSON 的
SHA-256 为 `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`。
Organization Job 目录当时仅有 `core.organization.media_interpretation.v1`。
不把首次 503 推断为特定故障原因，不改生产行为配置、不注入本地语料；发布后只读核对实际状态。

## 交付残余

本轮不重复 Preview 中的真实模型语料验收，也不以生产健康替代语义评审。既有误判、未覆盖输入和同步 SQL
性能限制见 [合并前复审](merge-review.md)。不默认启用 Organization，不承诺整组语义全部正确；parent task
及其其它 units 不因本次发布自动关闭。任务资料按 parent 生命周期保留。

Core 内部实现合同已进入本地 Unit TDD。Hub Product/Product-TDD promotion 没有在本次发布中执行，仍由 active
parent task 保留 owner reconciliation；本 unit 的生产交付完成不代表 program 的 durable-truth gate 已关闭。
