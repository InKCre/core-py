# Mail Collected-Graph Value Audit

- **Status**: accepted Block/Relation fields and Email identity/reference behavior are frozen through D-266。MailFlag exact
  content/normalization remains under review；the rest of this audit is closed unless new implementation evidence reopens it。
- **Test**: a persisted field/grammar must serve identity、reconciliation、later on-demand access、an accepted use path or
  independently valuable structure。Protocol availability、low fetch cost and possible future interest are not sufficient。

## Block Content

| Owner | Fact | Current judgment | Reason |
| --- | --- | --- | --- |
| Source anchor | `id` | keep | stable operational reference and historical descriptor after Source deletion |
| Source anchor | `type` | keep | exact Source identity/projection and readable provenance |
| Source anchor | `nickname` | keep | human label owned by Source and useful after operational deletion |
| Mailbox | `name` | keep | remote operation、label and source-scoped fallback identity |
| Mailbox | `delimiter` | remove — D-258 | no accepted hierarchy renderer/query；Source can use LIST delimiter transiently |
| Mailbox | generic `attributes` | narrow — D-258 | only recognized special-use role has communication/use value；subscription/selectability/tree hints do not earn persistence |
| Mailbox | `mailbox_id.value` | keep | rename continuity inside one Source when OBJECTID is available |
| Mailbox | `mailbox_id.access_scope` | remove — D-258 | permanent Source-scoped Mailbox plus `Source --manages--> Mailbox` already owns comparison/access scope |
| Email | `message_id` | keep — D-263 | authored message-version evidence、reply/reference input and best-effort reconciliation after scoped EMAILID；not exact occurrence identity |
| Email | `email_id` | keep — D-263 | optional server-native immutable-content evidence and scoped reconciliation before Message-ID；not unconditional uniqueness |
| Email | `subject` | keep | direct authored semantic content、label and retrieval |
| Email | `authored_at` | keep | authored chronology distinct from collection time |
| EmailAddress | `address` | keep | exact useful shared identity and participant navigation |
| MIME part | `part_id` | move to owner Relation — D-259 | MIME tree path identifies/orders the part relative to Email and serves remote fetch；it is not intrinsic Block identity |
| MIME part | `media_type` | keep | classification、rendering and semantic resolver selection |
| MIME part | `charset` | keep — D-259 | required to transcode an on-demand text/HTML part into exact core semantic-content encoding when MIME is the only declaration |
| MIME part | `disposition` | remove — D-259 | canonical owner Relation already owns the usable role |
| MIME part | `filename` | keep | user-facing label/download name |
| MIME part | `content_id` | keep + graph edge — D-259 | intrinsic part label；resolved body reference also earns contextual `embeds` Relation |
| MIME part | `description` | keep | MIME-authored basic semantic description with label/text retrieval value |
| MIME part | `transfer_encoding` | keep — D-259 | required to decode a later IMAP BODY section without re-fetching MIME structure；serves the accepted remote-access path |
| MIME part | `encoded_size` | keep | pre-download display/policy bound without fetching bytes；must remain explicitly encoded/estimated semantics |
| MIME part | `content_location` | keep + graph edge — D-259 | intrinsic part label；resolved body reference also earns contextual `embeds` Relation |
| MailFlag | `name` | keep — D-268 | mailbox-scoped case-insensitive flag identity、remote operation token and generic label |
| MailFlag | `description` | keep — D-268 | adapter-owned provider/standards semantic metadata for resolver text、retrieval and graph interpretation；nullable when no authoritative mapping exists |

## Relation Content

| Grammar | Judgment | Reason |
| --- | --- | --- |
| `manages` | keep | normalized provenance/access path and Source-scoped Mailbox ownership |
| `{type:"contains", uid_validity, uid}` | keep | exact occurrence idempotency/membership locator and later on-demand remote access |
| `{role:"body|attachment|inline", part_id}` | replace role/order strings — D-259 | one MIME tree path owns component identity、source order and IMAP fetch location without duplicate order authority |
| participant `{role, order, display_name}` | keep | complete contextual communication roles/names without corrupting shared EmailAddress |
| `parent:<order>` | keep | direct source-native reply structure and reverse reply navigation |
| `reference:<order>` | keep | ordered native ancestry/reference evidence without inferred thread entity |
| body → part `{type:"embeds", reference}` | add — D-259 | exact collected HTML reference occurrence and direct render/navigation edge |
| `Mailbox --has--> MailFlag` | add — D-262 | mailbox-scoped flag vocabulary shared by exact applications |
| MailFlag → Email `tags` | add — D-262 | ordinary semantic Relation for all durable IMAP flags；owning Mailbox + unique membership derives exact occurrence |

## Candidate Corrections

1. D-258 reduces Canonical Mailbox to `name`、nullable bare `mailbox_id` and a deliberately narrow special-use projection；
   delimiter、generic attributes and duplicated access scope are removed。
2. D-259 re-opens D-252/D-253 narrowly：remove disposition、move `part_id` from MIME-part Block content into a unified Email →
   component Relation and let it replace the separate order；retain semantic Content-Description and retain charset/
   transfer_encoding as compact on-demand materialization inputs。
3. D-259 keeps Content-ID/Location as intrinsic target labels while adding exact HTML body → MIME-part `embeds` Relations for
   resolved reference occurrences，rather than hiding useful graph topology in metadata lookup alone。
4. D-261 supersedes D-260 after duplicate-risk review by restoring best-effort canonical Email and retaining exact locator
   Relations。D-262 then removes locator duplication from MailFlag edges：plain `tags` stays exact because Collection forbids
   multiple live `contains` Relations for one Mailbox/Email pair。`contains` owns membership/locator only and no flag fields。
