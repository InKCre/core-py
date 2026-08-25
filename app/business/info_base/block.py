__all__ = ["BlockManager"]

import random
import typing
import sqlmodel
from typing import Optional as Opt
from app.business.info_base.resolver.main import ResolverManager
from libs.obsrv.main import get_logger
from utils.types_ import Undefined, _undefined
from app.engine import SessionLocal
from app.schemas.info_base.block import (
  BlockForm,
  BlockID,
  BlockModel,
  ResolverType,
)
from app.schemas.info_base.storage import StorageID

if typing.TYPE_CHECKING:
  from app.business.info_base.resolver import Resolver

logger = get_logger()


def _new_block(form: BlockForm) -> BlockModel:
  """Project only base producer fields across the persistence boundary."""
  values = form.model_dump(include=set(BlockForm.model_fields))
  return BlockModel.model_validate(values)


class BlockManager:
  @classmethod
  def get_many(
    cls,
    block_ids: typing.Collection[BlockID],
    db_session: Opt[sqlmodel.Session] = None,
  ) -> tuple[BlockModel, ...]:
    """Return the existing Blocks from a bounded identity set."""
    if not block_ids:
      return ()
    if db_session is None:
      with SessionLocal() as owned_session:
        return cls.get_many(block_ids, owned_session)
    return tuple(
      db_session.exec(
        sqlmodel.select(BlockModel).where(BlockModel.id.in_(tuple(block_ids)))  # type: ignore[union-attr]
      ).all()
    )

  @classmethod
  def get_random(
    cls,
    db_session: Opt[sqlmodel.Session] = None,
  ) -> Opt[BlockModel]:
    """Return one existing Block without transferring all identities."""
    if db_session is None:
      with SessionLocal() as owned_session:
        return cls.get_random(owned_session)
    block_id_column = sqlmodel.col(BlockModel.id)
    count = db_session.exec(sqlmodel.select(sqlmodel.func.count(block_id_column))).one()
    if count == 0:
      return None
    offset = random.SystemRandom().randrange(count)
    return db_session.exec(
      sqlmodel.select(BlockModel).order_by(block_id_column).offset(offset).limit(1)
    ).one()

  @classmethod
  def get_recent(
    cls, num: int = 10, resolver: Opt[ResolverType] = None
  ) -> tuple[BlockModel, ...]:
    """获取最新的块

    按创建时间倒序排序。

    :param num: 获取的块数量
    :param resolver: 限定解析器类型, None则不限定
    """
    with SessionLocal() as db_session:
      blocks = db_session.exec(
        sqlmodel.select(BlockModel)
        .order_by(sqlmodel.desc(BlockModel.created_at))
        .where(BlockModel.resolver == resolver if resolver else True)
        .limit(num)
      ).all()

    return tuple(blocks)

  @classmethod
  def get(
    cls,
    block_id: BlockID,
    db_session: Opt[sqlmodel.Session] = None,
  ) -> Opt[BlockModel]:
    if db_session is None:
      with SessionLocal() as owned_session:
        return cls.get(block_id, owned_session)
    return db_session.exec(
      sqlmodel.select(BlockModel).where(BlockModel.id == block_id)
    ).one_or_none()

  @classmethod
  def get_resolver(cls, block_id: BlockID) -> Opt["Resolver"]:
    """Get resolver instance of the block"""
    from .resolver import ResolverManager

    block = cls.get(block_id)
    if block is None:
      return None
    return ResolverManager.get(block)

  @classmethod
  def create(cls, form: BlockForm, db_session: Opt[sqlmodel.Session] = None) -> BlockModel:
    block = _new_block(form)
    logger.info(
      "Creating block",
      extra={
        "resolver": block.resolver,
        "storage": block.storage,
        "content_length": len(block.content) if block.content else 0,
      },
    )
    if db_session is None:
      with SessionLocal() as db_session:
        db_session.add(block)
        db_session.commit()
        db_session.refresh(block)
    else:
      db_session.add(block)
      db_session.flush()
      db_session.refresh(block)

    logger.info(
      "Block created successfully",
      extra={"block_id": block.id, "resolver": block.resolver},
    )
    return block

  @classmethod
  def create_many(
    cls,
    forms: typing.Iterable[BlockForm],
    db_session: sqlmodel.Session,
  ) -> tuple[BlockModel, ...]:
    """Create a caller-owned batch with one persistence round trip.

    The caller owns the surrounding transaction. Returned models have their
    database-managed identities populated, but are not individually refreshed.
    """
    blocks = tuple(_new_block(form) for form in forms)
    if not blocks:
      return ()
    logger.info("Creating block batch", extra={"block_count": len(blocks)})
    db_session.add_all(blocks)
    db_session.flush()
    return blocks

  @classmethod
  async def fetchsert(cls, form: BlockForm, db_session: sqlmodel.Session) -> BlockModel:
    """Create if not exists, else return the existing one.

    Will NOT commit the session.
    """
    block = _new_block(form)
    resolver = ResolverManager.get(block)
    existing = resolver.get_existing(db_session)
    if existing is not None:
      logger.debug(
        "Block already exists, returning existing",
        extra={"block_id": existing.id, "resolver": existing.resolver},
      )
      return existing

    logger.info(
      "Flushing new block via fetchsert",
      extra={"resolver": block.resolver, "storage": block.storage},
    )
    db_session.add(block)
    db_session.flush()
    db_session.refresh(block)
    return block

  @classmethod
  def edit_block(
    cls,
    block_id: BlockID,
    content: Opt[str] = None,
    resolver: Opt[ResolverType] = None,
    storage: Opt[StorageID] | Undefined = _undefined,
    db_session: Opt[sqlmodel.Session] = None,
  ) -> BlockModel:
    """编辑块"""
    logger.info("Editing block", extra={"block_id": block_id})
    if db_session is None:
      with SessionLocal() as owned_session:
        block = cls.edit_block(
          block_id,
          content=content,
          resolver=resolver,
          storage=storage,
          db_session=owned_session,
        )
        owned_session.commit()
        owned_session.refresh(block)
        return block

    block = cls.get(block_id, db_session)
    if block is None:
      logger.warning("Block not found for editing", extra={"block_id": block_id})
      raise ValueError("Block not found")

    if content is not None:
      block.content = content
    if resolver is not None:
      block.resolver = resolver
    if storage is not _undefined:
      block.storage = storage  # type: ignore

    db_session.add(block)
    db_session.flush()
    db_session.refresh(block)

    logger.info("Block edited successfully", extra={"block_id": block.id})
    return block

  @classmethod
  def delete(
    cls,
    block_id: BlockID,
    db_session: Opt[sqlmodel.Session] = None,
  ) -> bool:
    """Delete a block, using the caller's transaction when supplied."""
    if db_session is None:
      with SessionLocal() as owned_session:
        deleted = cls.delete(block_id, owned_session)
        owned_session.commit()
        return deleted

    block = cls.get(block_id, db_session)
    if block is None:
      return False
    db_session.delete(block)
    db_session.flush()
    return True
