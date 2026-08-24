# Mail Extension Evidence

## Historical client-web Source-runtime baseline

- The preflight `@inkcre/core` exposed persisted `Source`、`SourceType` and legacy `SourceCollectJob` models plus database helpers，
  while client-web exposed Source/job management UI。Repository search found no executable Source manager、handler registry
  or Source implementation in client-web；the Twitter extension contained Resolver/rendering behavior only。
- Therefore preflight could not name an existing client-web Source handler。The accepted client-web Job-worker capability was
  proven through the production registration contract，while production browser runtime correctly declines IMAP jobs it
  cannot transport。This keeps test aliases out of production and does not expand the Mail Source into a browser IMAP
  implementation。

## Acceptance-server capability coverage

- Dovecot's own 2.0.19 release notes already discuss fixes to `ENABLE CONDSTORE/QRESYNC`，and the Dovecot imaptest
  compatibility matrix lists both CONDSTORE and QRESYNC support。The blocking Dovecot harness can therefore provide real
  MODSEQ/flag-delta/VANISHED evidence rather than testing only new-message polling。
- The same compatibility matrix does not list RFC 8474 OBJECTID support for Dovecot。Adding a second production IMAP server
  solely for this optional rung has poor MVP return；a focused socket-level scripted protocol scenario may exercise the
  production Adapter's OBJECTID capability/response branch without replacing Dovecot as the vertical authority。
- Sources：Dovecot [2.0.19 release notes](https://dovecot.org/list/dovecot-news/2012-March/000218.html) and the
  Dovecot imaptest [server capability matrix](https://github.com/dovecot/imaptest/wiki/Specs)。

> Read-only product/technical evidence retained from the completed Mail unit。Decisions remain in the program decision register。

## Attachment Fetch Behavior

- [IMAP4rev2 RFC 9051](https://www.rfc-editor.org/rfc/rfc9051.html) allows clients to fetch envelope/body structure and
  individual MIME body parts through `BODY.PEEK[...]` / `BINARY.PEEK[...]` rather than retrieving the complete message。
- [Apple Mail account settings](https://support.apple.com/en-euro/guide/mail/cpmlprefacctinfo/mac) state that media
  attachments are always downloaded，while other attachment types can be configured as All、Recent or None。
- [Gmail desktop attachment help](https://support.google.com/mail/answer/30719) presents attachment download as an explicit
  action after opening a message。
- [Gmail Offline help](https://support.google.com/mail/answer/1306849) allows users to disable attachment download to reduce
  local storage，and [Gmail Android settings](https://support.google.com/mail/answer/6562) expose automatic attachment
  download on Wi-Fi as a setting。

### Product inference

There is no reliable cross-client rule that complete mail synchronization automatically downloads and durably stores every
attachment。Selective/lazy/configured fetching is supported by the protocol and mainstream clients。The current Mail scope
therefore does not need collection-time attachment bytes merely to behave like a credible email client。

## Message Identity Facts

- [Internet Message Format RFC 5322 §3.6.4](https://www.rfc-editor.org/rfc/rfc5322.html#section-3.6.4) defines Message-ID as
  the unique identifier for one particular version of one particular message；transport-added trace fields do not normally
  change that identity。
- [IMAP4rev2 RFC 9051 §2.3.1.1](https://www.rfc-editor.org/rfc/rfc9051.html#section-2.3.1.1) defines UID as mailbox-scoped。
  The tuple mailbox name + UIDVALIDITY + UID must refer to one immutable or expunged message on that server and detect UID
  regeneration across sessions。
- [IMAP implementation recommendations RFC 2683 §3.4.4](https://www.rfc-editor.org/rfc/rfc2683.html#section-3.4.4) warns that
  UIDVALIDITY does not itself identify a mailbox and UIDs are not unique across mailboxes。
- [IMAP4rev2 RFC 9051 §5.1.2](https://www.rfc-editor.org/rfc/rfc9051.html#section-5.1.2) allows one authenticated connection
  to expose Personal、Other Users' and Shared namespaces。Distinct authentication credentials are therefore not a protocol
  proof that their visible mailbox stores are disjoint。
- [IMAP OBJECTID RFC 8474](https://www.rfc-editor.org/rfc/rfc8474.html) defines optional server-allocated `MAILBOXID` and
  `EMAILID` values for servers advertising the `OBJECTID` capability。Base IMAP does not provide an equivalent mandatory
  stable account identifier。

### Technical inference awaiting decision

Message-ID is the strongest source-native cross-mailbox/cross-account reconciliation candidate when present。The
server/account instance + mailbox identity + UIDVALIDITY + UID tuple is an exact IMAP remote occurrence locator，not a global
Email identity or a fallback reconciliation key。The current implementation's bare `uid` field cannot locate a message
outside one selected mailbox and UID epoch。

A Mail Source can durably identify one configured IMAP access context，not a protocol-proven unique remote account。Different
Sources may expose overlapping mailboxes through aliases、delegation or shared namespaces。Without an optional server-native
identifier such as OBJECTID，cross-Source equality remains best-effort。

## Mailbox Discovery and Object-ID Facts

- [IMAP4rev2 RFC 9051 §7.3.1](https://www.rfc-editor.org/rfc/rfc9051.html#section-7.3.1) defines each `LIST` response using
  mailbox attributes、a hierarchy delimiter that may be `NIL`，and a mailbox name。The protocol does not expose one portable
  filesystem-like mailbox path field。
- [IMAP4rev2 RFC 9051 §5.1.2](https://www.rfc-editor.org/rfc/rfc9051.html#section-5.1.2) permits multiple personal、other-user
  and shared namespace prefixes and delimiters。Namespace classification is therefore additional discovery context，not the
  Mailbox object's universal identity。
- [IMAP OBJECTID RFC 8474 §4](https://www.rfc-editor.org/rfc/rfc8474.html#section-4) defines `MAILBOXID` as stable across
  ordinary mailbox rename and unique only within the mailboxes exposed to one client login on one server hostname。A bare
  `MAILBOXID` is not globally comparable。
- The same RFC requires `SELECT` / `EXAMINE` to return `MAILBOXID` when `OBJECTID` is advertised，so the accepted MVP can
  consume the value without one extra query per selected mailbox。

### Product/technical inference

The later collection-value audit supersedes the earlier inference that every stable LIST fact should persist。Canonical
Mailbox calls the protocol field `name`、retains only adapter-understood special-use roles with product meaning and keeps a
nullable bare `mailbox_id` for rename continuity inside its owning Source。LIST delimiter、generic structural/subscription
attributes、message counts and duplicated access scope remain transient Source evidence。Permanent Source scoping plus the
`manages` relation already provides the only comparison scope this unit admits。

## Message Content and Envelope Facts

- [Internet Message Format RFC 5322 §3.6.1](https://www.rfc-editor.org/rfc/rfc5322.html#section-3.6.1) defines `Date` as the
  time the creator considered the message complete and ready for delivery，not transport or mailbox-arrival time。
- [RFC 5322 §3.6](https://www.rfc-editor.org/rfc/rfc5322.html#section-3.6) requires origin date and originator fields for a
  conforming message but makes the other header fields syntactically optional。Real clients must still tolerate malformed
  or draft messages with missing values。
- [RFC 5322 §3.6.4](https://www.rfc-editor.org/rfc/rfc5322.html#section-3.6.4) defines Message-ID as identifying one version of
  one message；the surrounding angle brackets are syntax rather than part of the semantic identifier。In-Reply-To and
  References carry identifiers of other messages and therefore naturally pressure graph relationships/unresolved refs。
- [IMAP4rev2 RFC 9051 §7.5.2](https://www.rfc-editor.org/rfc/rfc9051.html#section-7.5.2) exposes an `ENVELOPE` parsed from RFC
  5322 headers and a separate `INTERNALDATE` message attribute。The latter belongs to one stored occurrence and must not be
  substituted for the message-authored Date fact。
- [MIME RFC 2046 §5.1.4](https://www.rfc-editor.org/rfc/rfc2046.html#section-5.1.4) defines multipart/alternative parts as
  representations ordered by increasing faithfulness/preference。Plain text and HTML can therefore be retained together as
  authored alternatives rather than collapsing one into the other during collection。
- [MIME RFC 2046 §5.1](https://www.rfc-editor.org/rfc/rfc2046.html#section-5.1) defines a multipart body as one or more body
  parts，each with its own header area and body area；`multipart/mixed` ordering is significant while
  `multipart/alternative` means interchangeable representations whose order conveys preference。
- [Content-Disposition RFC 2183 §2](https://www.rfc-editor.org/rfc/rfc2183.html#section-2) makes disposition optional and
  defines `inline` / `attachment` as presentation semantics for a MIME entity/body part。Attachment is therefore not a
  standalone media type；filename and disposition remain source-authored metadata about separately typed content。
- [IMAP4rev2 RFC 9051 §7.5.2](https://www.rfc-editor.org/rfc/rfc9051.html#section-7.5.2) defines `BODYSTRUCTURE` as a
  server-parsed MIME structure。A non-multipart part exposes media type/subtype、parameters、Content-ID、description、
  transfer encoding and encoded octet size；extension fields can expose disposition、language and content location。
- The RFC explicitly defines BODYSTRUCTURE body size as transfer-encoded octets。`BINARY.SIZE[section]` is the separate
  decoded size returned only through the corresponding decoded-fetch capability。A canonical pre-download metadata field
  must therefore not claim to be actual semantic-content byte size。
- [IMAP4rev2 RFC 9051 §6.4.5.1](https://www.rfc-editor.org/rfc/rfc9051.html#section-6.4.5.1) defines `section` as positional
  part specifiers assigned from MIME occurrence order。A canonical `part_id` such as `2.1` therefore has stable structural
  meaning relative to one exact Email/MIME tree：it identifies、orders and remotely locates that part。It is not global
  content identity，so its natural owner is the Email → component Relation rather than intrinsic MIME-part Block content。
- [MIME RFC 2045 §8](https://www.rfc-editor.org/rfc/rfc2045.html#section-8) defines Content-Description specifically as
  optional descriptive information for a body（for example，a human description of an image）。It is ordinary authored
  semantic metadata and can support label/text retrieval even before bytes are materialized。
- RFC 2045 calls a Content-Type value a `media type` and defines it through type/subtype identifiers；IMAP BODYSTRUCTURE
  returns those as separate `body type` and `body subtype` strings。Canonical `media_type = "type/subtype"` is therefore
  standards-aligned terminology，though not one literal IMAP response field name。
- [CID URL RFC 2392 §2](https://www.rfc-editor.org/rfc/rfc2392.html#section-2) defines Content-ID as a body-part identifier used
  by `cid:` references，while [MHTML RFC 2557 §4.2](https://www.rfc-editor.org/rfc/rfc2557.html#section-4.2) defines
  Content-Location as another body-part label。The label belongs to the MIME-part metadata；a resolved HTML-body occurrence
  referring to that label is a distinct contextual graph edge。

### Current implementation evidence

- `extensions/mail/schema.py` places mailbox-scoped `uid` and derived `has_attachments` in Email root content。
- `extensions/mail/imap.py` fetches full RFC822 bytes，uses only the first matching plain/HTML part，skips a message without
  both From and To，and substitutes local `datetime.now()` when Date is absent or invalid。
- These behaviors are PoC evidence，not accepted contracts：the new collection boundary already places UID in membership、
  attachments in graph metadata and Block timestamps solely in InKCre persistence lifecycle。

## Address Identity and Display-Name Facts

- [Internet Message Format RFC 5322 §3.4](https://www.rfc-editor.org/rfc/rfc5322.html#section-3.4) models a mailbox as an
  addr-spec optionally accompanied by a display name。The display name is presentation supplied in that address-field
  occurrence；the same addr-spec may appear without it or with another phrase in another message。
- [SMTP RFC 5321 §2.4](https://www.rfc-editor.org/rfc/rfc5321.html#section-2.4) requires preserving mailbox local-part case，
  even while discouraging servers from exploiting case sensitivity；mailbox domains follow case-insensitive DNS rules。
- [SMTPUTF8 RFC 6531 §3.2](https://www.rfc-editor.org/rfc/rfc6531.html#section-3.2) permits UTF-8 local parts and requires
  internationalized DNS names to use a Unicode-aware resolver or A-label transformation。Canonical identity must therefore
  preserve local-part Unicode/case while choosing one domain representation。
- Provider-specific equivalences such as plus-address removal or dot folding are not protocol identity rules and cannot be
  applied by a generic Mail adapter without explicit provider authority。

### Current implementation evidence

- `extensions/mail/schema.py` lowercases the complete addr-spec and stores one display name on the EmailAddress Block。
- `EmailAddressResolver.get_existing()` reconciles solely by that lowercased value，so independent messages can silently
  compete for a contextual name while protocol-significant local-part case has already been erased。

## Remote Mail State and Flag Facts

- [IMAP4rev2 RFC 9051 §2.3.2](https://www.rfc-editor.org/rfc/rfc9051.html#section-2.3.2) defines flags as a mutable list on a
  message in IMAP mailbox context。System flags are Seen、Answered、Flagged、Deleted and Draft；Recent is deprecated。
- The same section distinguishes system flags from server-defined keywords and standard `$...` keywords，but both remain
  members of the same FLAGS attribute and both may be added/removed。Different display/action semantics do not create a
  different protocol persistence category。
- [RFC 9051 §6.4.6](https://www.rfc-editor.org/rfc/rfc9051.html#section-6.4.6) changes flags through STORE against message
  sequence/UIDs in the selected mailbox。If a local model reconciles several remote occurrences into one Email，global
  unscoped Email → Flag edges erase the exact operation scope。D-262 instead scopes each MailFlag through its owning
  Mailbox and permits only one live Mailbox/Email occurrence，so a plain tag edge derives one exact UID locator without
  copying it into Relation content。
- The same RFC defines `\Deleted` as “marked for removal by later EXPUNGE”，so it is still a flag while membership exists；
  actual EXPUNGE is the separate evidence that removes the occurrence。`\Recent` is deprecated and session-derived，so it
  does not earn durable graph persistence。
- Base IMAP exposes flag names、current FLAGS and mailbox PERMANENTFLAGS，but no per-flag description field。A persisted
  MailFlag description can still have the same retrieval/interpretation value as MIME Content-Description，while its
  authority must be documented as standards/provider/adapter semantic metadata rather than a wire-returned IMAP fact。
- A FETCH `FLAGS` data item is the message's current complete flag list，while STORE supports replace/add/remove forms。
  Therefore a collected full FLAGS response is replacement authority for that occurrence's local `tags` set，not merely
  another append event。Discovering which previously collected occurrences changed is a separate synchronization problem。
- [CONDSTORE/QRESYNC RFC 7162](https://www.rfc-editor.org/rfc/rfc7162.html) defines HIGHESTMODSEQ as a mailbox sync checkpoint
  whose validity depends on the mailbox UIDVALIDITY。QRESYNC can return changed FLAGS and VANISHED UIDs；CONDSTORE alone can
  fetch CHANGEDSINCE metadata but still requires UID FETCH/SEARCH to discover expunges。An empty Mailbox has no occurrence
  Relation from which a prior synchronization epoch can be recovered，so checkpoint placement cannot be hand-waved as a
  duplicate occurrence locator。
- A Relation can own occurrence fields but cannot itself be the endpoint of Mail Flag Relations。This is topology evidence，
  not proof that an occurrence must become an association Block。A Mailbox-scoped MailFlag plus unique Mailbox/Email
  membership preserves exact scope without a MailOccurrence Block、locator-qualified tag or global one-Email-per-locator
  rule。
