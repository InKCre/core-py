---
applyTo: "**/schemas/**.py"
---

- ORM is SQLModel and database is PostgreSQL, use correct types:
  - use `sqlalchemy.dialects.postgresql.JSONB` instead of `sqlmodel.JSON`
- If JSONB column uses default factory `dict`, set `server_default=sa.text("'{}'::jsonb")`
- For enum
  - Use StrEnum
  - Set `sqlalchemy.Enum(values_callable=lambda x: [e.value for e in x])` for enum columns