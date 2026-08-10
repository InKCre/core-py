# Canonical Email and Graph Boundary

- **Status**: Email schema/body/component graph and participant graph frozen through D-266；best-effort canonical Email uses
  the complete linear reconciliation ladder、one live occurrence per Mailbox/Email pair、exact-one reuse and
  non-destructive identity compatibility；reply/reference anchors now follow the same locate/reuse-or-create model。
- **Protocol/code evidence**: [Message Content and Envelope Facts](../evidence.md#message-content-and-envelope-facts)。
- **Resolver**: retain exact ID `extensions.mail.email.v1`；old schema/behavior is not a compatibility authority。

## Canonical Email Root Content

```json
{
  "message_id": "1234@local.machine.example",
  "email_id": "M6d99ac3275bb4e",
  "subject": "Saying Hello",
  "authored_at": "1997-11-21T09:55:06-06:00"
}
```

- `message_id`、`email_id`、`subject`、`authored_at` are nullable。Do not reject malformed/draft messages merely
  because one is absent。
- `message_id` stores the semantic msg-id without surrounding CFWS/angle brackets。`email_id` stores the bare server-native
  OBJECTID EMAILID when available。Both are authored/server identity evidence useful to reference/use；D-263 places scoped
  EMAILID before Message-ID in best-effort reconciliation。D-264 owns candidate cardinality；neither field receives a
  database uniqueness constraint。
- `authored_at` means RFC 5322 origination time。Never synthesize it from collect time、Block.created_at、IMAP
  INTERNALDATE or local clock；those are different facts/lifecycles。
- This root is the Email's intrinsic scalar/header content needed for identity、label and chronology。It is not a wire
  archive and does not copy every arbitrary/transport header。An empty-body message is still collectible。

## Source-Native Body Graph

```text
Email Block
  ├─ role-bearing relation ─> core.text.v1 semantic content Block
  ├─ role-bearing relation ─> core.html.v1 semantic content Block
  └─ attachment/inline relation ─> Mail MIME-part metadata Block
                                    └─ content ─> core.<semantic-kind>.v1 Block (when materialized)
                                                     └─ Storage pointer -> bytes
```

- Decoded authored plain-text and HTML alternatives are independent Blocks。Their exact resolver already expresses content
  semantics；the relation expresses that the Block is one representation/body of this Email。
- Do not add `extensions.mail.text_body.*` / `html_body.*` metadata wrappers。Reuse of the core deep modules is supporting
  evidence，while independent semantic/use value remains the actual decomposition reason。Future independently valuable
  native metadata must justify its own Block rather than changing body-content authority。
- Attachment and non-text inline MIME parts do have independent protocol facts before bytes exist，so collection creates
  Mail-owned metadata Blocks for them。D-259 places their Email-relative MIME-tree `part_id` on the owner Relation rather
  than intrinsic Block content。
- A pure multipart container is not automatically a Block。It earns representation only when its ordering、alternative/
  related grouping、disposition or another structure fact is required by a real renderer/retrieval/materialization path。

## Graph-Owned Facts

- EmailAddress Blocks and directional originator/destination relations own From、Sender、Reply-To、To、Cc and Bcc。
- Email-to-Email relations/unresolved-reference representation own In-Reply-To and References。
- Source/Mailbox relations own provenance and membership occurrence facts，including UIDVALIDITY/UID。IMAP INTERNALDATE is
  intentionally not persisted absent a proven use path；Source may consume it transiently for collection bounds。
- Mailbox-scoped MailFlag Blocks and plain `tags` Relations uniformly own `\Seen`、`\Answered`、`\Flagged`、`\Deleted`、
  `\Draft` and observed keyword state。The owning Mailbox plus its unique Email membership derives the exact occurrence；
  behavior differs，but persistence shape does not。Deprecated `\Recent` is excluded。
- Attachment/inline-part metadata Blocks and relations own MIME component role/tree position、filename、declared media type、
  description、content labels、encoded size and later materialized semantic content links。
- Therefore root content excludes `uid`、`has_attachments`、body representations、participants、reply/reference IDs、flags、
  mailbox、Source and attachment arrays。Their presence there would create duplicate authority or a domain god object。

## MIME Component Relation Grammar

| From | To | `relation.content` | Meaning |
| --- | --- | --- | --- |
| Email | `core.text.v1` / `core.html.v1` | `{role:"body", part_id:"1.1"}` | selected authored body at this MIME-tree position |
| Email | Mail MIME-part metadata | `{role:"attachment", part_id:"2"}` | attachment at this MIME-tree position |
| Email | Mail MIME-part metadata | `{role:"inline", part_id:"1.2"}` | inline component at this MIME-tree position |

`part_id` is a canonical numeric MIME-tree path relative to the owning Email。It identifies the component position、preserves
source order and maps directly to IMAP section fetch；compare parsed numeric path segments rather than lexicographic strings。
It replaces each earlier independent role order，so there is one structural-order authority。`(Email Block, part_id)` is the
bounded identity；MIME-part Blocks do not reconcile globally by this value。No MIME tree table/container Blocks are introduced。

When collected HTML contains a reference resolved to a MIME part，Collection also creates an exact HTML body → MIME-part
metadata Relation：`{type:"embeds", reference:"<authored URI>"}`。Content-ID/Content-Location remain intrinsic target
labels；the Relation owns the contextual reference occurrence and enables rendering/navigation without graph lookup guesses。

## Canonical MIME-Part Metadata

- exact resolver ID：`extensions.mail.mime_part.v1`。
- exact content：

  ```json
  {
    "media_type": "image/png",
    "charset": null,
    "filename": "logo.png",
    "content_id": "logo@example.com",
    "description": "Company logo",
    "transfer_encoding": "base64",
    "encoded_size": 18342,
    "content_location": null
  }
  ```

- `part_id` is required on the owning Email Relation，not in this content。The MIME-part Resolver obtains its exact fetch
  locator from that relation；the metadata Block owns only facts intrinsic to the MIME body part。
- `media_type` is the normalized effective MIME type reported/defaulted by BODYSTRUCTURE；the Mail extension owns later
  resolver-classification policy。IMAP returns body type/subtype separately while MIME names their normalized `type/subtype`
  value a media type；this field is not byte-signature evidence。
- `charset` is the optional normalized MIME charset promoted from content-type parameters。It is independently required to
  transcode materialized text/HTML into the semantic resolver's supported encoding；this does not justify retaining every
  arbitrary MIME parameter。
- `disposition` is excluded after collection classifies the usable role into the owning Relation。Persisting the source wire
  value as well would duplicate authority without another accepted consumer。
- `filename` is the optional canonical filename selected by the adapter from disposition/content-type parameters；raw
  parameter bags are not copied merely for wire fidelity。
- `content_id` stores the semantic ID without surrounding angle brackets；`content_location` retains the normalized
  source-authored body-part label。`description` is decoded MIME-authored semantic description，not generated summary，and
  contributes to label/text/retrieval before bytes are materialized。
- `transfer_encoding` is nullable at the canonical level but the IMAP adapter records BODYSTRUCTURE's effective value so it
  can decode a `BODY[section]` response when decoded `BINARY` fetch is unavailable。`encoded_size` is nullable、non-negative；
  for IMAP it is BODYSTRUCTURE's transfer-encoded octet count，not actual decoded byte size。
- Exclude BODYSTRUCTURE MD5、language、line count、arbitrary parameters and disposition timestamps until a real use path
  earns them。Exclude checksum/detected MIME/decoded size/dimensions/duration because those are byte-derived Resolver facts。
- On materialization，the metadata resolver uses `media_type` through ResolverManager，writes decoded bytes through a
  configured WritableStorage and adds one `content` relation to the exact core semantic content Block。
- **Status**: D-253's wider shape and D-252's role-order strings are superseded by D-259。

## Canonical EmailAddress

- retain exact resolver ID `extensions.mail.email_address.v1`。
- exact content：`{"address":"Local.Part@example.com"}`。
- EmailAddress Blocks reconcile across messages and Sources by exact canonical addr-spec because that shared graph entity
  has concrete navigation/retrieval value。A display name is not part of this Block's content or identity。
- Canonicalization parses one valid addr-spec、preserves local-part Unicode/case、normalizes equivalent quoted forms to the
  minimally quoted serialization，and stores a lowercase IDNA A-label DNS domain；address literals retain a canonical
  bracketed representation。It applies no Unicode normalization to the local part。Do not strip plus tags、fold dots or
  apply provider-specific alias policy。
- Message-authored display name and participant role/order belong to the Email → EmailAddress Relation。This prevents
  `Alice`、`Support` and no-name occurrences from competing for one Block property while retaining the useful shared address
  node。
- `get_label()` / `get_text()` use the address only。Solved Email rendering gets the contextual display name from the
  participant Relation rather than mutating or looking up a preferred global name。
- From、Sender、Reply-To、To、Cc and Bcc are all Email participant facts represented by EmailAddress Blocks plus directional
  Email → EmailAddress Relations。None is copied into Email root content；the relation owns role、message occurrence order
  and the optional display name authored for that occurrence。
- **Status**: frozen by D-254。

## Email Participant Relations

Every observed participant occurrence is a directional Email → EmailAddress Relation whose content is the canonical compact
JSON serialization of：

```json
{
  "role": "from",
  "order": 0,
  "display_name": "Alice"
}
```

- exact `role` values：`from`、`sender`、`reply_to`、`to`、`cc`、`bcc`。
- `order` is a required non-negative、zero-based sequence owned independently by each role，preserving source occurrence
  order。One EmailAddress may have multiple occurrence Relations when the message gives it multiple roles。
- `display_name` is nullable and preserves the decoded occurrence-local phrase；it never mutates the shared EmailAddress。
- From and Sender remain distinct：From identifies authors while Sender identifies the transmitting mailbox when supplied。
  To、Cc and Bcc all remain destination participation facts；the adapter records only observed Bcc values and does not infer
  stripped/undelivered recipients。
- Use structured JSON rather than delimiter escaping because display names freely contain punctuation and Unicode。The Mail
  extension owns parsing and canonical compact serialization of this Relation content。
- RFC address-group labels are not retained in the MVP；only their actual addr-spec members produce participant Relations。
  A group label is not a communication endpoint and currently has insufficient rendering、navigation or retrieval return to
  earn a Block/hyperedge representation。Empty groups therefore produce no participant relation。
- **Status**: frozen by D-255。

## Reply / Reference Graph

- In-Reply-To produces reply Email → referenced Email Relations with `parent:<order>`，where each header owns a contiguous
  zero-based order。Incoming `parent:*` Relations are the target Email's replies；outgoing Relations are the current Email's
  explicitly authored parents。
- References produces referencing Email → referenced Email Relations with `reference:<order>`，preserving header order。
  This is ancestry/reference evidence rather than an inferred thread shortcut；a target may also have a `parent:*` Relation
  when both source headers name it。
- D-262 permits different Mailboxes' locators to share one best-effort canonical Email，so a Message-ID-only Email anchor
  can be the same domain node later completed by a collected occurrence。A second matching UID in the same Mailbox must
  instead create another Email Block。D-264 owns candidate cardinality，D-265 owns identity compatibility and D-266 restores
  D-256's anchor mechanism under those rules。
- The accepted product intent remains：preserve source-native In-Reply-To/References evidence and support reply navigation
  without inventing subject/participant/time inference。The same canonical identity rule now chooses/creates the target and
  later completes it；an occurrence never needs a separate reference entity merely for this purpose。
- Only parsed semantic msg-id values produce anchors/Relations。Malformed residue is not promoted to an identity-bearing
  Block merely for wire fidelity。Self-links、cycles and repeated protocol facts are not reinterpreted by Collection；normal
  exact-relation idempotency applies。
- Message-ID candidate resolution uses `zero → create anchor / one → reuse / many → create anchor`。The incomplete anchor is
  an ordinary Email with only `message_id` known，not a placeholder type or persisted lifecycle state。Later exact-one
  compatible collection completes that Block；ambiguity never authorizes rewriting one existing reference target。
- **Status**: D-256 relation intent and anchor mechanism are restored and refined by D-262–D-266。

## Explicit Non-Goals at This Edge

- Do not introduce a Mail Thread entity/table merely to group reply/reference edges；thread views are graph-derived unless a
  later use path proves otherwise。
- Do not preserve complete RFC822 bytes by default：that would also download attachment/inline bytes and contradict the
  accepted lazy materialization boundary。
- Do not introduce a generic arbitrary-header bag without a demonstrated use case。Specific valuable fields can later earn
  canonical root fields or graph representation through their own product pressure。

## Status

Canonical Email、body/component decomposition、participants and reply/reference graph are frozen for implementation
planning through D-266。
