# Canonical Email and Graph Boundary

- **Status**: candidate，awaiting Sir review。
- **Protocol/code evidence**: [Message Content and Envelope Facts](../evidence.md#message-content-and-envelope-facts)。
- **Resolver**: retain exact ID `extensions.mail.email.v1`；old schema/behavior is not a compatibility authority。

## Candidate Root Content

```json
{
  "message_id": "1234@local.machine.example",
  "subject": "Saying Hello",
  "authored_at": "1997-11-21T09:55:06-06:00",
  "body": {
    "text": "This is a message just to say hello.",
    "html": null
  }
}
```

- `message_id`、`subject`、`authored_at` are nullable。Do not reject malformed/draft messages merely because one is absent。
- `message_id` stores the semantic msg-id without surrounding CFWS/angle brackets；it is a best-effort reconciliation fact，
  never a database uniqueness constraint。
- `authored_at` means RFC 5322 origination time。Never synthesize it from collect time、Block.created_at、IMAP
  INTERNALDATE or local clock；those are different facts/lifecycles。
- `body.text` and `body.html` retain decoded authored alternatives independently。Both may be null；an empty-body message is
  still collectible。The pair is a semantic projection of supported body alternatives，not a raw MIME tree。
- This root is the Email's intrinsic scalar/authored content needed for identity、label、chronology and reading。It is not a
  wire archive and does not copy every arbitrary/transport header。

## Graph-Owned Facts

- EmailAddress Blocks and directional originator/destination relations own From、Sender、Reply-To、To、Cc and Bcc。
- Email-to-Email relations/unresolved-reference representation own In-Reply-To and References。
- Source/Mailbox relations own provenance and membership occurrence facts，including UIDVALIDITY/UID and later exact
  placement of IMAP INTERNALDATE。
- Mail Flag Blocks/relations own remote Seen、Answered and tag-like keyword state under their already accepted distinct
  semantics。
- Attachment/inline-part metadata Blocks and relations own MIME part identity、filename、declared content type、disposition、
  content-id、size/section locator and later materialized resource links。
- Therefore root content excludes `uid`、`has_attachments`、participants、reply/reference IDs、flags、mailbox、Source and
  attachment arrays。Their presence there would create duplicate authority or a domain god object。

## Explicit Non-Goals at This Edge

- Do not freeze exact relation predicates/content schemas here；only their ownership boundary。
- Do not preserve complete RFC822 bytes by default：that would also download attachment/inline bytes and contradict the
  accepted lazy materialization boundary。
- Do not introduce a generic arbitrary-header bag without a demonstrated use case。Specific valuable fields can later earn
  canonical root fields or graph representation through their own product pressure。

## Active Question

Whether to freeze the root as exactly `message_id + subject + authored_at + body{text,html}` and keep all other accepted Mail
facts graph-owned。
