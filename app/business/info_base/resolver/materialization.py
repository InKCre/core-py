"""Shared mechanics for Resolver-owned faithful text derivations."""

import logging

from app.business.ai import AIManager
from app.schemas.ai import SystemMessage, UserContentPart, UserMessage


logger = logging.getLogger(__name__)


async def generate_faithful_text(
  *,
  model: int,
  instruction: str,
  media: UserContentPart,
) -> str | None:
  """Ask one exact configured Model for source-faithful text, without graph access."""
  response = await AIManager.chat(
    model,
    (
      SystemMessage(content=instruction),
      UserMessage(content=(media,)),
    ),
  )
  text = (response.content or "").strip()
  return text or None


def materialize_text_child(block_id: int, role: str, text: str) -> None:
  """Best-effort idempotent graph write for one exact information role."""
  from app.business.info_base.main import InfoBaseManager
  from app.schemas.info_base.main import GraphBlockForm, GraphForm, GraphRelationForm

  if InfoBaseManager.get_related_block(block_id, content=role) is not None:
    return
  InfoBaseManager.submit_graph(
    GraphForm(
      blocks=(GraphBlockForm(id=-1, resolver="core.text.v1", content=text),),
      relations=(GraphRelationForm(from_=block_id, to_=-1, content=role),),
    )
  )


async def try_materialize_model_text(
  *,
  block_id: int,
  role: str,
  model: int,
  instruction: str,
  media: UserContentPart,
) -> None:
  """Keep one unavailable derivation shallow while preserving diagnostic evidence."""
  from app.business.info_base.main import InfoBaseManager

  if InfoBaseManager.get_related_block(block_id, content=role) is not None:
    return
  try:
    text = await generate_faithful_text(
      model=model,
      instruction=instruction,
      media=media,
    )
    if text is not None:
      materialize_text_child(block_id, role, text)
  except Exception:
    logger.warning(
      "Resolver text materialization unavailable",
      exc_info=True,
      extra={"block": block_id, "role": role, "model": model},
    )
