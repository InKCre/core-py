"""Exact Mail Resolvers over canonical root content and graph facts."""

from __future__ import annotations

import json
import typing

import sqlmodel

from app.business.info_base.block import BlockManager
from app.business.info_base.main import InfoBaseManager
from app.business.info_base.resolver import (
  Resolver,
  ResolverManager,
  TextProjectionContext,
)
from app.business.info_base.resolver.inspection import detect_media_type
from app.business.info_base.resolver.label import format_label
from app.business.info_base.storage import WritableStorage
from app.business.source import SourceManager
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockForm, BlockModel
from app.schemas.info_base.relation import RelationModel
from app.schemas.source import SourceModel

from .adapter import MailAdapterError, create_mail_adapter, decode_transfer
from .repository import (
  EMAIL_ADDRESS_RESOLVER,
  EMAIL_RESOLVER,
  HTML_RESOLVER,
  MAILBOX_RESOLVER,
  MAIL_FLAG_RESOLVER,
  MIME_PART_RESOLVER,
  TEXT_RESOLVER,
)
from .schema import (
  CanonicalEmail,
  CanonicalEmailAddress,
  CanonicalMailbox,
  CanonicalMailFlag,
  CanonicalMimePart,
  MailSourceConfig,
  MailSourceState,
  SolvedBlock,
  SolvedEmail,
  SolvedMimePart,
)


class MailMaterializationUnavailable(RuntimeError):
  """No exact live remote occurrence can supply the requested MIME content."""


def _json(content: str) -> dict[str, typing.Any] | None:
  try:
    value = json.loads(content)
  except (TypeError, json.JSONDecodeError):
    return None
  return value if isinstance(value, dict) else None


def _persisted_id(block: BlockModel) -> int:
  if block.id is None:
    raise RuntimeError("Persisted Block has no ID")
  return block.id


async def _solve_block(block: BlockModel, *, refresh: bool = False) -> SolvedBlock:
  resolver = ResolverManager.get(block)
  solved = await resolver.get_solved_content(
    refresh=refresh,
    materialize_missing=False,
  )
  return SolvedBlock(block=block, solved_content=solved)


class EmailResolver(
  Resolver[CanonicalEmail | SolvedEmail, str],
  rso_type=EMAIL_RESOLVER,
):
  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> SolvedEmail:
    del materialize_missing
    root = CanonicalEmail.model_validate_json(await self.get_raw_content(refresh=refresh))
    relations = await self.get_relations(refresh=refresh)
    block_ids = {
      relation.to_ if relation.from_ == self.block_id else relation.from_
      for relation in relations
    }
    with SessionLocal() as db:
      blocks = {
        block.id: block
        for block_id in block_ids
        if (block := db.get(BlockModel, block_id)) is not None
      }

    bodies: list[SolvedBlock] = []
    mime_parts: list[SolvedBlock] = []
    participants: list[dict[str, typing.Any]] = []
    mailboxes: list[dict[str, typing.Any]] = []
    flags: list[dict[str, typing.Any]] = []
    parents: list[SolvedBlock] = []
    references: list[SolvedBlock] = []
    for relation in relations:
      if relation.from_ == self.block_id:
        target = blocks.get(relation.to_)
        if target is None:
          continue
        value = _json(relation.content)
        if (
          value
          and value.get("role") == "body"
          and target.resolver
          in {
            TEXT_RESOLVER,
            HTML_RESOLVER,
          }
        ):
          bodies.append(await _solve_block(target, refresh=refresh))
        elif (
          value
          and value.get("role") in {"attachment", "inline"}
          and target.resolver == MIME_PART_RESOLVER
        ):
          mime_parts.append(await _solve_block(target, refresh=refresh))
        elif (
          value
          and value.get("role")
          in {
            "from",
            "sender",
            "reply_to",
            "to",
            "cc",
            "bcc",
          }
          and target.resolver == EMAIL_ADDRESS_RESOLVER
        ):
          participants.append(
            {"relation": value, "address": await _solve_block(target, refresh=refresh)}
          )
        elif relation.content.startswith("parent:") and target.resolver == EMAIL_RESOLVER:
          parents.append(await _solve_block(target, refresh=refresh))
        elif (
          relation.content.startswith("reference:") and target.resolver == EMAIL_RESOLVER
        ):
          references.append(await _solve_block(target, refresh=refresh))
      else:
        source = blocks.get(relation.from_)
        if source is None:
          continue
        value = _json(relation.content)
        if (
          value and value.get("type") == "contains" and source.resolver == MAILBOX_RESOLVER
        ):
          mailboxes.append(
            {"relation": value, "mailbox": await _solve_block(source, refresh=refresh)}
          )
        elif relation.content == "tags" and source.resolver == MAIL_FLAG_RESOLVER:
          flags.append({"flag": await _solve_block(source, refresh=refresh)})
    return SolvedEmail(
      root=root,
      bodies=tuple(bodies),
      mime_parts=tuple(mime_parts),
      participants=tuple(participants),
      mailboxes=tuple(mailboxes),
      flags=tuple(flags),
      parents=tuple(parents),
      references=tuple(references),
    )

  async def get_text(
    self,
    *,
    context: TextProjectionContext = "default",
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    solved = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    if isinstance(solved, CanonicalEmail):
      return solved.subject or solved.message_id or "email"
    body_texts = (
      []
      if context == "lexical"
      else [
        text
        for body in solved.bodies
        if (
          text := await ResolverManager.get(body.block).get_text(
            refresh=refresh,
            materialize_missing=False,
          )
        )
      ]
    )
    return "\n\n".join(item for item in (solved.root.subject, *body_texts) if item) or (
      solved.root.message_id or "email"
    )

  async def get_label(self, *, refresh: bool = False) -> str:
    root = CanonicalEmail.model_validate_json(await self.get_raw_content(refresh=refresh))
    return format_label("email", root.subject or root.message_id)


class MailboxResolver(
  Resolver[CanonicalMailbox, str],
  rso_type=MAILBOX_RESOLVER,
):
  def __post_init__(self, raw_content=None) -> None:
    if raw_content is not None:
      self.set_solved_content(CanonicalMailbox.model_validate_json(raw_content))

  async def _get_solved_content(self, *, refresh=False, materialize_missing=True):
    del materialize_missing
    return CanonicalMailbox.model_validate_json(await self.get_raw_content(refresh=refresh))

  async def get_text(
    self,
    *,
    context: TextProjectionContext = "default",
    refresh=False,
    materialize_missing=True,
  ) -> str:
    del context, materialize_missing
    mailbox = await self.get_solved_content(refresh=refresh)
    roles = ", ".join(mailbox.special_uses)
    return mailbox.name if not roles else f"{mailbox.name}\nSpecial uses: {roles}"

  async def get_label(self, *, refresh=False) -> str:
    mailbox = await self.get_solved_content(refresh=refresh)
    return format_label("mailbox", mailbox.name)


class EmailAddressResolver(
  Resolver[CanonicalEmailAddress, str],
  rso_type=EMAIL_ADDRESS_RESOLVER,
):
  def __post_init__(self, raw_content=None) -> None:
    if raw_content is not None:
      self.set_solved_content(CanonicalEmailAddress.model_validate_json(raw_content))

  async def _get_solved_content(self, *, refresh=False, materialize_missing=True):
    del materialize_missing
    return CanonicalEmailAddress.model_validate_json(
      await self.get_raw_content(refresh=refresh)
    )

  async def get_text(
    self,
    *,
    context: TextProjectionContext = "default",
    refresh=False,
    materialize_missing=True,
  ) -> str:
    del context, materialize_missing
    return (await self.get_solved_content(refresh=refresh)).address

  async def get_label(self, *, refresh=False) -> str:
    address = await self.get_solved_content(refresh=refresh)
    return format_label("email address", address.address)


class MailFlagResolver(
  Resolver[CanonicalMailFlag, str],
  rso_type=MAIL_FLAG_RESOLVER,
):
  def __post_init__(self, raw_content=None) -> None:
    if raw_content is not None:
      self.set_solved_content(CanonicalMailFlag.model_validate_json(raw_content))

  async def _get_solved_content(self, *, refresh=False, materialize_missing=True):
    del materialize_missing
    return CanonicalMailFlag.model_validate_json(
      await self.get_raw_content(refresh=refresh)
    )

  async def get_text(
    self,
    *,
    context: TextProjectionContext = "default",
    refresh=False,
    materialize_missing=True,
  ) -> str:
    del context, materialize_missing
    flag = await self.get_solved_content(refresh=refresh)
    return flag.name if flag.description is None else f"{flag.name}: {flag.description}"

  async def get_label(self, *, refresh=False) -> str:
    flag = await self.get_solved_content(refresh=refresh)
    return format_label("mail flag", flag.name)


class MailMimePartResolver(
  Resolver[SolvedMimePart, str],
  rso_type=MIME_PART_RESOLVER,
):
  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> SolvedMimePart:
    root = CanonicalMimePart.model_validate_json(
      await self.get_raw_content(refresh=refresh)
    )
    existing = InfoBaseManager.get_related_block(self.block_id, content="content")
    if existing is not None:
      return SolvedMimePart(
        root=root,
        content=await _solve_block(existing, refresh=refresh),
      )
    if not materialize_missing:
      return SolvedMimePart(root=root)
    child = await self._materialize(root)
    return SolvedMimePart(root=root, content=await _solve_block(child, refresh=refresh))

  async def _materialize(self, root: CanonicalMimePart) -> BlockModel:
    context = self._resolve_remote_context()
    source, mailbox_name, uid, part_id = context
    setup = MailSourceConfig.model_validate(source.config)
    state = MailSourceState.model_validate(source.state or {})
    adapter = create_mail_adapter(setup.protocol, setup.parameters)
    try:
      async with adapter:
        if state.binding is None or state.binding != adapter.binding:
          raise MailMaterializationUnavailable("Mail Source access binding is unavailable")
        raw = await adapter.fetch_part(mailbox_name, uid, part_id)
    except MailAdapterError as error:
      raise MailMaterializationUnavailable(str(error)) from error
    content = decode_transfer(raw, root.transfer_encoding)
    declared = ResolverManager.match_media_type(root.media_type)
    detected = ResolverManager.match_media_type(detect_media_type(content))
    resolver_id = declared or detected or "core.file.v1"
    if resolver_id in {TEXT_RESOLVER, HTML_RESOLVER}:
      try:
        rendered = content.decode(root.charset or "utf-8", errors="replace")
      except LookupError:
        rendered = content.decode("utf-8", errors="replace")
      content = rendered.encode("utf-8")

    with SessionLocal() as db:
      metadata = db.exec(
        sqlmodel.select(BlockModel).where(BlockModel.id == self.block_id).with_for_update()
      ).one()
      existing = InfoBaseManager.get_related_block(
        self.block_id,
        content="content",
        db_session=db,
      )
      if existing is not None:
        db.commit()
        return existing
      live_source = db.get(SourceModel, source.id)
      if live_source is None:
        raise MailMaterializationUnavailable("Mail Source no longer exists")
      storage = SourceManager.resolve_writable_storage(live_source, db)
      if not isinstance(storage, WritableStorage):  # registry/catalog invariant
        raise TypeError("Resolved target Storage is not writable")
      pointer = storage.create_raw_content(content, db)
      child = BlockManager.create(
        BlockForm(
          storage=storage.storage_id,
          resolver=resolver_id,
          content=pointer,
        ),
        db,
      )
      from app.business.info_base.relation import RelationManager

      RelationManager.create(
        _persisted_id(metadata),
        _persisted_id(child),
        "content",
        db,
      )
      db.commit()
      db.refresh(child)
      return child

  def _resolve_remote_context(self) -> tuple[SourceModel, str, int, str]:
    """Derive one exact live locator through MIME part -> Email -> Mailbox -> Source."""
    with SessionLocal() as db:
      owner_relations = db.exec(
        sqlmodel.select(RelationModel).where(RelationModel.to_ == self.block_id)
      ).all()
      owners: list[tuple[int, str]] = []
      for relation in owner_relations:
        value = _json(relation.content)
        owner = db.get(BlockModel, relation.from_)
        if (
          value
          and value.get("role") in {"attachment", "inline"}
          and isinstance(value.get("part_id"), str)
          and owner is not None
          and owner.resolver == EMAIL_RESOLVER
        ):
          owners.append((_persisted_id(owner), value["part_id"]))
      if len(owners) != 1:
        raise MailMaterializationUnavailable("MIME part has no unique owning Email")
      email_id, part_id = owners[0]
      occurrences = db.exec(
        sqlmodel.select(RelationModel).where(RelationModel.to_ == email_id)
      ).all()
      for occurrence in occurrences:
        locator = _json(occurrence.content)
        mailbox = db.get(BlockModel, occurrence.from_)
        if (
          not locator
          or locator.get("type") != "contains"
          or not isinstance(locator.get("uid"), int)
          or mailbox is None
          or mailbox.resolver != MAILBOX_RESOLVER
        ):
          continue
        manages = db.exec(
          sqlmodel.select(RelationModel).where(
            RelationModel.to_ == mailbox.id,
            RelationModel.content == "manages",
          )
        ).all()
        for manages_relation in manages:
          source = db.exec(
            sqlmodel.select(SourceModel).where(SourceModel.block == manages_relation.from_)
          ).one_or_none()
          if source is None or source.type != "extensions.mail.source.Source":
            continue
          mailbox_content = CanonicalMailbox.model_validate_json(mailbox.content)
          return source, mailbox_content.name, locator["uid"], part_id
    raise MailMaterializationUnavailable("No live exact Mail occurrence is available")

  async def get_text(
    self,
    *,
    context: TextProjectionContext = "default",
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    del context, materialize_missing
    root = CanonicalMimePart.model_validate_json(
      await self.get_raw_content(refresh=refresh)
    )
    return "\n".join(
      item
      for item in (
        root.filename,
        root.description,
        root.media_type,
      )
      if item
    )

  async def get_label(self, *, refresh: bool = False) -> str:
    root = CanonicalMimePart.model_validate_json(
      await self.get_raw_content(refresh=refresh)
    )
    return format_label(
      "mail MIME part", root.filename or root.description or root.media_type
    )
