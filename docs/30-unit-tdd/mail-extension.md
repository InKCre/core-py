# Mail Extension

## Purpose

本文记录 core-py `mail` extension 的稳定本地架构。Mail 保留完整 email client/agent 的长期方向；当前实现边界是
可信的 IMAP collection baseline、canonical Mail graph、read-only solved projection，以及显式 MIME-part
materialization。它不提供 Mail 专用浏览页、compose/send/draft 或后台 IMAP IDLE。

```text
manual/Cron-created typed Job
  -> Mail Source
  -> protocol-neutral Mail adapter
  -> source-owned reconciliation and graph effects
  -> Mail Resolvers
  -> generic InfoBase use

Mail MIME Resolver
  -> same adapter family
  -> writable Storage
  -> semantic content Block + content Relation
```

Hub Product TDD 只拥有 generic Source、Job/Cron、graph、Storage、Resolver、Peer 与 InfoBase route contracts；本文拥有
完整的 Mail-specific product/technical contract，包括 Python package topology、exact IDs、Mail schemas、IMAP
checkpoint policy、graph grammar 与 acceptance boundary。

## Package Topology

```text
extensions/mail/
  __init__.py       extension lifecycle、config defaults、exact Peer inbound
  schema.py         commands、canonical facts、checkpoints、solved projections
  adapter.py        protocol-neutral port、IMAPClient adapter、factory
  source.py         ordinary/backfill Source policy and state advancement
  repository.py     reconciliation ladder and exact graph effects
  resolver.py       read projections and remote MIME materialization
```

`MailProtocol = Literal["imap"]` 是公开协议选择，不是 InKCre adapter ID。`create_mail_adapter(protocol, parameters)`
是唯一 shallow construction seam；每个 Source command 与 Resolver materialization command 使用 fresh async-context
adapter。Adapter 产出 canonical remote facts/checkpoint proposals，不生产 Block/Relation、不持久 state，也不拥有
collection 语义。

## Exact Runtime IDs

- Source type：`extensions.mail.source.Source`；
- Resolvers：
  - `extensions.mail.email.v1`；
  - `extensions.mail.mailbox.v1`；
  - `extensions.mail.email_address.v1`；
  - `extensions.mail.flag.v1`；
  - `extensions.mail.mime_part.v1`；
- remote materialization capability：`extensions.mail.mime_part.materialize.v1`；
- provider route：`POST /mail/mime-parts/materialize`。

Extension config 只拥有新 Source 可继承的 default mailbox exclusion policy。Source 第一次使用时把 null policy
materialize 为自己的 snapshot；后续 extension config 变化不 retroactively mutate existing Sources。

## Source Config And State

Source config separates protocol identity from parameters：

```text
protocol: "imap"
parameters: { host, port, security, username, password }
excluded_mailboxes: { names, special_uses } | null
ordinary_mark_as_seen: boolean
backfill_mark_as_seen: boolean
synchronize_deletions: boolean
```

Source state 只保存 non-secret access binding 与 per-Mailbox ordinary checkpoints。Binding 改变不能静默接续旧
state/graph effects。Checkpoint 由 adapter 解释，Source 决定 accepted-effect boundary 与持久推进时机。

Ordinary collection 默认只接纳 Source creation time 之后的信息；第一次建立 checkpoint 后使用：

1. QRESYNC（可靠 VANISHED + changed flags）；
2. CONDSTORE（changed/new occurrences，无删除证明）；
3. new-occurrence-only。

不以 full mailbox scan 猜 deletion。Backfill 是独立 exact Job type，使用 `[since, before)` date interval，不读取或
写入 ordinary checkpoints，也不被代码禁止进入 Cron。

## Canonical Graph

```text
Source anchor --manages--> Mailbox
Mailbox --contains {uid_validity, uid}--> Email
Email --{role:"body", part_id}--> core.text.v1 / core.html.v1
Email --{role:"inline|attachment", part_id}--> MIME-part metadata
Email --{role, order, display_name}--> EmailAddress
MailFlag --tags--> Email
reply Email --parent:<order> / reference:<order>--> target Email
HTML body --{type:"embeds", reference}--> MIME-part metadata
MIME-part metadata --content--> semantic content Block
```

Email root 只保存 `{message_id,email_id,subject,authored_at}`。Mailbox root 保存
`{name,special_uses,mailbox_id}`。MIME root 保存 source-declared semantic metadata；`part_id` 属于 Email component
Relation，因为它同时表达 MIME-tree location/order 与 exact remote fetch locator。Participants、membership、flags、
references、attachments 与 materialized bytes 不复制进 Email content。

Source anchor 是 Source authority 的 lazy graph projection；`sources.block` nullable unique，projection content 只为
use-time label/text 与 historical readability 服务。

## Identity And Reconciliation

Email reconciliation 是 linear exact ladder：

1. same-Source Mailbox + UIDVALIDITY + UID；
2. comparable cross-Source exact occurrence；
3. scoped EMAILID；
4. Message-ID；
5. create。

每一 rung 都遵守 `zero -> continue / one -> reuse / many -> stop-and-create`。Null identity 可以被后续 exact fact
补全；non-null contradiction 拒绝 reconciliation。弱 Message-ID match 涉及 MIME remote locator 时 lazy-duplicate，
不根据 metadata 猜 UID/part。

Mailbox 永远 Source-scoped，不跨 Source merge。同一 Mailbox/canonical Email pair 至多保留一个 live `contains`；
同 Mailbox duplicate occurrence 创建另一个 Email Block。Plain `tags` 是 canonical best-effort flag projection；完整
FLAGS response 替换当前 observed set。可靠 removal 只删除 exact membership 与相关 tag effects，不删除 canonical
Email graph。

## MIME Materialization

Collection 保存 body content 与 MIME metadata，但不默认下载 attachment/inline bytes。`MailMimePartResolver` 先通过
singular `content` relation 返回任意 existing child；只有缺失且 `materialize_missing=true` 才：

1. 从 MIME part → owning Email → exact Mailbox occurrence → Source anchor 导出 remote locator；
2. 验证 live Source binding；
3. 通过 fresh adapter 读取 exact `part_id` 并 decode transfer encoding；
4. 以 declared media type → byte signature → `core.file.v1` 选择 core Resolver；
5. lock/recheck 后使用 Source effective writable Storage 写 bytes，并提交 child Block + single `content` Relation。

Effective Storage 顺序是 `sources.storage` → deployment `core.source` default → built-in PostgreSQL binary `-4`。
Catalog constraint 保证 explicit Source Storage 类型可写；runtime error 仍可以表达具体 instance unavailable。

client-web 无 IMAP socket，使用 exact Peer capability 请求 provider-local materialization，再从共享数据库/Storage
自行 solve returned child。Provider inbound 调 non-delegating local Resolver path；不建立 generic Resolver delegation。

## Failure And Concurrency Boundary

- Job 是 one-shot envelope，无 retry/attempt；Source 可以逐 Mailbox/occurrence提交 accepted partial graph。
- Ordinary checkpoint 只在 owning accepted boundary 推进；中断后允许重扫并依赖 exact reconciliation。
- Mark-as-seen 发生在 graph commit 后，ordinary/backfill 分别配置。
- MIME materialization 先读 existing child；并发 lock/recheck 尽量避免 duplicate。即使 race 留下多个有效 child，
  solved projection 通过 singular graph read 取一个，Organization 可在以后处理 redundancy。
- Resolver public completion 不暴露 created/reused/race mechanics。Remote unavailable 是 capability failure，不通过
  UID/metadata guessing 降级。

## Verification Authority

阻塞验收使用 repository-owned professional-reading `.eml` corpus、checksum-verified Dovecot 2.4、disposable
PostgreSQL，以及 built client-web/Mail remote：

- J1：ordinary horizon、mailbox exclusions、QRESYNC flags/removals、idempotence；
- J2：exact backfill、ordinary checkpoint independence；
- J3：read-only solve、explicit image materialization、PostgreSQL bytes/local re-solve、unavailable remote outcome；
- J4：GraphSurface/InfoBaseRouter、popup literal back、Mail rendering、HTML isolation/no passive fetch、CID refresh 与 missing
  Block state。

低层 schema/helper tests 不是 Mail 产品有效性的 authority；static checks 保证 mechanical contracts，真实纵向旅程
证明 feature behavior。
