---
applyTo: "**/schemas/**.py"
description: "When you editing a schema"
---

- The database is PostgreSQL, make sure your column type, default follows PostgreSQL best practices:
  - use `sqlalchemy.dialects.postgresql.JSONB` instead of `sqlmodel.JSON`
  - If JSONB column uses default factory `dict`, set `server_default=sa.text("'{}'::jsonb")`
- For enum
  - Use StrEnum
  - Set `values_callable` for `sqlalchemy.Enum` to `lambda x: [e.value for e in x]` to use enum values in DB