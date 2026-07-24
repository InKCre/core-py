"""Print the database contract environment or ``absent`` before bootstrap."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.database_contract.connection import database_connection


def get_database_environment() -> str:
  with database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute("SELECT to_regclass('inkcre_internal.contract_state')")
      relation_row = cursor.fetchone()
      if relation_row is None or relation_row[0] is None:
        return "absent"
      cursor.execute(
        "SELECT environment FROM inkcre_internal.contract_state WHERE singleton"
      )
      row = cursor.fetchone()
      if row is None:
        raise RuntimeError("database contract identity row is missing")
      return row[0]


def main() -> int:
  print(get_database_environment())
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
