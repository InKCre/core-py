# 验收环境与交付前置

2026-09-14。这里区分已执行的环境/协议探针与未来 CLI 四条旅程；没有把 preflight 当作产品验收。

## 基线与共享开发环境

Core feature base/main 是 `b3ccb00ca2e235bfcc9b9f4f4cc17948c59ef54a`；client-web main 是
`54882ace9634710ff3bfc96a6b521ebe11efaf75`；ext-reg main 是 `3fc45236afcaeaa500f6cef907812a1ac8c2040b`。
后两者本机 checkout 有旧提交或未跟踪内容，实施使用 origin/main 派生的独立 feature 工作位置，不 reset。
Core 当前依赖 released Python Extension runtime 0.1.2；修改 owner 在 ext-reg，不修改 site-packages。

共享开发 target 仍是 SVC instance `b0a97f7ca6abfdf7` / Compose project
`inkcre-core-py-b0a97f7ca6abfdf7`，经 SSH `wsl.win-ws.localhost` 使用声明的 Windows Docker。
最初 execution `8c683d1f-a9f3-4379-99a3-62b9c9fb5ece` 在 SSH key exchange 阶段失败，没有迁移或修改 DB。
恢复后的 execution `505c6a2e-fa00-4ba1-92f9-8ec11ffa13cb` 外层一度返回 child-exit/exit 3 和旧快照，
但随后 execution 日志完成 ensure；重新 status 为 healthy 1/1。以最终直接证据为准，不推断 SVC 内部根因。

当前 Core image 为 `inkcre-core-py-development:b3ccb00ca2e2`，Core/init 对应该镜像，init exit 0。
`http://127.0.0.1:60965/readyz` 返回 200 ready，current/expected migration 都是 `143c4f4adc85`，
roles/privileges/catalog 正常。source fingerprint 为
`b51450cb04ef9d9e92f20930812f0cfc620fbc61587e981d0be944e27e5b6a48`。未 reset/stop 共享 DB 或删除其 volume。

实际 Chromium 149.0.7827.55 从临时 localhost browser origin 带本机开发 JWT 请求声明的 PostgREST
`/jobs?select=id,status&limit=1`，返回 200 和 JSON array。浏览器与临时 HTTP server 已关闭。
这是浏览器到真实持久化的通路证据，不是尚未实现的 browser abort worker 验收。

## 双 Core 与真实 IMAP

为不污染共享库，另建临时 Docker network `inkcre-cli-preflight-m9huov`。所有容器带同名
`inkcre.preflight` label：postgres/init/a/b/imap，另有局部 Registry 探针。Postgres 使用独立 tmpfs。
只使用临时非凭据常量，未复制用户邮箱凭据。Core A/B 使用同一当前 image 和这个独立数据库。

两个 readyz 均 ready，两个不同 Peer 的 lease 均在线；两端都能连接真实 IMAP 并 SELECT INBOX。
A ID 是 `2d525392-6c57-407a-b375-691bef4ef803`，B 是 `084d77b9-ee20-465a-8f46-820463e82d40`。
IMAP 使用官方 `dovecot/dovecot:2.4.4`，digest 为
`sha256:723e3392fe16c6fad8ddc605ea767cc01b4bad9cd9f13eb1dbac15e79c89b2d4`，只在该网络暴露 31143。

实际 pinned image 的 auth 默认值与最新 README 的简单密码示例不一致；本探针在临时 Dovecot 的 conf.d
显式设置 static passdb `password`、允许明文和关闭 SSL，沿已有 Mail harness 的隔离协议场景。
没有改 Mail 产品配置默认值，没有借此新增安全测试。权威以 actual image / doveconf 为准：
[官方 Docker 文档](https://doc.dovecot.org/2.4.4/installation/docker.html)、[官方源码](https://github.com/dovecot/docker)。

## 实际发现：production Extension wheel 缺少 finalization

对 [Mail 0.2.0 Release](https://registry.inkcre.dev/v1/extensions/inkcre/mail/releases/0.2.0) 和 PEP 503 的请求
均成功。Core A 普通 REST 安装返回 200，但 Core B enable 返回 409：
`Registry did not yield exactly one Extension wheel`。

下载的正式 wheel SHA-256 为 `2171fac4b94056401d17dd6df67d22099bdf85a1593635fafe54341dbaaed31e`，
与 Simple 页面一致；ZIP 中有常规 METADATA/entry_points/RECORD，却没有 `dist-info/inkcre-extension.json`。
runtime 0.1.2 和 ext-reg main 均要求此 installed record。

原因在现有 producer 交付链：`scripts/automation/extension_publication.sh` 的 build 直接上传原始 wheel；
`scripts/build_extension_preview.py` 则已调用 `inkcre-ext python wheel finalize`。Toolkit 0.2.1 的该命令
拥有写入 installed record 与重打包的实现。本机对正式 Mail wheel 调用它成功，生成独立候选；没有覆盖或
上传正式 0.2.0。这不是 CLI 输入错误，也不应在 CLI/runtime 添加绕过。

实施计划 P5 增加一处必要接合：production producer 复用同一 Toolkit finalize，保留各 Extension 的 version
authority 和不可变发布；本 unit 本来就需要为 Mail cancellation 修正提供 fragment，使用下一正式版本交付。
共用 publisher 的其它项目也获得同一构建步骤，但不重写已发布 artifact、不擅自给全部项目 bump version。
正式关闭前必须实际安装并启用新发布的 Mail，不能只验证 metadata endpoint 为 200。

候选闭合验证已通过：用 Toolkit 0.2.1 finalize 后的 wheel 构建单 Mail preview inventory，在上述独立网络
用普通静态 HTTP server 承载。Pages 的一条 `_redirects` 被等价静态文件映射承载，目录只读权限显式开放给
容器进程；Core B 的 pip 显式允许该私有 fixture HTTP host。两者只是临时承载条件，不改产品的 HTTPS 发布。
Core A 安装返回 200；B enable 返回 200，enabled[] 只包含 B，config schema 和 sources_types catalog
实际生成。随后将仓库 historical-parent.eml APPEND 到 Dovecot，UID SEARCH / UID FETCH
`BODYSTRUCTURE BODY.PEEK[]` 成功。这证明修复路径和真实材料可用，不冒充尚未编写的 CLI collection 旅程。

## AI 的真实可用性

canonical production 的 ai_providers、ai_models、embedding_profiles、configs 当前为空；不能假设 Preview
自动拥有 AI 配置。共享开发库有 Provider 1 / `core.openai-compatible.v1`，Model 1 `text-embedding-v4`，
Profile 1 dimensions 256。只在内存取其 config，不打印或复制密钥到 packet。

用现有 OpenAI SDK、关闭自动 retry、限定 timeout 发出极小请求：text-embedding-v4 实际返回 256 维；
qwen-plus 返回 403，但 Sir 先前指定的 `qwen3.5-omni-flash` 和 `qwen3-omni-flash` 都成功返回 function tool
call。验收准备采用已成功的精确模型，并在隔离环境明确创建 Provider/Model/Profile/Agent/config；不依赖
production 中不存在的记录，不用这次小请求声称 rumination/semantic retrieval 旅程已通过。

## 云端与正式发布

Core production [run 34709831934](https://github.com/InKCre/core-py/actions/runs/34709831934) 成功，实际
`https://inkcre-core-production-b26009ded782.herokuapp.com/readyz` 返回 200 ready。
PostgREST 唤醒初期一度 503/PGRST002；Heroku 日志显示 03:27:48 UTC 连接 PostgreSQL 17.11，03:27:55
加载 schema cache，之后上述目录 GET 全部 200。这是实测冷启动，不是持久的 migration/CD 故障，未做修复。

最近 Preview application [run 34709745186](https://github.com/InKCre/core-py/actions/runs/34709745186)
成功。CLI 尚无候选 PR，因而没有可声称“CLI preview 已通过”的环境；按原有 PR workflow 创建精确候选
Preview，再跑已批准旅程。IMAP/双 Core 的受控操作留在上述同网络隔离运行时，绝不把 localhost 填给云端 Core。

PyPI Trusted Publisher 尚未验证/配置，这是首次正式发布前的 Human 条件，不是本机编码 blocker。
2026-09-14 公开 PyPI `inkcre-cli` JSON 查询为 404；这不保留名称，也不证明用户发布权限。
目标沿 release-and-distribution.md：InKCre/core-py、cli-publish.yml、production。先交付 Core 新 REST，
再 CLI 0.1.0；不承诺当前已有发布权限，不在 preflight 创建收费服务或执行发布。

## 清理

探针结束后已停止并删除本次带精确 label 的 A/B/Registry/IMAP/init/Postgres 六个临时容器、
其临时 volume 和独立 network。再次 `svc dev status database` 为 healthy 1/1，仍是原共享 Compose project。
本机 ignored 探针目录的结果已归入这些预演页，目录已移入系统废纸篓，可恢复；不把派生 wheel/虚拟环境
或探针升级为测试套件。
