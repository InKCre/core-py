import asyncio
from typing import Literal as Lit, Optional as Opt

import fastapi
import sqlmodel

from app.business.info_base.block import BlockManager
from libs.ai import Chat, Message, MessageContent, Prompt, Embedding
from app.schemas.info_base.block import BlockID


async def _optional_resolver_text(resolver) -> str | None:
  from app.business.info_base.resolver import UnsupportedResolverCapability

  try:
    return await resolver.get_text()
  except UnsupportedResolverCapability:
    return None


async def _optional_block_text(block) -> str | None:
  from app.business.info_base.resolver import ResolverManager

  return await _optional_resolver_text(ResolverManager.get(block))


class SinkV1RAGResBody(sqlmodel.SQLModel):
  message: str


class SinkManager:
  type RetrieveMode = Lit["feature", "embedding", "reasoning"]

  @classmethod
  async def rag(  # noqa: PLR0913
    cls,
    query: str,
    context: Opt[str] = None,
    context_blocks: list[BlockID] = fastapi.Query([]),
    retrieve_mode: RetrieveMode = "embedding",
    use_reranker: bool = True,
    num_retrieve: int = 20,
    num_rerank: int = 5,
  ) -> SinkV1RAGResBody:
    """RAG (Retrieval Augmented Generation) endpoint

    :param query: User query
    :param context: Additional context string
    :param context_blocks: Additional context block IDs
    :param retrieve_mode: Retrieval mode - "embedding", "reasoning", or "feature"
    :param use_reranker: Whether to use reranker to improve retrieval results
    :param num_retrieve: Number of blocks to retrieve initially
    :param num_rerank: Number of blocks to keep after reranking
    """
    from .embedding import EmbeddingManager

    # retrieve from base
    if retrieve_mode == "reasoning":
      related_blocks = await BlockManager.query_by_reasoning(query=query)
      texts = await asyncio.gather(
        *(_optional_block_text(block) for block in related_blocks)
      )
      retrieve_result_prompt = MessageContent(
        content="\n".join(text for text in texts if text is not None)
      )
    elif retrieve_mode == "embedding":
      # Use embedding-based retrieval
      query_embedding = Embedding("", "text-embedding-v3").embed(query)
      related_blocks = EmbeddingManager.query_blocks_by_embedding(
        embedding=query_embedding,
        num=num_retrieve,
        max_distance=0.5,  # More lenient initial retrieval
      )

      # Apply reranker if enabled
      if use_reranker and related_blocks:
        related_blocks = EmbeddingManager.rerank_blocks(
          query=query,
          blocks=related_blocks,
          top_k=num_rerank,
        )

      # Convert blocks to text for LLM
      texts = await asyncio.gather(
        *(_optional_block_text(block) for block in related_blocks)
      )
      retrieve_result_prompt = MessageContent(
        content="\n".join(text for text in texts if text is not None)
      )
    else:
      raise NotImplementedError(f"Retrieve mode '{retrieve_mode}' not implemented")

    # context + context_blocks -> context_text
    context_text = context or ""
    if context_blocks:
      resolvers = [BlockManager.get_resolver(bid) for bid in context_blocks]
      block_content_texts = await asyncio.gather(
        *(_optional_resolver_text(resolver) for resolver in resolvers if resolver)
      )
      context_text += "\n".join(text for text in block_content_texts if text is not None)

    prompt = Prompt("sink_rag")
    prompt.format(
      query=query,
      context=context_text,
    )
    chat = Chat("", "qwen-plus")
    chat.add_messages(
      Message(role="system", content=prompt),
      Message(role="system", content=retrieve_result_prompt),
    )

    res = chat.complete()
    return SinkV1RAGResBody(message=res.content)
