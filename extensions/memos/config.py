"""Configuration owned by the Memos extension."""

import pydantic
import sqlmodel


class MemosConfig(sqlmodel.SQLModel):
  """Deployment-scoped Memos backend configuration."""

  model_config = pydantic.ConfigDict(extra="forbid")

  personal_access_token: str | None = pydantic.Field(
    default=None,
    pattern=r"^memos_pat_[0-9A-Za-z]{32}$",
  )
