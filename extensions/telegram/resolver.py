"""Legacy Telegram messages and metadata-first attachment materialization."""

from __future__ import annotations

import mimetypes
from pathlib import Path

import sqlmodel
import telegram

from app.business.info_base.block import BlockManager
from app.business.info_base.relation import RelationManager
from app.business.info_base.resolver import Resolver, ResolverManager, TextProjectionContext
from app.business.info_base.resolver.inspection import detect_media_type
from app.business.info_base.resolver.label import format_label
from app.business.source import SourceManager
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockForm, BlockModel
from app.schemas.info_base.main import StarsGraphForm
from app.schemas.info_base.relation import RelationModel
from app.schemas.source import SourceModel

from .schema import SolvedTelegramAttachment, TelegramAttachment, TelegramMessage


ATTACHMENT_RESOLVER = "extensions.telegram.attachment.v1"
CONTENT_RELATION = "content"
SOURCE_RELATION = "collects"


class TelegramMaterializationUnavailable(RuntimeError):
  """The attachment's exact live Telegram access context is unavailable."""


def _id(block: BlockModel) -> int:
  if block.id is None:
    raise RuntimeError("persisted Block has no ID")
  return block.id


class TelegramMessageResolver(
  Resolver[TelegramMessage, str],
  rso_type="extensions.telegram.message.v1",
):
  """Read-only decoder for published 0.1.0 Telegram message Blocks."""

  def __post_init__(self, raw_content):
    if raw_content is not None:
      self.set_solved_content(TelegramMessage.model_validate_json(raw_content))

  async def _get_solved_content(
    self, *, refresh: bool = False, materialize_missing: bool = True
  ) -> TelegramMessage:
    del materialize_missing
    return TelegramMessage.model_validate_json(await self.get_raw_content(refresh=refresh))

  @classmethod
  def create_graph(cls, message: TelegramMessage) -> StarsGraphForm:
    """Legacy fixture seam; new collection never calls it."""
    return StarsGraphForm(
      block=BlockForm(resolver=cls.__rsotype__, content=message.model_dump_json())
    )

  async def get_text(
    self,
    *,
    context: TextProjectionContext = "default",
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str | None:
    del context
    message = await self.get_solved_content(
      refresh=refresh, materialize_missing=materialize_missing
    )
    parts = [message.text or message.caption]
    if message.has_media and message.media_type:
      parts.append(f"[{message.media_type}]")
    return "\n".join(part for part in parts if part) or None

  async def get_label(self, *, refresh: bool = False) -> str:
    message = await self.get_solved_content(refresh=refresh, materialize_missing=False)
    return format_label(
      "telegram message",
      message.text or message.caption or str(message.message_id),
      first_line=True,
    )


class TelegramAttachmentResolver(
  Resolver[SolvedTelegramAttachment, str],
  rso_type=ATTACHMENT_RESOLVER,
):
  """Project useful remote-file metadata without implicit network effects."""

  async def _get_solved_content(
    self, *, refresh: bool = False, materialize_missing: bool = True
  ) -> SolvedTelegramAttachment:
    del materialize_missing
    root = TelegramAttachment.model_validate_json(
      await self.get_raw_content(refresh=refresh)
    )
    relations = await self.get_relations(
      include_in=False, include_out=True, refresh=refresh
    )
    content_ids = [
      relation.to_ for relation in relations if relation.content == CONTENT_RELATION
    ]
    if len(content_ids) > 1:
      raise RuntimeError(
        f"Telegram attachment {self.block_id} has multiple content children"
      )
    content = BlockManager.get(content_ids[0]) if content_ids else None
    return SolvedTelegramAttachment(root=root, content=content)

  @classmethod
  def create_block(
    cls, content: TelegramAttachment, storage: int | None = None
  ) -> BlockForm:
    return BlockForm(
      resolver=cls.__rsotype__, content=content.model_dump_json(), storage=storage
    )

  async def get_text(
    self,
    *,
    context: TextProjectionContext = "default",
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str | None:
    del context
    solved = await self.get_solved_content(
      refresh=refresh, materialize_missing=materialize_missing
    )
    values = [
      solved.root.filename,
      solved.root.title,
      solved.root.performer,
      solved.root.mime_type,
      solved.root.kind,
      solved.root.emoji,
    ]
    return "\n".join(value for value in values if value) or None

  async def get_label(self, *, refresh: bool = False) -> str:
    root = TelegramAttachment.model_validate_json(
      await self.get_raw_content(refresh=refresh)
    )
    return format_label(f"telegram {root.kind}", root.filename or root.title or root.emoji)

  def _source(self) -> SourceModel:
    with SessionLocal() as db:
      relations = db.exec(
        sqlmodel.select(RelationModel).where(
          RelationModel.to_ == self.block_id,
          RelationModel.content == SOURCE_RELATION,
        )
      ).all()
      sources = [
        source
        for relation in relations
        if (
          source := db.exec(
            sqlmodel.select(SourceModel).where(SourceModel.block == relation.from_)
          ).one_or_none()
        )
        is not None
      ]
      if len(sources) != 1:
        raise TelegramMaterializationUnavailable(
          "Telegram attachment has no unique live owning Source"
        )
      return sources[0]

  async def materialize_content(self) -> BlockModel:
    existing = await self.get_solved_content(materialize_missing=False)
    if existing.content is not None:
      return existing.content
    source = self._source()
    from .schema import TelegramSourceConfig, TelegramSourceState

    setup = TelegramSourceConfig.model_validate(source.config)
    state = TelegramSourceState.model_validate(source.state or {})
    if state.bot_id is None:
      raise TelegramMaterializationUnavailable("Telegram Source has no pinned bot identity")
    root = TelegramAttachment.model_validate_json(await self.get_raw_content())
    try:
      async with telegram.Bot(setup.bot_token) as bot:
        identity = await bot.get_me()
        if identity.id != state.bot_id:
          raise TelegramMaterializationUnavailable("Telegram Source bot identity changed")
        remote = await bot.get_file(root.file_id)
        body = bytes(await remote.download_as_bytearray())
    except TelegramMaterializationUnavailable:
      raise
    except telegram.error.BadRequest as error:
      raise TelegramMaterializationUnavailable(str(error)) from error

    declared = ResolverManager.match_media_type(root.mime_type)
    detected = ResolverManager.match_media_type(detect_media_type(body))
    guessed = ResolverManager.match_media_type(
      mimetypes.guess_type(Path(root.filename).name)[0] if root.filename else None
    )
    by_kind = {
      "photo": "core.image.v1",
      "sticker": "core.image.v1",
      "animation": "core.video.v1",
      "video": "core.video.v1",
      "video_note": "core.video.v1",
      "audio": "core.audio.v1",
      "voice": "core.audio.v1",
    }.get(root.kind)
    resolver_id = detected or declared or guessed or by_kind or "core.file.v1"

    with SessionLocal() as db:
      metadata = db.exec(
        sqlmodel.select(BlockModel).where(BlockModel.id == self.block_id).with_for_update()
      ).one_or_none()
      if metadata is None or metadata.resolver != ATTACHMENT_RESOLVER:
        raise TelegramMaterializationUnavailable("Telegram attachment no longer exists")
      existing_relation = db.exec(
        sqlmodel.select(RelationModel).where(
          RelationModel.from_ == self.block_id,
          RelationModel.content == CONTENT_RELATION,
        )
      ).one_or_none()
      if existing_relation is not None:
        existing = db.get(BlockModel, existing_relation.to_)
        if existing is None:
          raise RuntimeError("Telegram attachment content child is missing")
        return existing
      live_source = db.get(SourceModel, source.id)
      if live_source is None:
        raise TelegramMaterializationUnavailable("Telegram Source no longer exists")
      storage = SourceManager.resolve_writable_storage(live_source, db)
      pointer = storage.create_raw_content(body, db)
      child = BlockManager.create(
        BlockForm(storage=storage.storage_id, resolver=resolver_id, content=pointer), db
      )
      RelationManager.create(_id(metadata), _id(child), CONTENT_RELATION, db)
      db.commit()
      db.refresh(child)
      return child
