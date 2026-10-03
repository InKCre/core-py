# client-web 第一批观测实现与验收

2026-10-03，分支 `codex/observability-foundation`。此报告属于父任务，不建立第二控制权。
子工作未 commit/push，未改 shared 挂载或生成数据库协议文件；候选生成类型由 primary 写入。

## 交付面

`packages/core/src/obsrv/telemetry.ts` 集中拥有标准 OTel SDK 的三信号初始化、公开配置校验、
有界排空、W3C SDK carrier 与 Span Link、固定元数据事件和低基数操作耗时。
连接本地 `telemetry_enabled=false` 是唯一启用开关。关闭不读共享观测配置、不启 provider，
默认 Job INSERT carrier 为 null。没有出口时保留固定原因本地诊断而不启 SDK。

`telemetry_peer_relay_url` 为空时使用共享完整 per-signal public URL 且不发送 Peer JWT；
显式设置时追加 `/v1/traces`、`/v1/logs`、`/v1/metrics`。SDK 的标准 async headers factory
通过现有签名 authority 生成短期 Peer JWT，捕获初始化时的连接，不能把旧批次绑定到后来
切换的 secret。没有 SaaS 私密 token 字段，没有隐式 relay 推导、失败回退或新增常驻服务。

PeerManager 的异步选择 context 显式传给 PeerHTTPOutbound，后者负责一次 W3C 注入。
开启态拒绝所有 Peer 重定向以守住配置 endpoint 边界，错误仍是原来的
`PeerOutcomeUnknown` 且不重试；关闭态保留原 fetch 跟随行为。PostgREST 仅作本地 client
span，不注入 W3C，也不声称有 server/SQL span。无全局 fetch/Promise patch。

Job 创建同 INSERT 写 carrier；执行成功 claim 后独立 trace Link 提交，所有 claim 分支
共用执行观测。claim/close 不覆盖 submission 列。`job.submitted`、`job.started`、
`job.closed` 事件来自持久化边界。失败、超时、取消的 metric outcome 独立于 trace 导出状态，
不会因捕获业务错误后返回而记成功。原 PG 日志、任意业务错误 message 和结果 state 保留原
路径，不桥接到新增 OTLP。Job 页仅增加可选诊断基础链接，以 Job ID 查询。

SPA 生命周期、设置保存/导入、重置和关闭已接入。设置控件使用安装的 UI 2.2.1 规范。
默认关闭和空 relay 已在生产构建浏览器页面验证，截图见 `client-settings.png`。

## 实际验收

执行：在 client-web 下运行 `pnpm exec node ../core-py/tasks/observability-foundation/experiments/client-browser.mjs`。
脚本依赖 parent 创建的 disposable `o11y_impl` PostgreSQL/PostgREST（loopback 33000），
只从忽略的 0600 `runtime/database-credential.json` 读取合成 JWT secret，不输出它。
它临时改写公共 `inkcre.observability` 出口，保留 deployment ID，并在 finally 恢复原
schema/value；运行前须与 parent 协调该 key 的独占使用。不能对共享 dev/preview 运行。

最新 `client-browser-result.json` 记录 Chromium 149.0.7827.55、74 spans 和三个 OTLP/HTTP protobuf
信号。合成 Job 主样本 67、68、72，另有错误/取消/超时样本。实际断言覆盖：

- 关闭态不读取共享配置，Job carrier 为 null；正常 lifecycle 开启读取公共配置。
- 两条并发原生 await 链显式 context 隔离，Peer HTTP 实际收到正确 traceparent。
- 真实 Job INSERT、claim、close 和 off→on / on→off 组合保留列与终态，执行独立 root Link。
- 无效 carrier 被 SDK 忽略，未采样标志保留；SDK API set 构造超过 512 bytes 的 tracestate 后，应用省略可选字段。
- 双 origin 真 HTTP 重定向第二端收到零请求，not-executed 与可读 HTTP 500 的业务语义不变。
- 完整三信号和 metrics-only 的 Job error/timeout/cancelled 与 HTTP 500 error 标签一致。
- 新增 OTLP 不含请求 body/query/异常 message 的合成 sentinel，公开出口不带 Peer JWT。
- 中转三信号的动态 JWT 通过真实密码学验证；修改全局连接 secret 后旧 provider 仍用捕获的原 secret。
- 不可达出口不影响业务返回，flush/shutdown 有界；页面退出仍只 best effort。

这使用真实浏览器、SDK、PostgREST 和本地 OTLP HTTP 接收端，不冒充 Grafana Cloud
账号、远端保留、查询或限额已通过。真实 core-py relay 联调见下节。

## 真实 core relay 联调

`client-real-relay.mjs` 在真实 Chromium 中读取未改写的共享配置，使用官方 protobuf
exporter 发送合成元数据到 `http://127.0.0.1:35501/telemetry`。relay 来自实际 core-py
应用进程，只有其上游是本地合成 OTLP 接收端。`client-real-relay-verify.py` 通过标准
生成的 protobuf 消息解析上游落盘数据，结果在 `client-real-relay-result.json`。

三信号的 SDK protobuf 请求和响应均为 200；缺失/无效 Peer JWT 均 401，带合法 JWT 的
JSON 请求为 415。接收端证实服务器私密合成 ingest 认证正确，浏览器没有持有它。
提交与执行两个 Trace ID、两个 Span ID、独立执行 trace 的提交 Link 原值逐项一致；
Link sampled 标志保留，两个 Job 事件的 Trace/Span ID 与 Job ID 正确，metric label
仅操作名与结果，资源部署/Peer/实例身份齐全。该脚本不改共享配置、不使用 Cloud。

联调实际捕获并修复了两个缺陷：Python 的可选配置字段会序列化为 null，TS 现已同时
接受缺省与 null；泛用 ProtoJSON 解析会把 OTLP JSON 的 hex ID 当作 Base64，曾生成
错误长度的 ID。最终选择官方 OTLP/HTTP protobuf exporter，core relay 仅接受 protobuf，
删除该 JSON 转换责任，并用精确 ID 与 Link 比较替代仅检查 HTTP 200。

## 检查与剩余边界

`pnpm lint`、全 workspace `pnpm type-check`、`pnpm build`、portable package check 均通过。
所有 tracked 文件及新增 telemetry.ts 的 oxfmt 检查和 `git diff --check` 通过。
完整 `pnpm check` 在格式阶段被用户原有未跟踪
`.agents/skills/vue-ts-code/{SKILL.md,scripts/audit.mjs}` 阻塞；按委派要求保留原状，未改或删除。

浏览器扩展、第三方 native extension handler 内部和任意 provider 原生 await 不自动继承
Job 执行 context；首批不改全仓 target、不引 Zone、不声称完整执行调用树。
Webext 仅获得共用配置的默认关闭字段，尚未接入其独立宿主遥测生命周期。
发布前需从正式获准 core artifact 重跑既有 database contract 同步；本轮生成列是 primary
从 candidate migration `3d9593b0c855` 的实际隔离 schema 生成，不能冒充 stable release 已准入。
