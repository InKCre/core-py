import sqlmodel
from typing import Optional as Opt
from app.engine import SessionLocal
from app.logging_config import get_logger
from ..schemas.block import BlockID
from ..schemas.relation import RelationModel

logger = get_logger()


class RelationManager:
    @classmethod
    def create(cls, from_: BlockID, to_: BlockID, content: str) -> RelationModel:
        """Create a relation"""
        logger.info(
            "Creating relation",
            extra={
                "from_block": from_,
                "to_block": to_,
                "content": content,
            }
        )
        relation = RelationModel(from_=from_, to_=to_, content=content)
        with SessionLocal() as db:
            db.add(relation)
            db.commit()
            db.refresh(relation)

        logger.info(
            "Relation created successfully",
            extra={"relation_id": relation.id, "from_block": from_, "to_block": to_}
        )
        return relation

    @classmethod
    def fetchsert(
        cls, relation: RelationModel, db_session: sqlmodel.Session
    ) -> RelationModel:
        """Create if not exists, else return the existing one.

        Will not commit the session.
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
                    "to_block": existing.to_
                }
            )
            return existing
        
        logger.info(
            "Creating new relation via fetchsert",
            extra={
                "from_block": relation.from_,
                "to_block": relation.to_,
                "content": relation.content
            }
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
    ) -> tuple[RelationModel, ...]:
        """Get relations from/to a block

        :param include_in: Include the relations where the block is the target
        :param include_out: Include the relations where the block is the source
        :param content: If specified, filter relations by content (eq)
        """
        with SessionLocal() as db:
            res = db.exec(
                sqlmodel.select(RelationModel)
                .where(((RelationModel.to_ == block_id) if include_in else True))
                .where(((RelationModel.from_ == block_id) if include_out else True))
                .where(((RelationModel.content == content) if content else True))
            ).all()

        return tuple(res)
