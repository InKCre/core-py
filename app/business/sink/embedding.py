"""Embedding Manager for RAG Sink

This module manages embeddings for blocks and relations.
Embeddings are created/updated here as they are part of the RAG sink (output/usage of info-base).
"""

__all__ = ["EmbeddingManager"]

import asyncio
import sqlmodel
from typing import Optional as Opt
from app.engine import SessionLocal
from libs.obsrv.main import get_logger
from libs.ai import Embedding
from app.schemas.sink.embedding import BlockEmbeddingModel, RelationEmbeddingModel
from app.schemas.info_base.block import BlockModel, BlockID
from app.schemas.info_base.relation import RelationModel, RelationID
from app.schemas.info_base.main import Vector

logger = get_logger()


class EmbeddingManager:
  @classmethod
  async def upsert_block_embedding(
    cls, block: BlockModel, db_session: Opt[sqlmodel.Session] = None
  ) -> BlockEmbeddingModel:
    """Upsert a block's embedding

    :param block: Block to create/update embedding for
    :param db_session: Optional database session, if provided uses that session; won't commit.
    """
    from app.business.info_base.resolver import ResolverManager

    resolver = ResolverManager.new_resolver(block)
    embedding = BlockEmbeddingModel(
      id=block.id,  # type: ignore[arg-type]
      embedding=Embedding("", "text-embedding-v3").embed(resolver.get_str_for_embedding()),
    )
    if db_session:
      db_session.merge(embedding)
      return embedding
    with SessionLocal() as db_session:
      db_session.merge(embedding)
      db_session.commit()
      db_session.refresh(embedding)
    return embedding

  @classmethod
  async def upsert_relation_embedding(
    cls, relation: RelationModel, db_session: Opt[sqlmodel.Session] = None
  ) -> RelationEmbeddingModel:
    """Upsert a relation's embedding

    :param relation: Relation to create/update embedding for
    :param db_session: Optional database session, if provided uses that session; won't commit.
    """
    # For relations, we embed the content directly
    embedding = RelationEmbeddingModel(
      id=relation.id,  # type: ignore[arg-type]
      embedding=Embedding("", "text-embedding-v3").embed(relation.content),
    )
    if db_session:
      db_session.merge(embedding)
      return embedding
    with SessionLocal() as db_session:
      db_session.merge(embedding)
      db_session.commit()
      db_session.refresh(embedding)
    return embedding

  @classmethod
  async def refresh_all_block_embeddings(cls):
    """Rebuild all blocks' embeddings"""
    with SessionLocal() as db_session:
      blocks = db_session.exec(
        sqlmodel.select(BlockModel).where(
          BlockModel.resolver == "learn_english.lexical"
        )  # FIXME
      ).all()
      tasks = tuple(cls.upsert_block_embedding(block, db_session) for block in blocks)
      await asyncio.gather(*tasks)
      db_session.commit()

  @classmethod
  async def check_and_create_missing_embeddings(cls):
    """Check for blocks/relations missing embeddings and create them
    
    This is called periodically by the scheduler to ensure all content has embeddings.
    """
    logger.info("Checking for missing embeddings")
    with SessionLocal() as db_session:
      # Find blocks without embeddings
      blocks_without_embeddings = db_session.exec(
        sqlmodel.select(BlockModel)
        .outerjoin(BlockEmbeddingModel, BlockModel.id == BlockEmbeddingModel.id)
        .where(BlockEmbeddingModel.id.is_(None))
        .limit(10)  # Process in batches to avoid long-running jobs
      ).all()

      # Find relations without embeddings
      relations_without_embeddings = db_session.exec(
        sqlmodel.select(RelationModel)
        .outerjoin(RelationEmbeddingModel, RelationModel.id == RelationEmbeddingModel.id)
        .where(RelationEmbeddingModel.id.is_(None))
        .limit(10)  # Process in batches
      ).all()

      if blocks_without_embeddings:
        logger.info(
          f"Creating embeddings for {len(blocks_without_embeddings)} blocks"
        )
        block_tasks = tuple(
          cls.upsert_block_embedding(block, db_session) 
          for block in blocks_without_embeddings
        )
        await asyncio.gather(*block_tasks)

      if relations_without_embeddings:
        logger.info(
          f"Creating embeddings for {len(relations_without_embeddings)} relations"
        )
        relation_tasks = tuple(
          cls.upsert_relation_embedding(relation, db_session)
          for relation in relations_without_embeddings
        )
        await asyncio.gather(*relation_tasks)

      db_session.commit()

    if blocks_without_embeddings or relations_without_embeddings:
      logger.info(
        f"Created embeddings for {len(blocks_without_embeddings)} blocks "
        f"and {len(relations_without_embeddings)} relations"
      )

  @classmethod
  def query_blocks_by_embedding(
    cls,
    block_id: Opt[int] = None,
    embedding: Opt[Vector] = None,
    resolver: Opt[str] = None,
    num: int = 10,
    max_distance: float = 0.3,
  ) -> tuple[BlockModel, ...]:
    """Query blocks by cosine similarity

    :param block_id: Use embedding from existing block
    :param embedding: Use given embedding
    :param resolver: Filter by resolver type, None means no filter
    :param num: Number of results to return
    :param max_distance: Maximum cosine distance threshold
    """
    with SessionLocal() as db_session:
      if block_id is not None:
        base_embedding = db_session.exec(
          sqlmodel.select(BlockEmbeddingModel.embedding).where(
            BlockEmbeddingModel.id == block_id
          )
        ).one()
      else:
        if embedding is not None:
          base_embedding = embedding
        else:
          raise ValueError("one of block_id or embedding must be provided")

      similar_blocks = db_session.exec(
        sqlmodel.select(BlockModel)
        .select_from(BlockModel)
        .join(BlockEmbeddingModel, BlockEmbeddingModel.id == BlockModel.id)  # type: ignore
        .where(BlockModel.resolver == resolver if resolver else True)
        .where(BlockEmbeddingModel.embedding is not None)
        .where(BlockEmbeddingModel.id != block_id)
        .where(
          BlockEmbeddingModel.embedding.cosine_distance(base_embedding) < max_distance  # type: ignore
        )
        .order_by(BlockEmbeddingModel.embedding.cosine_distance(base_embedding))  # type: ignore
        .limit(num)
      ).all()

    return tuple(similar_blocks)  # type: ignore

  @classmethod
  def rerank_blocks(
    cls,
    query: str,
    blocks: tuple[BlockModel, ...],
    top_k: int = 5,
  ) -> tuple[BlockModel, ...]:
    """Rerank blocks using a more sophisticated method
    
    This uses cross-encoder or similar reranking approach to improve retrieval quality.
    Currently implements a simple score-based reranking using query embedding similarity.
    
    :param query: The search query
    :param blocks: Candidate blocks to rerank
    :param top_k: Number of top results to return after reranking
    """
    if not blocks:
      return tuple()

    # Generate query embedding
    query_embedding = Embedding("", "text-embedding-v3").embed(query)
    
    # Calculate scores for each block
    with SessionLocal() as db_session:
      block_scores: list[tuple[BlockModel, float]] = []
      
      for block in blocks:
        block_embedding = db_session.exec(
          sqlmodel.select(BlockEmbeddingModel.embedding).where(
            BlockEmbeddingModel.id == block.id
          )
        ).one_or_none()
        
        if block_embedding:
          # Calculate cosine distance (lower is better)
          # We'll use SQLAlchemy's cosine_distance for consistency
          distance = db_session.exec(
            sqlmodel.select(
              BlockEmbeddingModel.embedding.cosine_distance(query_embedding)  # type: ignore
            ).where(BlockEmbeddingModel.id == block.id)
          ).one()
          block_scores.append((block, distance))
      
      # Sort by distance (ascending) and take top_k
      block_scores.sort(key=lambda x: x[1])
      reranked_blocks = tuple(block for block, _ in block_scores[:top_k])
    
    return reranked_blocks
