# Mail Identity and Remote Occurrence

- **Status**: Core occurrence semantics、MVP MAILBOXID support、Source Block provenance placement、canonical Mail relation
  direction/content、Source deletion survival and distinct Source/Block identities/content frozen by D-239–D-244；atomic
  cross-peer creation remains open。
- **Protocol evidence**: [Message Identity Facts](../evidence.md#message-identity-facts)。
- **Correction pressure**: 不把 local Email identity、跨 occurrence reconciliation 与 IMAP remote occurrence
  locator 误认为同一种 identity；但 collection 可以把后两者组织成有明确 scope 的 reconciliation ladder。

## Distinct Concepts

1. **Local Email identity**：`Block.id` 是 InKCre 内唯一无条件成立的 Email identity。
2. **Reconciliation key**：`Message-ID` 是可选的 source-native key，用于 best-effort 判断不同 remote
   occurrences 是否对应同一 particular message version。它缺失时，不发明 content fingerprint。
3. **Remote occurrence locator**：IMAP 操作需要 authenticated message-store/source namespace + mailbox +
   `UIDVALIDITY` + `UID`，用来再次读取或改变一个远端 occurrence。它不是 Email identity 的 fallback。

更稳定的逻辑表达是 `remote mailbox identity + UIDVALIDITY + UID`。`account + mailbox` 只有在 remote account
identity 可知、且 mailbox 确实位于该账号自身 namespace 时，才是 `remote mailbox identity` 的一种 concrete
representation；它不是 Base IMAP 的普遍事实。

## Source / Access-Context Boundary

- Email address 是消息参与者/路由地址，不能证明一个独立 mailbox store；登录名也未必是 Email address。
- Base IMAP 只能让我们确认一个 Source 持有一套 connection/authentication config。一次 authenticated connection
  可以看到 personal、other-user 与 shared namespaces；不同凭据暴露的 mailbox 集合可能重叠。因此撤回“一 Source
  必然对应一个协议可识别账号”的承诺。
- Source instance 只能代表这个 local access context。它不会证明两个 Sources 指向不同 remote account，也不支持
  用 address/password 推导 account identity；credentials 不是 identity。每个 Source instance 在 info-base 中恰好有
  一个 Source Block projection，Mailbox 通过 graph relation 连接该 Block，而不是在 Mailbox content 中嵌入
  `SourceRef` 作为唯一 provenance。
- 即使获得 authenticated-user identity，一个 connection 仍可能暴露 delegated/shared mailbox；这类 mailbox 的
  identity 属于 mailbox/store，而不属于当前登录账号。因而 `account + mailbox name` 不能普遍解决跨 Source merge。
- 当前仍没有足够价值引入 `MailAccount` Block。支持 `OBJECTID` 的服务器可提供更稳定的 `MAILBOXID` / `EMAILID`，
  其中 MVP 已确认消费 `MAILBOXID`；`EMAILID` / `THREADID` 是否进入 reconciliation 是独立 edge。

## UIDVALIDITY Boundary

- `UID` 只在一个 mailbox 的某次 UID epoch 内有意义，不能自证它仍指向原来的 remote message。
- `UIDVALIDITY` 变化后，相同数值的 `UID` 可以指向另一个 message；凡是持久保存 UID 并在以后据此读取/改变远端
  occurrence 的路径，都必须保留并核对它所属的 epoch。
- tuple 的 durable placement 已冻结：Mailbox Block 持有 remote mailbox identity evidence，Email–Mailbox
  membership fact 持有 occurrence-local UID + UIDVALIDITY snapshot；Mailbox–Source Block relation 提供 access/
  provenance path。exact relation direction/content 仍需结合 graph predicate vocabulary 冻结。
- Base IMAP 的安全 concrete fallback 是 Source-scoped mailbox binding + `UIDVALIDITY` + `UID`。如果 adapter 获得
  exact provider-native mailbox identity（例如受支持且可正确限定 server/store scope 的 `MAILBOXID`），多个
  Source-scoped bindings 才能被证明指向同一个 remote mailbox；此时 locator 可自然跨 Source 合并。
- MVP 在 authentication 后执行一次 CAPABILITY，发现 `OBJECTID` 时解析随后 SELECT/EXAMINE 必须携带的
  `MAILBOXID`。不为每个已选择 mailbox 追加 STATUS query。RFC 只保证 MAILBOXID 在 single client login + single
  server hostname 的可见范围内唯一，因此 adapter 必须先证明比较 scope，不能跨任意 Sources 比较 bare value。

## Candidate Collection Reconciliation

- local Email identity 始终是 `Block.id`；`Block.id` 不是 reconciliation rung。
- collection 对一个 fetched message 依次：
  1. 先用当前 Source access context + mailbox + `UIDVALIDITY` + `UID` 查找已知的 exact remote occurrence；
  2. occurrence 未知且存在 `Message-ID` 时，best-effort reconciliation 到已有 Email Block；
  3. 均未命中时创建新的 Email Block，并把本次 occurrence 绑定到它。
- 这条流程保留 locator 的全部实际收益，同时允许一个 Email Block 拥有多个 remote occurrence locators。没有
  `Message-ID`、没有 optional server-native object ID 且 Source/mailbox occurrence 改变时，允许创建重复 Block，
  不引入 content fingerprint。
- 跨 Source occurrence merge 只由 exact mailbox/store evidence 驱动；配置的 mail address、username 或 password
  不充当 proof。缺少这种 evidence 时，`Message-ID` 仍可 reconciliation Email，但不能证明两个 occurrence locator
  相等。

## Canonical Provenance Graph

```text
Source Block --manages--> Mailbox Block
Mailbox Block --contains { UIDVALIDITY, UID }--> Email Block
```

- Mailbox content 不保存 `source`；每个 Source instance 由 `SourceModel.block` 唯一映射到一个 Source Block。
- `manages` 表示当前 Source access context 管理/同步该 Mailbox；可证明为同一 remote mailbox 的 Mailbox Block
  可以连接多个 Source Blocks。
- `contains` 是当前已知 membership fact，其 structured content 同时保存 occurrence-local UID epoch/UID。远端
  membership 消失时删除 relation，不创建历史 tombstone。
- `manages` / `contains` 使用 normalized active direction。反向遍历可以描述为 `managed by` / `contained in`，但
  不为此重复持久化 inverse relations；这是 producer common pattern，不是 Relation validation rule。
- 删除 operational SourceModel 不删除 Source Block、`manages`/`collects` relations 或 collected graph。Relation
  表达 provenance/binding，不证明 live credentials 或 executor；远端操作必须另外解析仍存在的 operational Source。
- `sources.id` 继续拥有 Source identity；`sources.block` 是无独立 sequence/default 的 `NOT NULL UNIQUE` Block FK。
  Relation 始终只是 Block-to-Block；Source producer 读取自己的 `source.block` 并用该 BlockRef 写入 provenance。

## Source Block Contract

- exact resolver ID：`core.source.v1`。
- canonical content：`{ "id": SourceRef, "type": exact Source type, "nickname": string | null }`。
- `nickname` 由 Source Block content 单独拥有，`sources.nickname` 删除；config、state、collect_at 仍只属于 SourceModel。
- Source Block 是否 operationally active 由 unique `sources.block` binding 是否存在派生，不进入 canonical content。
- Source Block 与 SourceModel 的 identity/lifecycle 不同；Source 删除后 content 中的 SourceRef 作为历史 descriptor
  保留，不被新 Source 根据相似 config 自动复用。

## Active Question

冻结兼容 core-py 与 client-web/PostgREST peers 的 atomic Source + Source Block creation command；不得给
`sources.block` 增加独立 sequence，也不得允许 committed Source 缺少 projection。
