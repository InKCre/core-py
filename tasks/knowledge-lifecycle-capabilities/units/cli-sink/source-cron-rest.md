# Source / Cron 配置与执行接入

状态：2026-09-13 按 [D-588](../../decisions/D581-D590.md) 确认，尚未实施。沿用 D-573/D-575 的管理范围、D-577 的动态输入和 D-587 的
Job 接入。Source 保存来源配置与游标，Cron 保存周期模板，Job 承担一次执行；这些仍是不同对象。

## 普通 REST

| 接口 | 用途 |
| --- | --- |
| GET /source-types、GET /source-types/{type} | deployment 的 Source 类型目录及 config/collect/backfill schemas |
| GET /sources、GET /sources/{id} | Source 列表与详情 |
| POST /sources | 创建 Source 配置，不隐式 collect 或创建 Cron |
| PATCH /sources/{id} | 修改 Source 的可编辑字段 |
| DELETE /sources/{id} | 删除 Source 配置，不删除已收集 graph |
| POST /sources/{id}/collect、POST /sources/{id}/backfill | 创建对应 exact Source Job |
| GET /crons、GET /crons/{id} | Cron 列表与详情 |
| POST /crons、PATCH /crons/{id}、DELETE /crons/{id} | 管理周期模板 |
| POST /crons/{id}/run | 从现有模板立即创建一次独立 Job |

新建配置或 Job 返回 201 与实际记录，读取/更新返回 200 与实际记录，删除返回 204。单条不存在为 404；
列表与 CLI 删除回执沿 D-597 的[共同输出合同](list-error-contract.md)。不重复包 status/result 或另造 command receipt。

## 创建与修改 Source

创建表单为 type、nickname、config、storage；后面三项沿用当前默认 null、空对象、null，并按 Source type
校验 config。CLI 的 --type 仍在 argv，JSON 只填写其余字段。id、timestamps、state、block 不进入该创建表单。
本轮 PATCH 允许 nickname、storage、config，不允许改变 type；不同 Source 实现的 config、cursor 和 graph
含义不同，不将换实现伪装成普通配置编辑。需要另一个 type 时创建另一个 Source，不迁移旧 state。

配置持久化与执行资格分开。类型目录读取 SourceTypesModel 的持久 catalog，保存不要求接入 Peer 已加载
Source class。建议 SourceManager 沿用 JobManager 的现有模式：本地有模型时用它校验/规范化；没有本地
模型时用已持久化的 config_schema 和已有 jsonschema 库校验，执行时仍由实际 Source 模型处理自身合同。
JSON Schema 不能替代所有自定义模型逻辑；这里不声称保存成功证明登录、网络访问或未来 collection 成功。
不把 fallback 校验放在 CLI，不扩大 ConfigContract 为 schema registry 或 JSON Schema 编译器。

Source 管理保持 deployment scope。storage=null 沿用 Source → deployment default → PostgreSQL binary
的既有选择语义；writable catalog/数据库约束继续有效，保存时不要求接入 Peer 实例化并连通目标 Storage。
Source state 由实际 Source 执行维护，PATCH 不清空游标，也不覆盖正在推进的 state。native identity/config
变化与已有 cursor 是否相容仍由该 Source 的既有合同判断，不添加通用重绑定或重置策略。

已有 lazy Source anchor 时，nickname 更新同时经 SourceManager 刷新这个已有 projection；没有 anchor 时
不为改名创建它。配置记录仍是 nickname/type 的 authority，Source Block 只是 graph 中的投影。

## PATCH 只修改提交的顶层字段

两类对象都采用浅层更新：省略的字段保持不变；显式 null 只用于允许空值的字段；提交的对象/数组整体替换，
不递归合并。例如：

```http
PATCH /sources/12
Content-Type: application/json

{"nickname":"工作邮箱","storage":null}
```

这不改变 config 或 state。若提交 `{"config":{…}}`，则提供的是完整的新 config，而不是其中几项；
`{"job_parameters":{…}}` 对 Cron 同理。这样不会留下调用者以为已删除、实际被深层 merge 保留的旧参数。
HTTP 使用普通 application/json 的字段更新合同，不冒称 JSON Merge Patch 的 null 删除语义。

合并与校验由 owning manager 在持久化边界处理，得到有效的完整候选值后只写可编辑字段。复用现有
ConfigContract 的浅层更新思路与 Pydantic 的 exclude_unset，不把表单默认值写回所有未提供字段，不将
整个 ORM 记录 upsert 回去。涉及读取旧配置再合并时沿用 DeploymentConfigManager 的短事务/行锁模式。
这一方案不改变现有 config API 自身的相对更新层级，也不为本 unit 批量重写 client-web 的普通管理表单。

## Cron 是模板，不是 Source 的附属设置

沿用 CronForm：schedule、enabled、job_type、job_parameters、job_timeout_seconds。时区仍由 deployment
的 core.cron 配置提供；enabled 默认 true，job_timeout_seconds=null 使用 Job type 的默认值。
last_job、last_scheduled_for、id 与 timestamps 只读，修改模板不重置调度进度。Cron 的 job_type 可以修改，
更新后完整模板的参数必须满足新类型 schema；不复用 Source 的“不可换 type”限制。

例如 CLI `cron create --job-type core.source.collect.v1 --input cron.json` 中的 cron.json 为：

```json
{"schedule":"*/15 * * * *","enabled":true,"job_parameters":{"source":12,"config":{}},"job_timeout_seconds":300}
```

创建/修改模板应校验 schedule 与对应 Job 参数，不调用 JobManager.create 来做校验或额外生成一个 Job。
从现有 JobManager 参数校验中抽出可复用调用即可；不要求本机 can_handle，不为 backfill 增加 Cron 禁用规则。
不会新增 SourceCollectCronBinding、sources.collect_at，或由 Source 推断自己的周期设置。

CLI cron enable/disable 分别是 PATCH enabled=true/false，不另造 REST action。cron run 则调用
CronManager.run_now：即使 Cron disabled 也可显式运行，不推进 last_scheduled_for，不替换 last_job，
不复用一个已经存在的 Job。它产生的独立工作与周期 Job 可以并存；不因此改变已有周期 occurrence 去重规则。

## 派发与删除的效果

Source collect/backfill 的 body 保持单次 config 本身，timeout_seconds 使用可选 query 参数，两者都返回
创建后的 Job。CLI 增加同义的执行 timeout 选项；它与 job wait 的观察预算分开。默认执行期限继续由 Job type
拥有，Source 缺失/不支持 backfill 等情况由 Source 接入明确报告，而不是靠实例化本地 Source 检查执行资格。

创建 Job 后可用 FastAPI 既有 BackgroundTasks 触发本机 JobManager.check，保留现有手动收集的即时扫描机会。
该扫描是响应后的 best-effort 提示，失败保留日志，不能让已提交的 Job 被报告为创建失败；现有周期 worker
仍是持续发现路径。不在 BackgroundTasks 中承载真正的业务 Job，不增加新的消息队列或调度器。

删除 Source 保留已收集 Blocks/Relations、Source anchor、Cron 模板和历史/在途 Jobs，不隐式 abort 或改绑。
残留模板/Job 仍可能引用不存在的 Source，需要显式编辑、删除或停止；原本依赖该 Source 凭据才能取得的
未物化内容也可能无法再读取。保留 graph 不等于承诺继续访问外部邮箱或文件。管理接口不遍历全图做级联修复。

删除或 disable Cron 只移除/改变未来调度意图，不取消已经创建的 Job；停止现有工作使用 job abort。
调度与删除并发时，已经提交的 Job 同样保留。命令 help 与结果说明这些操作影响的对象，不承诺撤回既有副作用。

## 证据与实施前压力

- app/business/source/main.py 的 create 目前只接受本机 class，缺 Source update/delete；ensure_block 已能刷新
  既有 anchor。这些是预期需要补齐的 owner 方法，不应由新 REST route 直接操作数据库代替。
- SourceTypesModel 已持久化 config/collect/backfill schemas；SourceModel 的 state 与 block 是独立字段。
- app/configuration.py 的 ConfigContract.prepare_patch、DeploymentConfigManager.patch 已有浅层合并与完整校验。
- CronManager 已有 create/update/run_now；现有 update 接收完整表单，新 PATCH 不能直接把缺省字段填入它。
  现有 create/update 只显式校验 schedule，Job template 参数校验需要补齐，但不会产生试运行 Job。
- app/routes/source.py 在提交 Job 后同步 await check；当前提案将这个附带扫描与创建响应分离，保留扫描机会。
- [FastAPI 更新文档](https://fastapi.tiangolo.com/tutorial/body-updates/) 说明 exclude_unset 能区分未提交字段；
  最终模型校验仍由 owner 承担，不能把无校验的 model_copy(update=…) 当作完整候选值验证。

预演仍需核对无本地 Source class 的保存/发现、参数默认值和模型自定义 validator 差异、并发配置/游标更新、
已有/无 anchor 的改名，以及删除后实际的 template/Job/未物化内容表现。已获批的黑盒验收策略不变，未增加
源码、依赖、迁移或自动化测试。python-backend-code 与 ponytail 用于保持普通 HTTP、Pydantic 与既有 owner 边界。
