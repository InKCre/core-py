"""Role-specific database URLs preserve branch coordinates without leaks."""

import pytest

from scripts.rebind_database_url import rebind_database_url


def test_rebind_database_url_encodes_credentials_and_preserves_coordinates():
  result = rebind_database_url(
    "postgresql://owner:old@db.example.test:5432/inkcre?sslmode=require",
    role="inkcre_core",
    password="slash/colon:at@percent%",
    scheme="postgresql+psycopg",
  )

  assert result == (
    "postgresql+psycopg://"
    "inkcre_core:slash%2Fcolon%3Aat%40percent%25"
    "@db.example.test:5432/inkcre?sslmode=require"
  )


@pytest.mark.parametrize(
  ("source_url", "role", "password", "scheme"),
  [
    ("", "role", "password", "postgresql"),
    ("https://example.test/database", "role", "password", "postgresql"),
    ("postgresql://owner@db.test/database", "", "password", "postgresql"),
    ("postgresql://owner@db.test/database", "role", "", "postgresql"),
    ("postgresql://owner@db.test/database", "role", "password", "https"),
  ],
)
def test_rebind_database_url_rejects_invalid_inputs(
  source_url,
  role,
  password,
  scheme,
):
  with pytest.raises(ValueError):
    rebind_database_url(
      source_url,
      role=role,
      password=password,
      scheme=scheme,
    )
