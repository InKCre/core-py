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
