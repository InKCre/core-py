"""Attachment graph ownership and application commands."""

import datetime

import sqlmodel

from app.business.info_base.block import BlockManager
from app.business.info_base.relation import RelationManager
from app.business.info_base.resolver import ResolverManager
from app.business.info_base.storage import StorageManager, WritableStorage
from app.business.info_base.storage.postgresql import StorageBlobNotFoundError
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel

from .graph import (
  ATTACHMENT_RELATION_PREFIX,
  ATTACHMENT_RESOLVER,
  MemoGraphRepository,
)
from .schema import CanonicalAttachment, SolvedAttachment


DATABASE_BINARY_STORAGE_ID = -4


class AttachmentNotFoundError(LookupError):
  pass


class AttachmentOwnershipError(ValueError):
  pass


class AttachmentGraphRepository:
  @classmethod
  def get_block(
    cls,
    attachment_id: int,
    db_session: sqlmodel.Session,
  ) -> BlockModel | None:
    block = BlockManager.get(attachment_id, db_session)
    if block is None or block.resolver != ATTACHMENT_RESOLVER:
      return None
    return block

  @classmethod
  def owner_relation(
    cls,
    attachment_id: int,
    db_session: sqlmodel.Session,
  ) -> RelationModel | None:
    relations = tuple(
      relation
      for relation in RelationManager.get(
        attachment_id,
        include_in=True,
        include_out=False,
        db_session=db_session,
      )
      if relation.content.startswith(ATTACHMENT_RELATION_PREFIX)
    )
    if len(relations) > 1:
      raise AttachmentOwnershipError(
        f"Attachment attachments/{attachment_id} has multiple memo owners"
      )
    return relations[0] if relations else None

  @classmethod
  def create(
    cls,
    *,
    filename: str,
    media_type: str,
    content: bytes,
    created_at: datetime.datetime,
    db_session: sqlmodel.Session,
  ) -> BlockModel:
    storage = StorageManager.get_storage(DATABASE_BINARY_STORAGE_ID, db_session)
    if not isinstance(storage, WritableStorage):
      raise TypeError("Configured PostgreSQL binary storage is not writable")
    blob_id = storage.write_raw_content(content, db_session)
    canonical = CanonicalAttachment(
      filename=filename,
      media_type=media_type,
      size=len(content),
      created_at=created_at,
      blob_id=blob_id,
    )
    return BlockManager.create(
      BlockModel(
        resolver=ATTACHMENT_RESOLVER,
        storage=DATABASE_BINARY_STORAGE_ID,
        content=canonical.to_block_content(),
      ),
      db_session,
    )

  @classmethod
  def current_attachment_relations(
    cls,
    memo_id: int,
    db_session: sqlmodel.Session,
  ) -> dict[int, RelationModel]:
    positions: dict[int, RelationModel] = {}
    for relation in RelationManager.get(
      memo_id,
      include_in=False,
      include_out=True,
      db_session=db_session,
    ):
      if not relation.content.startswith(ATTACHMENT_RELATION_PREFIX):
        continue
      raw_position = relation.content.removeprefix(ATTACHMENT_RELATION_PREFIX)
      if not raw_position.isdigit():
        raise ValueError(f"Invalid attachment relation: {relation.content}")
      position = int(raw_position)
      if position in positions:
        raise ValueError(f"Duplicate attachment position: {position}")
      positions[position] = relation
    if positions and sorted(positions) != list(range(len(positions))):
      raise ValueError("Attachment positions must be contiguous and zero-based")
    return positions

  @classmethod
  def set_memo_attachments(
    cls,
    memo_id: int,
    attachment_ids: tuple[int, ...],
    db_session: sqlmodel.Session,
  ) -> None:
    if len(set(attachment_ids)) != len(attachment_ids):
      raise AttachmentOwnershipError("Attachment list contains duplicate identities")
    if MemoGraphRepository.get_root(memo_id, db_session) is None:
      raise AttachmentNotFoundError(f"Memo memos/{memo_id} not found")

    for attachment_id in attachment_ids:
      if cls.get_block(attachment_id, db_session) is None:
        raise AttachmentNotFoundError(f"Attachment attachments/{attachment_id} not found")
      owner = cls.owner_relation(attachment_id, db_session)
      if owner is not None and owner.from_ != memo_id:
        raise AttachmentOwnershipError(
          f"Attachment attachments/{attachment_id} already has an owner"
        )

    current = cls.current_attachment_relations(memo_id, db_session)
    current_ids = {relation.to_ for relation in current.values()}
    requested_ids = set(attachment_ids)

    for position, attachment_id in enumerate(attachment_ids):
      relation = current.get(position)
      if relation is None:
        RelationManager.create(
          memo_id,
          attachment_id,
          f"{ATTACHMENT_RELATION_PREFIX}{position}",
          db_session,
        )
      elif relation.to_ != attachment_id:
        if relation.id is None:
          raise RuntimeError("Persisted attachment relation has no ID")
        RelationManager.update(relation.id, to_=attachment_id, db_session=db_session)

    for position, relation in current.items():
      if position >= len(attachment_ids):
        if relation.id is None:
          raise RuntimeError("Persisted attachment relation has no ID")
        RelationManager.delete(relation.id, db_session)

    for removed_id in current_ids - requested_ids:
      cls.delete_component(removed_id, db_session)

  @classmethod
  def delete_component(
    cls,
    attachment_id: int,
    db_session: sqlmodel.Session,
  ) -> bool:
    block = cls.get_block(attachment_id, db_session)
    if block is None:
      return False
    storage = StorageManager.get_storage(DATABASE_BINARY_STORAGE_ID, db_session)
    if not isinstance(storage, WritableStorage):
      raise TypeError("Configured PostgreSQL binary storage is not writable")
    storage.delete_raw_content(block.content, db_session)
    return BlockManager.delete(attachment_id, db_session)


class AttachmentApplicationService:
  @classmethod
  async def create(
    cls,
    *,
    filename: str,
    media_type: str,
    content: bytes,
    memo_id: int | None = None,
    now: datetime.datetime | None = None,
  ) -> SolvedAttachment:
    created_at = now or datetime.datetime.now(datetime.UTC)
    with SessionLocal() as db_session:
      if memo_id is not None and MemoGraphRepository.get_root(memo_id, db_session) is None:
        raise AttachmentNotFoundError(f"Memo memos/{memo_id} not found")
      block = AttachmentGraphRepository.create(
        filename=filename,
        media_type=media_type,
        content=content,
        created_at=created_at,
        db_session=db_session,
      )
      if block.id is None:
        raise RuntimeError("Persisted attachment block has no ID")
      if memo_id is not None:
        current = AttachmentGraphRepository.current_attachment_relations(
          memo_id, db_session
        )
        AttachmentGraphRepository.set_memo_attachments(
          memo_id,
          tuple(relation.to_ for _, relation in sorted(current.items())) + (block.id,),
          db_session,
        )
      db_session.commit()
      db_session.refresh(block)
    return await cls._solve(block)

  @classmethod
  async def list(cls) -> tuple[SolvedAttachment, ...]:
    with SessionLocal() as db_session:
      blocks = tuple(
        db_session.exec(
          sqlmodel.select(BlockModel)
          .where(BlockModel.resolver == ATTACHMENT_RESOLVER)
          .order_by(
            sqlmodel.desc(BlockModel.created_at),
            sqlmodel.desc(BlockModel.id),
          )
        ).all()
      )
    return tuple([await cls._solve(block) for block in blocks])

  @classmethod
  async def download(cls, attachment_id: int, filename: str) -> tuple[str, bytes]:
    with SessionLocal() as db_session:
      block = AttachmentGraphRepository.get_block(attachment_id, db_session)
    if block is None:
      raise AttachmentNotFoundError(f"Attachment attachments/{attachment_id} not found")
    solved = await cls._solve(block)
    if solved.canonical.filename != filename:
      raise AttachmentNotFoundError(
        f"Attachment filename does not match attachments/{attachment_id}"
      )
    try:
      content = await ResolverManager.get(block).get_raw_content()
    except StorageBlobNotFoundError as error:
      raise AttachmentNotFoundError(str(error)) from error
    if not isinstance(content, bytes):
      raise TypeError("Attachment storage returned non-binary content")
    return solved.canonical.media_type, content

  @classmethod
  def delete(cls, attachment_id: int) -> None:
    with SessionLocal() as db_session:
      if not AttachmentGraphRepository.delete_component(attachment_id, db_session):
        raise AttachmentNotFoundError(f"Attachment attachments/{attachment_id} not found")
      db_session.commit()

  @classmethod
  async def _solve(cls, block: BlockModel) -> SolvedAttachment:
    solved = await ResolverManager.get(block).get_solved_content()
    if not isinstance(solved, SolvedAttachment):
      raise TypeError("Attachment resolver returned an unexpected solved value")
    return solved
