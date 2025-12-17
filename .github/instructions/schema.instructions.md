---
applyTo: "**/schemas/**.py"
description: "When you editing a schema"
---

- The database is PostgreSQL, make sure your column type, default follows PostgreSQL best practices:
  - use `sqlalchemy.dialects.postgresql.JSONB` instead of `sqlmodel.JSON`
  - If JSONB column uses default factory `dict`, set `server_default=sa.text("'{}'::jsonb")`