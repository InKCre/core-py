# Shared Row Timestamp Contract

> [Technical design index](index.md)

## Database-Owned `updated_at` Contract（approved by D-090）

- Shared protocol row-mutation time must not depend on SQLAlchemy `onupdate` because PostgREST and other equal peers can
  write the same relations。
- A reusable internal-schema PostgreSQL `BEFORE UPDATE` trigger touches `updated_at` with statement time when the row
  actually changes。No-op updates should not create false invalidation pressure。
- The trigger is shallow：it does not delete、mark or rebuild embeddings。Block/Profile freshness consumers compare
  database timestamps and schedule/perform derived maintenance separately。
- For blocks，changes to content pointer、storage selection or resolver identity all change the semantic input boundary
  and therefore touch `updated_at`。The same generic row-mutation behavior also covers relation endpoint/content changes。
- Mutating bytes behind an unchanged storage pointer remains outside block row freshness；D-062/D-066 storage authority
  boundaries are unchanged。
- Do not apply this trigger to source-authored timestamps、job event columns or other values whose semantics are not
  “database row last changed”。
