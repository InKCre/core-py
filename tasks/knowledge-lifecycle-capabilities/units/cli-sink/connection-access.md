# 本机连接与 Core REST 接入

状态：[D-581/D-582](../../decisions/D581-D590.md) 已确认 JWT 自签、命名连接与选择规则。默认目录按 Sir 建议
位于 `~/.inkcre`，CLI 的具体文件落点为 `~/.inkcre/cli/connections.json`。D-575 的本机/远端配置分离保持不变。

## 本机连接只说明去哪里、用什么凭据

CLI 本地连接的最小数据为 `base_url` 与 `jwt_secret`。它们由 CLI 自己的 Pydantic model 承载，不写入远端
`configs`、`peers` 或 `sinks`。`connection` 管理这份本机数据；`config` 继续操作远端 deployment 配置。

```json
{"base_url":"https://inkcre.example","jwt_secret":"<deployment-jwt-secret>"}
```

这里的地址是 Core REST 入口，不是 PostgREST，也不是 MCP endpoint。CLI 不根据它发现数据库连接后直连，
也不因连接成功就注册为 Peer。配置可以持久化在本机，不强制引入 keychain 或凭据代理。命名连接与本机
配置机制已按 D-582 获批，不意味着源码已实现。

## 命名连接、持久默认与单次选择

一个用户配置文件保存少量命名连接和可选默认名。连接名是本机别名，不是远端 deployment ID、Peer ID
或另一个认证主体。每条连接保存完整的 `base_url` 与 `jwt_secret`；不设置父连接或继承关系。

这一层的收益是让日常 personal、开发/preview 等目标可以明确选择。Agent 不必先修改全局默认值，再执行
业务命令；两个进程选择不同连接时也不需要互相切换默认值。单个命令启动后固定使用解析出的连接，不在
后续 wait 查询或请求中跟随另一个进程对默认连接的修改。

```sh
inkcre-cli connection set personal --input personal.json
inkcre-cli connection set preview --input preview.json
inkcre-cli connection use personal
inkcre-cli --connection preview source list
```

输入文件仍只含该连接的两个字段，name 已经位于 argv。`set` 创建或完整替换同名配置，不递归合并；沿用
`--input`、`--input-json` 和本机可用的 `--schema`。其余配套命令如下：

| 命令 | 效果 |
| --- | --- |
| `connection list` | 离线列出名称、地址与保存的默认选择，不发网络请求 |
| `connection get <name>` | 读取该名称保存的本地配置，不推断远端是否可用 |
| `connection set <name>` | 写入完整连接配置，不把连通性检查作为保存前提 |
| `connection use <name>` | 只修改本机持久默认连接 |
| `connection delete <name>` | 只删除本机记录，不停服务、不删除远端 Peer 或数据 |
| `connection check` | 对本次实际选中的 Core 发出轻量检查，分别报告地址可达/就绪与认证读取的真实结果 |

`check` 不是合法业务调用的前置条件，也不触发 collection/organization。只访问公共 `/readyz` 不能证明
JWT 已通过；应复用一个轻量的受保护读取，准确 route 随 REST 设计落实。检查输出应包含实际使用的 endpoint，
避免仅报告某个别名“成功”。远端休眠时 HTTP 本身可能唤醒它，沿用 D-574，不增加平台专用唤醒逻辑。

默认选择的低风险行为可直接推导：首次创建连接时将其作为默认，之后新增不改变已有默认；显式 `use` 才
切换。删除默认记录时一并清除默认引用，不随机选另一部署。没有选择或名称未知时给出已有名称和缺失信息，
不弹出必须交互的菜单，也不把失败连接自动替换为另一个连接。

## 保存位置与本次覆盖

默认使用 `~/.inkcre/cli/connections.json`。Sir 选择 `~/.inkcre` 作为根目录；`cli/` 是本单元的具体落点，
明确连接文件由独立 CLI 拥有，不替未来完整 Peer 预设配置合同。不跟随工作目录查找项目配置、向上搜索或
自动加载 core-py 的 `.env`。实现可直接使用 `Path.home() / ".inkcre" / "cli" / "connections.json"`，
不需要平台目录依赖或自行实现各平台路径规则。JSON 与 Pydantic 保持不变。

只保留两条独立而直接的选择规则：

| 选择对象 | 从高到低的优先级 |
| --- | --- |
| 使用哪份完整连接文件 | `--connections-file` → `INKCRE_CLI_CONNECTIONS_FILE` → `~/.inkcre/cli/connections.json` |
| 使用其中哪条连接 | `--connection` → `INKCRE_CLI_CONNECTION` → 文件中保存的默认名 |

显式参数优先于环境变量，不因两者同时存在而报错。指定文件是替换本次使用的文件，不与默认文件合并；
命名连接是完整参数组合，当前不增加独立 `--base-url`/`--jwt-secret` 或逐字段环境覆盖。需要临时 endpoint
或凭据时，可以在隔离文件中提供完整组合；这里不添加 env interpolation、凭据引用或 profile registry。

除了 `set/use/delete`，业务命令及单次 `--connection` 选择不写回本机配置。显式连接文件也让脚本能够使用
自己生成的临时配置，不修改日常配置。保存文件的原子替换等实现细节由技术设计处理，不扩大成配置数据库。

## 参考与明确的取舍

GitHub CLI 分别提供主机/凭据环境参数、可覆盖的配置目录与持久账户切换，见
[环境变量](https://cli.github.com/manual/gh_help_environment) 和 [auth switch](https://cli.github.com/manual/gh_auth_switch)。
参考的是持久选择与一次进程上下文分离；不复制其账户层、交互式选择或 Git 目录推断。InKCre 的 Block/Job ID
本身不能指示目标 deployment，因此显式连接名有实际使用价值。

本地 `xiaoland/svc` 的 `svc_cli/src/svc_cli/config.py` 已采用 JSON/Pydantic，但其完整项目配置加 sparse
local overlay 解决的是项目/机器配置组合，不直接搬到这个只有连接参数的 CLI。原提案曾考虑操作系统原生
用户配置目录；D-582 已改为 Human 选择的 home 下 `.inkcre`，因此不再需要为目录定位选择 platformdirs。

## 使用既有 JWT 合同

CLI 在发出受保护的 Core REST 请求时，使用配置的 JWT secret 签发有期限的 token，通过
`Authorization: Bearer <jwt>` 发送。签发属于 CLI 的普通 HTTP 请求层，不分散到每个命令；限时 wait 的
后续查询也由同一请求层签发，不要求 Agent 手动续签。无需 token cache、登录会话或 refresh-token 协议。

现有合同的 authority 是 `app/database_contract/constants.py`、`app/middleware.py` 与
`docs/40-deployment/database-contract.md`：HS256，`role=authenticated`、`iss=inkcre-peer`、
`aud=inkcre-api`，具有合法 `iat`/`exp`，最大生命周期 24 小时。CLI 遵循同一合同，不另造 issuer/audience
或放宽验证。具体签发期限与时钟偏差处理在技术设计中对齐现有客户端实践，不能仅照抄 24 小时作为默认值。

Core router 可以继续使用现有 `require_peer_jwt`。该验证读取 JWT claims，不要求在 peers 表登记调用者。
独立 CLI 使用成熟 JWT 库实现签发，不为调用一个签发 helper 依赖整个 core-py runtime；实际依赖版本在
技术选型时核验。这里复用的是协议合同，不强求不恰当的跨项目源码依赖。

## 认证复用不合并运行角色

CLI 不作为 Peer 的含义是：它不访问数据库、不发布 Peer advertisement、不执行 Peer delegation/Job worker，
也不包含 Core runtime。它仍可使用 deployment owner 提供的同一签名凭据。这些职责边界不自动构成一种
比 Peer 更低的凭据权限；尤其不能把“CLI 不访问 PostgREST”误写成该凭据无法通过 PostgREST 验证。

先前从“CLI 是独立的外部界面”推出“必须有独立 REST token”是不成立的推导。2026-09-13 Sir 明确否决该
提案；不新增 `core.rest_api` 凭据配置、API token 表、签发服务或认证方式切换。已有 MCP PAT 仍由 MCP Sink
拥有，与此次 CLI 决定无关。

现有 semantic/lexical/rumination HTTP handler 还有真实 Peer inbound consumer，DTO/路由调整仍按 D-572
核对；这与是否共用认证方式是两件事。不因 CLI 新增另一套验证依赖或复制 router/领域业务。

## 剩余技术落点

JWT 库、签发期限、HTTP 错误呈现以及配置读写细节仍需技术设计。
本轮按 ponytail 保留一个 JSON 文件、Pydantic 与标准库目录定位，不建 profile 继承、合并框架或认证子系统。
没有修改源码、durable docs 或实际凭据。
