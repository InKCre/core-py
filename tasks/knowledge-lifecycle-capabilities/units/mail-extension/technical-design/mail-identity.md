# Mail Identity and Remote Occurrence

- **Status**: D-263 freezes the complete linear Email reconciliation ladder；D-264 freezes zero/one/many candidate behavior
  under D-262's same-Mailbox guard；D-265 freezes identity completion/contradiction behavior；D-266 restores reference-anchor
  creation and later completion under the same locate/reuse model。This identity edge is closed for implementation planning。
- **Protocol evidence**: [Message Identity Facts](../evidence.md#message-identity-facts)。
- **Correction pressure**: 不把 local Email identity、跨 occurrence reconciliation 与 IMAP remote occurrence
  locator 误认为同一种 identity；但 collection 可以把后两者组织成有明确 scope 的 reconciliation ladder。

## Distinct Concepts

1. **Local Email identity**：`Block.id` 是 InKCre 内唯一无条件成立的 Email identity。
2. **Authored/server evidence**：`Message-ID` 表达 authored message-version identity；`EMAILID` 表达可选
   server-native immutable-content identity。D-262 允许它们帮助一个新 locator 选择 canonical Email endpoint，
   D-263–D-265 已冻结 exact scope、precedence、cardinality 与 compatibility behavior。
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
  用 address/password 推导 account identity；credentials 不是 identity。一个 Source instance 在首次需要 graph
  provenance 时拥有至多一个 lazy Source Block anchor；Mailbox 通过 graph relation 连接该 Block，而不是在 Mailbox
  content 中嵌入 `SourceRef` 作为唯一 provenance。
- 即使获得 authenticated-user identity，一个 connection 仍可能暴露 delegated/shared mailbox；这类 mailbox 的
  identity 属于 mailbox/store，而不属于当前登录账号。因而 `account + mailbox name` 不能普遍解决跨 Source merge。
- 当前仍没有足够价值引入 `MailAccount` Block。支持 `OBJECTID` 的服务器可提供更稳定的 `MAILBOXID` / `EMAILID`；
  MVP 消费 `MAILBOXID` 支持 owning Source 内的 rename continuity，并将 optional `EMAILID` 保存为 Email
  content evidence。D-262 允许 EMAILID 参与 best-effort canonical reconciliation，但不自动证明任意 Sources
  之间的 comparison scope；`THREADID` 仍不采集。

## UIDVALIDITY Boundary

- `UID` 只在一个 mailbox 的某次 UID epoch 内有意义，不能自证它仍指向原来的 remote message。
- `UIDVALIDITY` 变化后，相同数值的 `UID` 可以指向另一个 message；凡是持久保存 UID 并在以后据此读取/改变远端
  occurrence 的路径，都必须保留并核对它所属的 epoch。
- tuple 的 durable placement 已冻结：Mailbox Block 持有 remote mailbox identity evidence，Email–Mailbox
  membership fact 持有 occurrence-local UID + UIDVALIDITY snapshot；Mailbox–Source Block relation 提供 access/
  provenance path。D-241/D-257 已冻结 exact direction/content 为
  `Source --manages--> Mailbox --contains {type:"contains",uid_validity,uid}--> Email`。
- Base IMAP 的安全 concrete fallback 是 Source-scoped mailbox binding + `UIDVALIDITY` + `UID`。如果 adapter 获得
  exact provider-native mailbox identity（例如受支持且可正确限定 server/store scope 的 `MAILBOXID`），它可以
  支持当前 Source 内的 Mailbox rename continuity。D-248 仍保留 Source-scoped Mailbox Blocks；D-262 允许不同
  Mailboxes 的 occurrence locators 指向同一 canonical Email，但不因 bare provider value 自动跨不可比 Sources
  merge，也不合并同一 Mailbox 内的多个 live UIDs。
- MVP 在 authentication 后执行一次 CAPABILITY，发现 `OBJECTID` 时解析随后 SELECT/EXAMINE 必须携带的
  `MAILBOXID`。不为每个已选择 mailbox 追加 STATUS query。RFC 只保证 MAILBOXID 在 single client login + single
  server hostname 的可见范围内唯一，因此 adapter 必须先证明比较 scope，不能跨任意 Sources 比较 bare value。

## Collection Identity and Canonical Reconciliation

- local Email identity 始终是 `Block.id`。`(Source-scoped Mailbox Block, UIDVALIDITY, UID)` 是 exact occurrence
  idempotency 与 remote-access authority；它不等于 canonical Email identity。
- 已知 exact locator 必须复用其现有 `contains` Relation 与 Email endpoint。对于未知 locator，Collection 才使用
  source-native identity evidence best-effort 选择或创建 canonical Email；不使用 content fingerprint。
- 多个 Mailboxes 的 locators 可以指向一个 canonical Email；同一 Mailbox 内的第二个 live UID 即使匹配 canonical
  evidence 也创建另一个 Email Block。这样 Mailbox-scoped ordinary flag Relations 仍能精确映射 occurrence-local
  mutable facts。
- UIDVALIDITY reset 使旧 epoch locators 失效；后续收集重建 occurrence Relations，并通过 D-263–D-265 的 canonical
  reconciliation rule 选择现有或新的 Email endpoint。它不因 UID epoch 改变而必然复制 canonical Email。
- D-260 temporarily superseded canonical reconciliation but did not erase its decision lineage。D-261/D-262 restore the
  earlier ladder；do not redesign already accepted rungs merely because the current projection had called them pending。

## Recovered Accepted Ladder and Narrow Delta

The accepted D-239/D-248/D-256 order before D-260 was：

1. **Known local occurrence**：same Source-scoped Mailbox + UIDVALIDITY + UID reuses its bound Email endpoint。This is
   idempotency，not logical fallback。
2. **Comparable exact remote occurrence**：when the adapter can prove comparable OBJECTID/server-login scope，the same
   MAILBOXID + UIDVALIDITY + UID observed through another Source-scoped Mailbox reuses that Email endpoint。
3. **Message-ID**：a valid semantic Message-ID is the best-effort logical Email reconciliation rung。It may also identify
   an incomplete reply/reference anchor created before content collection。
4. **Create**：without usable exact/logical evidence，create another Email Block；do not use a content fingerprint。

D-262 adds one eligibility guard to every cross-occurrence rung：a candidate already connected to the current Mailbox by a
different live UID is ineligible，so the new occurrence safely creates or selects another Email Block。

The only identity rung not present in that earlier ladder was optional OBJECTID EMAILID，which D-260 later added to Email
content。D-263 freezes it after exact occurrence matching and before Message-ID，because within a proven OBJECTID namespace
it is a server assertion of identical immutable message content and survives COPY/MOVE，while Message-ID is authored
best-effort evidence。Bare EMAILID remains incomparable across arbitrary Sources。

The resulting exact ladder is therefore `known local occurrence → comparable exact cross-Source occurrence → scoped
EMAILID → Message-ID → create`。It remains linear：the first usable rung wins，without scoring、cross-rung voting or content
fingerprints。D-264 defines one rung as zero → continue、one → reuse、many → stop and create；contradictory facts remain a
separate compatibility check，not a new identity level。

## Exact-One Resolution

- Apply comparison scope and D-262's current-Mailbox eligibility guard before counting candidates。
- Zero means this rung found no existing endpoint；continue to the next rung。One means reuse。More than one means the value is
  non-unique in the current scope；stop reconciliation and create another Email Block。
- Do not select by persistence accident such as minimum/oldest Block ID，and do not use a weaker rung to vote among stronger
  ambiguous candidates。The identifier value can remain evidence even when it cannot authorize reuse。
- This is the Collection shallow outcome because the observed occurrence still requires an Email endpoint。Reference-only
  observations use the same locate/reuse safety rule and create an incomplete Email on zero or ambiguity per D-266。

## Identity Compatibility After Exact-One Location

- For `message_id` and scope-comparable `email_id`：existing null is filled by an incoming non-null fact；incoming null does
  not erase an existing fact；equal non-null values are compatible。
- Different non-null comparable identity values reject a cross-occurrence reconciliation candidate。The newly observed
  occurrence gets another Email endpoint；Collection neither overwrites the old identity nor falls through to weaker rungs。
- EMAILID and Message-ID cross-check one another only where their comparison scope makes that meaningful。In particular，
  bare EMAILID values from adapter-unproven scopes neither match nor contradict one another。
- A known/comparable exact occurrence locator is a stronger remote-occurrence authority，not a logical reconciliation
  candidate。Identity conflict on that exact path does not fork the occurrence；it exposes a producer/data-integrity
  inconsistency and must not be hidden by destructive overwrite。
- `subject` and `authored_at` are not identity evidence。Their completion/update policy remains separate and cannot silently
  turn into content-fingerprint reconciliation。

## Future Ladder Utility Boundary

The repeated mechanics now justify a Source-domain utility，subject to implementation preflight：ordered async rung
execution、scope-filtered candidate cardinality、short-circuiting and rung-labelled typed outcomes。Mail adapter logic still
owns candidate queries、OBJECTID comparison scope、same-Mailbox eligibility、identity compatibility and the decision to
create an Email。Other Sources likewise own their evidence semantics and command effects。The shared utility must not own a
universal identity ladder or hide domain policy behind callbacks so generic that the abstraction has no meaningful contract。

## Canonical Provenance Graph

```text
Source Block --manages--> Mailbox Block
Mailbox Block --contains { UIDVALIDITY, UID }--> Email Block
```

- Mailbox content 不保存 `source`；每个 Source instance 由 `SourceModel.block` 唯一映射到一个 Source Block。
- `manages` 表示当前 Source access context 管理/同步该 Source-scoped Mailbox；每个 Mailbox Block 恰有一个
  Source Block provenance path。即使另一 Source 暴露相同 remote mailbox，也保留另一个 Mailbox Block。
- `contains` 是当前已知 membership fact，其 structured content 同时保存 occurrence-local UID epoch/UID。每个
  exact locator 只有一条 live occurrence Relation；不同 Mailboxes 的 locators 可以共享 canonical Email endpoint，
  但一个 Mailbox/Email pair 至多一条 live Relation。远端 membership 消失时删除 exact relation，不创建历史
  tombstone。
- `manages` / `contains` 使用 normalized active direction。反向遍历可以描述为 `managed by` / `contained in`，但
  不为此重复持久化 inverse relations；这是 producer common pattern，不是 Relation validation rule。
- 删除 operational SourceModel 不删除 Source Block、`manages`/`collects` relations 或 collected graph。Relation
  表达 provenance/binding，不证明 live credentials 或 executor；远端操作必须另外解析仍存在的 operational Source。
- Mailbox Block 永久保持 Source-scoped：每个 Mailbox 只有一个 `manages` 来源；不同 Sources 即便暴露同一个 remote
  mailbox 也保留不同 Blocks。MAILBOXID 在一个 Source 内支持 Mailbox rename continuity；EMAILID remains Email
  content evidence and may participate in D-262 canonical reconciliation only under an explicitly supported comparison
  scope。
- `sources.id` 继续拥有 Source identity；`sources.block` 是无独立 sequence/default 的 nullable `UNIQUE` Block FK。
  Relation 始终只是 Block-to-Block；Source producer 读取自己的 `source.block` 并用该 BlockRef 写入 provenance。

## Source Anchor Contract

- exact resolver ID：`core.source.v1`。
- canonical content：`{ "id": SourceRef, "type": exact Source type, "nickname": string | null }`。
- `sources.block` 是 nullable unique Block FK。Source 可以在尚未需要 provenance endpoint 时没有 anchor；首次
  producer 写入 `collects`/`manages` 前由 SourceManager 并发安全地创建并绑定，之后不替换。
- SourceModel 始终拥有 id、type、nickname、config、state、collect_at；Block content 中的 id/type/nickname 只是为
  resolver `get_label/get_text` 与 Source 删除后的历史可读性服务的 projection，不接管 authority。
- Source Block 是否 operationally active 由 unique `sources.block` binding 是否存在派生，不进入 canonical content。
- Source Block 与 SourceModel 的 identity/lifecycle 不同；Source 删除后 content 中的 SourceRef 作为历史 descriptor
  保留，不被新 Source 根据相似 config 自动复用。
- `SourceManager.ensure_block(source, session)` 锁定 Source row，在同一 caller transaction 内创建或复用 anchor，
  并让 `{id,type,nickname}` projection 与本次观察到的 SourceModel 一致。该 postcondition 不另加 `refresh` 参数；
  Resolver label/text 只读 Block content。

## Canonical Mailbox Content

- exact resolver ID：`extensions.mail.mailbox.v1`。
- exact content：

  ```json
  {
    "name": "Sent",
    "special_uses": ["\\Sent"],
    "mailbox_id": "F123456"
  }
  ```

- `mailbox_id` 可为 null。它只在 owning Source 内支持 rename continuity；D-248 已永久禁止跨 Source 合并
  Mailboxes，且 `Source --manages--> Mailbox` 已提供 comparison/access scope，因此不复制 host/port/username。
- `special_uses` 是去重、稳定排序后的 adapter-understood standards-backed user-role attributes。保留例如
  `\\Sent`、`\\Drafts`、`\\Junk`、`\\Trash`、`\\Archive`；不保存 generic subscription、selectability、child hints、
  transient marked state 或 unknown extension attributes。
- 不包含 SourceRef（由 `manages` relation 表达）、UIDVALIDITY（属于 `contains` occurrence）、LIST delimiter、generic
  attributes、message counts、namespace classification 或派生 path。Source 可以在 discovery/config filtering 时临时
  使用这些 protocol facts，而不复制到 info-base。
- `get_label()` 返回当前 mailbox name；`get_text()` 只投影 name 与 recognized special uses。
- **Status**: D-249 的较宽 shape 已由 D-258 收窄。

## Mailbox Occurrence Relation

One current remote occurrence is a Mailbox → Email Relation whose content is canonical compact JSON：

```json
{
  "type": "contains",
  "uid_validity": 3857529045,
  "uid": 42
}
```

- `uid_validity` and `uid` are required positive IMAP integers and jointly identify the occurrence within the Source-scoped
  Mailbox。
- A Mailbox/Email pair has at most one live `contains` Relation。When another UID in the same Mailbox matches the same
  canonical evidence，Collection creates another Email Block；cross-Mailbox locators may still share one endpoint。The
  Relation remains the exact external locator and remote-access authority。
- Reliable remote removal deletes only the exact matching occurrence Relation。No tombstone or Email deletion follows；a
  mailbox move is removal of the old occurrence plus addition of the new occurrence。
- On UIDVALIDITY change，all old-epoch occurrence locators for that Mailbox are invalid。The Source deletes those stale
  Relations、resets its permitted sync cursor/validator state and incrementally rebuilds current occurrences through
  ordinary bounded collect jobs；it does not retry or require one job to finish the mailbox。
- `INTERNALDATE`、`EMAILID` / `THREADID`、flags、mailbox sequence numbers and message body/content do not enter this
  Relation。EMAILID persists in Email root content as optional server evidence；all durable flags use separate plain
  MailFlag Relations whose owning Mailbox and unique Mailbox/Email membership derive the locator；UIDVALIDITY + UID remains
  the remote-access authority。
- **Status**: D-257 locator/reset retained；D-262 permits cross-Mailbox endpoint reuse while rejecting same-Mailbox
  multiplicity，superseding both D-260's global non-reconciliation and D-261's locator-qualified flags。

## Reply / Reference Anchor Resolution

- A parsed Message-ID resolves eligible Email candidates。Exactly one is reused；zero or more than one creates a new ordinary
  Email Block containing only that Message-ID and null remaining root facts。
- Creating on ambiguity preserves the exact authored reference without falsely selecting one candidate or multiplying the
  relation across all candidates。The accepted cost is bounded best-effort duplicate anchors，not incorrect graph facts。
- Later Collection applies the same D-263–D-265 path。One compatible anchor is completed in place and retains inbound
  Relations；multiple anchors remain ambiguous and therefore do not authorize mutation of any one of them。
- “Incomplete anchor” is not persisted state or a separate resolver/lifecycle。It is an ordinary Email whose currently known
  content/graph is sparse。

## Status

Mail identity、occurrence、canonical reconciliation and reference-anchor behavior are frozen through D-266。Reopen only for
implementation evidence or a new product use path，not for speculative deduplication completeness。
