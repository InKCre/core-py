# Canonical Email and Graph Boundary

- **Status**: root scalar/body ownership amended and frozen by D-250；the following direct semantic-body topology and exact
  body/part graph grammar remain candidate。
- **Protocol/code evidence**: [Message Content and Envelope Facts](../evidence.md#message-content-and-envelope-facts)。
- **Resolver**: retain exact ID `extensions.mail.email.v1`；old schema/behavior is not a compatibility authority。

## Canonical Email Root Content

```json
{
  "message_id": "1234@local.machine.example",
  "subject": "Saying Hello",
  "authored_at": "1997-11-21T09:55:06-06:00"
}
```

- `message_id`、`subject`、`authored_at` are nullable。Do not reject malformed/draft messages merely because one is absent。
- `message_id` stores the semantic msg-id without surrounding CFWS/angle brackets；it is a best-effort reconciliation fact，
  never a database uniqueness constraint。
- `authored_at` means RFC 5322 origination time。Never synthesize it from collect time、Block.created_at、IMAP
  INTERNALDATE or local clock；those are different facts/lifecycles。
- This root is the Email's intrinsic scalar/header content needed for identity、label and chronology。It is not a wire
  archive and does not copy every arbitrary/transport header。An empty-body message is still collectible。

## Candidate Source-Native Body Graph

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
- Do not add `extensions.mail.text_body.*` / `html_body.*` metadata wrappers without an independently useful native identity、
  metadata or lifecycle。This is the restraint side of source-native decomposition。
- Attachment and non-text inline MIME parts do have independent protocol facts before bytes exist，so collection creates
  Mail-owned metadata Blocks for them。Their exact resolver ID/content schema is the next edge。
- A pure multipart container is not automatically a Block。It earns representation only when its ordering、alternative/
  related grouping、disposition or another structure fact is required by a real renderer/retrieval/materialization path。

## Graph-Owned Facts

- EmailAddress Blocks and directional originator/destination relations own From、Sender、Reply-To、To、Cc and Bcc。
- Email-to-Email relations/unresolved-reference representation own In-Reply-To and References。
- Source/Mailbox relations own provenance and membership occurrence facts，including UIDVALIDITY/UID and later exact
  placement of IMAP INTERNALDATE。
- Mail Flag Blocks/relations own remote Seen、Answered and tag-like keyword state under their already accepted distinct
  semantics。
- Attachment/inline-part metadata Blocks and relations own MIME part identity、filename、declared content type、disposition、
  content-id、size/section locator and later materialized semantic content links。
- Therefore root content excludes `uid`、`has_attachments`、body representations、participants、reply/reference IDs、flags、
  mailbox、Source and attachment arrays。Their presence there would create duplicate authority or a domain god object。

## Explicit Non-Goals at This Edge

- Do not yet freeze exact relation predicates/content schemas；only their ownership topology。
- Do not preserve complete RFC822 bytes by default：that would also download attachment/inline bytes and contradict the
  accepted lazy materialization boundary。
- Do not introduce a generic arbitrary-header bag without a demonstrated use case。Specific valuable fields can later earn
  canonical root fields or graph representation through their own product pressure。

## Active Question

Freeze the exact Email-body/MIME-part graph grammar：whether ordinary text/HTML bodies connect directly to semantic content
Blocks while only independently useful attachment/inline parts receive metadata Blocks；then decide which MIME ordering and
grouping facts have enough use value to persist。
