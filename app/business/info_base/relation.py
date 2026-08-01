import sqlmodel
import sqlalchemy
import typing
from typing import Optional as Opt
from app.engine import SessionLocal
from libs.obsrv.main import get_logger
from app.schemas.info_base.block import BlockID
from app.schemas.info_base.relation import RelationModel
from app.schemas.info_base.relation import RelationID
from utils.types_ import Undefined, _undefined

logger = get_logger()


class RelationManager:
  @classmethod
  def create(
    cls,
    from_: BlockID,
    to_: BlockID,
    content: str,
    db_session: Opt[sqlmodel.Session] = None,
  ) -> RelationModel:
    """Create a relation"""
    logger.info(
      "Creating relation",
      extra={
        "from_block": from_,
        "to_block": to_,
        "content": content,
      },
    )
    relation = RelationModel(from_=from_, to_=to_, content=content)
    if db_session is None:
      with SessionLocal() as owned_session:
        relation = cls.create(from_, to_, content, owned_session)
        owned_session.commit()
        owned_session.refresh(relation)
        return relation

    db_session.add(relation)
    db_session.flush()
    db_session.refresh(relation)

    logger.info(
      "Relation created successfully",
      extra={"relation_id": relation.id, "from_block": from_, "to_block": to_},
    )
    return relation

  @classmethod
  def fetchsert(
    cls, relation: RelationModel, db_session: sqlmodel.Session
  ) -> RelationModel:
    """Create if not exists, else return the existing one.

    Will NOT commit the session.
    """
    existing = db_session.exec(
      sqlmodel.select(RelationModel).where(
        RelationModel.content == relation.content,
        RelationModel.from_ == relation.from_,
        RelationModel.to_ == relation.to_,
      )
    ).one_or_none()
    if existing is not None:
      logger.debug(
        "Relation already exists, returning existing",
        extra={
          "relation_id": existing.id,
          "from_block": existing.from_,
          "to_block": existing.to_,
        },
      )
      return existing

    logger.info(
      "Flushing new relation via fetchsert",
      extra={
        "from_block": relation.from_,
        "to_block": relation.to_,
        "content": relation.content,
      },
    )
    db_session.add(relation)
    db_session.flush()
    db_session.refresh(relation)
    return relation

  @classmethod
  def get(
    cls,
    block_id: BlockID,
    include_in: bool = True,
    include_out: bool = True,
    content: Opt[str] = None,
    db_session: Opt[sqlmodel.Session] = None,
  ) -> tuple[RelationModel, ...]:
    """Get relations from/to a block

    :param include_in: Include the relations where the block is the target
    :param include_out: Include the relations where the block is the source
    :param content: If specified, filter relations by content (eq)
    """
    if not include_in and not include_out:
      return ()
    if db_session is None:
      with SessionLocal() as owned_session:
        return cls.get(
          block_id,
          include_in=include_in,
          include_out=include_out,
          content=content,
          db_session=owned_session,
        )

    directions: list[typing.Any] = []
    if include_in:
      directions.append(RelationModel.to_ == block_id)
    if include_out:
      directions.append(RelationModel.from_ == block_id)
    statement = sqlmodel.select(RelationModel).where(sqlalchemy.or_(*directions))
    if content is not None:
      statement = statement.where(RelationModel.content == content)
    res = db_session.exec(statement).all()

    return tuple(res)

  @classmethod
  def update(
    cls,
    relation_id: RelationID,
    *,
    from_: BlockID | Undefined = _undefined,
    to_: BlockID | Undefined = _undefined,
    content: str | Undefined = _undefined,
    db_session: Opt[sqlmodel.Session] = None,
  ) -> RelationModel:
    """Update selected relation facts in the caller's transaction when supplied."""
    if db_session is None:
      with SessionLocal() as owned_session:
        relation = cls.update(
          relation_id,
          from_=from_,
          to_=to_,
          content=content,
          db_session=owned_session,
        )
        owned_session.commit()
        owned_session.refresh(relation)
        return relation

    relation = db_session.exec(
      sqlmodel.select(RelationModel).where(RelationModel.id == relation_id)
    ).one_or_none()
    if relation is None:
      raise ValueError("Relation not found")
    if from_ is not _undefined:
      relation.from_ = from_  # type: ignore[assignment]
    if to_ is not _undefined:
      relation.to_ = to_  # type: ignore[assignment]
    if content is not _undefined:
      relation.content = content  # type: ignore[assignment]
    db_session.add(relation)
    db_session.flush()
    db_session.refresh(relation)
    return relation

  @classmethod
  def delete(
    cls,
    relation_id: RelationID,
    db_session: Opt[sqlmodel.Session] = None,
  ) -> bool:
    """Delete a relation, using the caller's transaction when supplied."""
    if db_session is None:
      with SessionLocal() as owned_session:
        deleted = cls.delete(relation_id, owned_session)
        owned_session.commit()
        return deleted

    relation = db_session.exec(
      sqlmodel.select(RelationModel).where(RelationModel.id == relation_id)
    ).one_or_none()
    if relation is None:
      return False
    db_session.delete(relation)
    db_session.flush()
    return True
