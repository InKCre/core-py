# Mail Extension Evidence

> Read-only product/technical evidence for the active Mail unit。Decisions remain in the program decision register。

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

Canonical Mailbox content should call the protocol field `name`，retain nullable `delimiter` and normalized `attributes`，
and keep nullable `mailbox_id` with the comparison scope needed to interpret it。It should not persist volatile message
counts merely because IMAP can report them。Because Mailbox Blocks are permanently Source-scoped，these facts describe one
observed mailbox and do not create pressure to merge conflicting observations across Sources。

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

### Current implementation evidence

- `extensions/mail/schema.py` places mailbox-scoped `uid` and derived `has_attachments` in Email root content。
- `extensions/mail/imap.py` fetches full RFC822 bytes，uses only the first matching plain/HTML part，skips a message without
  both From and To，and substitutes local `datetime.now()` when Date is absent or invalid。
- These behaviors are PoC evidence，not accepted contracts：the new collection boundary already places UID in membership、
  attachments in graph metadata and Block timestamps solely in InKCre persistence lifecycle。
