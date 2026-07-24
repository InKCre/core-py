"""HTTP-facing adapter over the executable database readiness contract."""

from app.database_contract.readiness import (
  ContractReadiness,
  check_database_contract,
  get_repository_heads,
)


DatabaseReadiness = ContractReadiness


def check_database_readiness(
  database_url: str | None = None,
) -> ContractReadiness:
  """Check the runtime profile without importing lifecycle mutations."""
  return check_database_contract(
    profile="runtime",
    database_url=database_url,
  )


__all__ = [
  "ContractReadiness",
  "DatabaseReadiness",
  "check_database_readiness",
  "get_repository_heads",
]
