"""Real PostgreSQL proof for shared AI facts and database-owned invariants."""

import datetime
import os
import time

import pytest
import sqlalchemy
import sqlalchemy.exc

from app.business.ai import AIManager
from app.engine import SessionLocal
from app.schemas.ai import (
  AIModelModel,
  AIProviderModel,
  ChatCapability,
  EmbeddingCapability,
  EmbeddingProfileModel,
)


pytestmark = pytest.mark.skipif(
  not os.getenv("INKCRE_TEST_DATABASE_URL"),
  reason="requires an explicitly selected migrated PostgreSQL runtime",
)


def _cleanup(provider_id: int | None) -> None:
  if provider_id is None:
    return
  with SessionLocal() as db:
    db.connection().execute(
      sqlalchemy.text(
        "DELETE FROM inkcre.embedding_profiles WHERE ai_model IN "
        "(SELECT id FROM inkcre.ai_models WHERE provider = :provider)"
      ),
      {"provider": provider_id},
    )
    db.connection().execute(
      sqlalchemy.text("DELETE FROM inkcre.ai_models WHERE provider = :provider"),
      {"provider": provider_id},
    )
    db.connection().execute(
      sqlalchemy.text("DELETE FROM inkcre.ai_providers WHERE id = :provider"),
      {"provider": provider_id},
    )
    db.commit()


def test_ai_facts_round_trip_typed_capabilities_and_database_invariants():
  AIManager.sync_dialects()
  provider_id: int | None = None
  try:
    with SessionLocal() as db:
      provider = AIProviderModel(
        name="integration provider",
        dialect="core.openai-compatible.v1",
        config={"api_key": "test-key", "base_url": "https://provider.example/v1"},
      )
      db.add(provider)
      db.flush()
      provider_id = provider.id
      assert provider_id is not None
      model = AIModelModel(
        provider=provider_id,
        native_model_id="integration-model",
        capabilities=(
          EmbeddingCapability(input_modalities=["text"], output_modalities=["vector"]),
          ChatCapability(
            input_modalities=["text"],
            output_modalities=["text"],
            features=["tool_calling"],
          ),
        ),
      )
      db.add(model)
      db.flush()
      assert model.id is not None
      profile = EmbeddingProfileModel(ai_model=model.id, dimensions=2)
      db.add(profile)
      db.commit()
      db.refresh(model)
      db.refresh(profile)

      assert [capability.type for capability in model.capabilities] == [
        "chat",
        "embedding",
      ]
      assert profile.created_at.tzinfo is not None
      prior = profile.updated_at
      time.sleep(0.002)
      profile.name = "updated"
      db.add(profile)
      db.commit()
      db.refresh(profile)
      assert isinstance(profile.updated_at, datetime.datetime)
      assert profile.updated_at > prior

      model.native_model_id = "forbidden-change"
      db.add(model)
      with pytest.raises(sqlalchemy.exc.IntegrityError):
        db.commit()
      db.rollback()
  finally:
    _cleanup(provider_id)
