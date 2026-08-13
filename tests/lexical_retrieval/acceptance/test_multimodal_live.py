"""Credentialed real-provider media -> graph -> lexical acceptance."""

import asyncio
import os
from pathlib import Path
import typing

import pytest
import sqlalchemy

from app.business.ai import AIManager
from app.business.deployment_config import DeploymentConfigManager
from app.business.info_base import BlockManager
from app.business.info_base.main import InfoBaseManager
from app.business.info_base.resolver import ResolverManager, register_core_resolvers
from app.business.info_base.resolver.audio import (
  AUDIO_RESOLVER_CONFIG_KEY,
  AUDIO_RESOLVER_CONFIG_SCHEMA,
)
from app.business.info_base.resolver.image import (
  IMAGE_RESOLVER_CONFIG_KEY,
  IMAGE_RESOLVER_CONFIG_SCHEMA,
)
from app.business.info_base.resolver.video import (
  VIDEO_RESOLVER_CONFIG_KEY,
  VIDEO_RESOLVER_CONFIG_SCHEMA,
)
from app.business.info_base.storage import StorageManager, WritableStorage
from app.business.lexical_retrieval import LexicalRetrievalManager
from app.business.organization import SUBMIT_GRAPH_TOOL
from app.business.organization_media import (
  MEDIA_INTERPRETATION_CONFIG_KEY,
  MEDIA_INTERPRETATION_CONFIG_SCHEMA,
  interpret_missing_media,
)
from app.engine import SessionLocal
from app.schemas import AgentDefinitionModel
from app.schemas.ai import AIModelModel, AIProviderModel, ChatCapability
from app.schemas.deployment_config import DeploymentConfigModel
from app.schemas.info_base.block import BlockForm, BlockModel
from app.schemas.lexical_retrieval import LexicalMaintenanceOptions

from .prepare_media_assets import prepare_assets


REQUIRED_ENVIRONMENT = (
  "INKCRE_TEST_DATABASE_URL",
  "INKCRE_ACCEPTANCE_AI_API_KEY",
  "INKCRE_ACCEPTANCE_AI_BASE_URL",
  "INKCRE_ACCEPTANCE_MULTIMODAL_MODEL",
)
CONFIG_KEYS = (
  IMAGE_RESOLVER_CONFIG_KEY,
  AUDIO_RESOLVER_CONFIG_KEY,
  VIDEO_RESOLVER_CONFIG_KEY,
  MEDIA_INTERPRETATION_CONFIG_KEY,
)


pytestmark = pytest.mark.skipif(
  not all(os.getenv(name) for name in REQUIRED_ENVIRONMENT),
  reason="requires an explicit database and real multimodal Model Studio model",
)


def _reset_runtime_rows() -> None:
  with SessionLocal() as db:
    db.connection().execute(
      sqlalchemy.text(
        "TRUNCATE TABLE inkcre.block_lexical_records, inkcre.jobs, inkcre.crons, "
        "inkcre.relations, inkcre.blocks, inkcre.storage_blobs RESTART IDENTITY CASCADE"
      )
    )
    db.commit()


def _backup_configs() -> dict[str, dict[str, typing.Any]]:
  with SessionLocal() as db:
    return {
      key: record.model_dump()
      for key in CONFIG_KEYS
      if (record := db.get(DeploymentConfigModel, key)) is not None
    }


def _restore_configs(backup: dict[str, dict[str, typing.Any]]) -> None:
  with SessionLocal() as db:
    for key in CONFIG_KEYS:
      current = db.get(DeploymentConfigModel, key)
      if current is not None:
        db.delete(current)
    db.flush()
    for record in backup.values():
      db.add(DeploymentConfigModel.model_validate(record))
    db.commit()


def _stored_media(resolver: str, path: Path) -> BlockModel:
  with SessionLocal() as db:
    storage = StorageManager.get_storage(-4, db)
    assert isinstance(storage, WritableStorage)
    pointer = storage.create_raw_content(path.read_bytes(), db)
    block = BlockManager.create(
      BlockForm(storage=-4, resolver=resolver, content=pointer),
      db,
    )
    db.commit()
    db.refresh(block)
    return block


def _related(block: int, role: str) -> BlockModel | None:
  related = InfoBaseManager.get_related_block(block, content=role)
  if related is None:
    return None
  with SessionLocal() as db:
    return db.get(BlockModel, related.id)


async def _project(block: BlockModel) -> str:
  text = await ResolverManager.get(block).get_text(materialize_missing=False)
  assert text is not None
  return text


def test_real_multimodal_materialization_interpretation_and_recall() -> None:
  assets = prepare_assets()
  _reset_runtime_rows()
  register_core_resolvers()
  StorageManager.setup_builtin_storages()
  AIManager.sync_dialects()
  backup = _backup_configs()
  provider_id: int | None = None
  model_id: int | None = None
  agent_id: int | None = None

  try:
    with SessionLocal() as db:
      provider = AIProviderModel(
        name="Live Model Studio acceptance",
        dialect="core.alibaba-model-studio.v1",
        config={
          "api_key": os.environ["INKCRE_ACCEPTANCE_AI_API_KEY"],
          "base_url": os.environ["INKCRE_ACCEPTANCE_AI_BASE_URL"],
        },
      )
      db.add(provider)
      db.flush()
      provider_id = provider.id
      assert provider_id is not None
      model = AIModelModel(
        provider=provider_id,
        native_model_id=os.environ["INKCRE_ACCEPTANCE_MULTIMODAL_MODEL"],
        capabilities=(
          ChatCapability(
            input_modalities=("text", "image", "audio", "video"),
            output_modalities=("text",),
            features=("tool_calling",),
          ),
        ),
      )
      db.add(model)
      db.flush()
      model_id = model.id
      assert model_id is not None
      agent = AgentDefinitionModel(
        name="Live media interpretation acceptance Agent",
        system_prompt=(
          "Inspect the supplied media and call submit_graph exactly once. Create one "
          "core.text.v1 Block whose content is exactly 'international flight-software "
          "collaboration insight', then connect the focal Block to it with an "
          "'interpretation' Relation. In GraphForm, positive IDs reference existing "
          "Blocks and MUST NOT be repeated in graph.blocks; negative IDs declare new "
          "Blocks. Therefore graph.blocks contains only the new Block with id -1, "
          "while the Relation uses the positive focal Block id from the user message "
          "as from_. After a successful Tool result, return done without another "
          "ToolCall."
        ),
        tools=(SUBMIT_GRAPH_TOOL,),
        tool_choice="auto",
        model=model_id,
        max_model_calls_per_turn=2,
      )
      db.add(agent)
      db.commit()
      db.refresh(agent)
      agent_id = agent.id
      assert agent_id is not None

    DeploymentConfigManager.replace(
      IMAGE_RESOLVER_CONFIG_KEY,
      IMAGE_RESOLVER_CONFIG_SCHEMA,
      {"text_model": model_id},
    )
    DeploymentConfigManager.replace(
      AUDIO_RESOLVER_CONFIG_KEY,
      AUDIO_RESOLVER_CONFIG_SCHEMA,
      {"transcript_model": model_id},
    )
    DeploymentConfigManager.replace(
      VIDEO_RESOLVER_CONFIG_KEY,
      VIDEO_RESOLVER_CONFIG_SCHEMA,
      {"text_model": model_id, "transcript_model": model_id},
    )
    DeploymentConfigManager.replace(
      MEDIA_INTERPRETATION_CONFIG_KEY,
      MEDIA_INTERPRETATION_CONFIG_SCHEMA,
      {
        "image_agent": 2**62,
        "audio_agent": 2**62,
        "video_agent": agent_id,
      },
    )

    image = _stored_media("core.image.v1", assets / "nasa-gpm-frame.png")
    audio = _stored_media("core.audio.v1", assets / "nasa-gpm-audio.wav")
    video = _stored_media("core.video.v1", assets / "nasa-gpm-subtitled.mkv")
    assert image.id is not None and audio.id is not None and video.id is not None

    first = asyncio.run(
      LexicalRetrievalManager.maintain(
        LexicalMaintenanceOptions(max_records=30, scan_page_size=3)
      )
    )
    assert first.failed == first.unavailable == 0
    image_text = _related(image.id, "text")
    audio_transcript = _related(audio.id, "transcript")
    video_subtitle = _related(video.id, "subtitle")
    video_transcript = _related(video.id, "transcript")
    video_text = _related(video.id, "text")
    assert all(
      block is not None
      for block in (
        image_text,
        audio_transcript,
        video_subtitle,
        video_transcript,
        video_text,
      )
    )
    assert (
      "nasa.gov/gpm" in asyncio.run(_project(typing.cast(BlockModel, image_text))).lower()
    )
    assert (
      "flight software"
      in asyncio.run(_project(typing.cast(BlockModel, audio_transcript))).lower()
    )
    assert (
      "flight software"
      in asyncio.run(_project(typing.cast(BlockModel, video_subtitle))).lower()
    )

    image_recall = LexicalRetrievalManager.retrieve_local("nasa.gov/gpm")
    assert image_recall.matches[0].block.id == typing.cast(BlockModel, image_text).id
    spoken_recall = LexicalRetrievalManager.retrieve_local("Tanegashima")
    assert typing.cast(BlockModel, audio_transcript).id in {
      match.block.id for match in spoken_recall.matches
    }

    child_ids = {
      typing.cast(BlockModel, block).id
      for block in (
        image_text,
        audio_transcript,
        video_subtitle,
        video_transcript,
        video_text,
      )
    }
    second = asyncio.run(LexicalRetrievalManager.maintain())
    assert second.failed == second.unavailable == 0
    assert child_ids == {
      typing.cast(BlockModel, _related(image.id, "text")).id,
      typing.cast(BlockModel, _related(audio.id, "transcript")).id,
      typing.cast(BlockModel, _related(video.id, "subtitle")).id,
      typing.cast(BlockModel, _related(video.id, "transcript")).id,
      typing.cast(BlockModel, _related(video.id, "text")).id,
    }

    report = asyncio.run(interpret_missing_media())
    assert report.selected == 3
    assert report.interpreted == 1
    assert report.unavailable == 2
    interpretation = _related(video.id, "interpretation")
    assert interpretation is not None
    assert asyncio.run(_project(interpretation)) == (
      "international flight-software collaboration insight"
    )
    indexed = asyncio.run(LexicalRetrievalManager.maintain())
    assert indexed.failed == 0
    interpretation_recall = LexicalRetrievalManager.retrieve_local(
      "international flight-software collaboration insight"
    )
    assert interpretation_recall.matches[0].block.id == interpretation.id
  finally:
    _restore_configs(backup)
    with SessionLocal() as db:
      if agent_id is not None:
        stored_agent = db.get(AgentDefinitionModel, agent_id)
        if stored_agent is not None:
          db.delete(stored_agent)
      if model_id is not None:
        stored_model = db.get(AIModelModel, model_id)
        if stored_model is not None:
          db.delete(stored_model)
      if provider_id is not None:
        stored_provider = db.get(AIProviderModel, provider_id)
        if stored_provider is not None:
          db.delete(stored_provider)
      db.commit()
    _reset_runtime_rows()
