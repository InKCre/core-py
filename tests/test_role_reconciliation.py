"""Focused tests for provider-compatible role reconciliation."""

from app.database_contract import roles


class RecordingCursor:
  """Record statements without requiring a live PostgreSQL connection."""

  def __init__(self) -> None:
    self.statements: list[object] = []

  def execute(self, statement: object) -> None:
    self.statements.append(statement)


def test_matching_role_refreshes_only_the_password(monkeypatch) -> None:
  monkeypatch.setattr(
    roles,
    "_role_attributes",
    lambda _cursor, _role_name: (True, False, False, False, False, False, False),
  )
  cursor = RecordingCursor()

  roles._set_role_attributes(
    cursor,
    "authenticator",
    login=True,
    inherit=False,
    password="x" * 32,
  )

  assert len(cursor.statements) == 1
  statement = repr(cursor.statements[0])
  assert "PASSWORD" in statement
  assert "NOSUPERUSER" not in statement
