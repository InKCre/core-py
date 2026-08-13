# Mail acceptance corpus

These original messages form a small professional reading thread about software design。They are installed only through
real IMAP `APPEND` by the Mail acceptance harness；production code contains no fixture IDs or aliases。

- `historical-parent.eml` is present before Source creation and is admitted only by explicit backfill。
- `missing-parent.eml` completes the reply's initially sparse Message-ID anchor during a later ordinary collection。
- `current-reply.eml` is a realistic reply with From/To/Cc、plain + HTML alternatives、CID inline media、a remote tracker、
  a script and a typed attachment。
- `removal-candidate.eml` gives QRESYNC removal synchronization an independent occurrence。
