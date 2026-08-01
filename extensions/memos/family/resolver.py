"""Versioned CanonicalMemo decoder and graph resolver."""

from app.business.info_base.resolver import Resolver
from app.schemas.info_base.block import BlockModel

from .graph import MEMO_RESOLVER, solve_memo_links
from .schema import CanonicalMemo, SolvedMemo


class MemoResolver(Resolver[SolvedMemo, str], rso_type=MEMO_RESOLVER):
  """Resolve CanonicalMemo v1 content together with graph-owned links."""

  def __post_init__(self, raw_content: str | None = None) -> None:
    if raw_content is None:
      raise ValueError("CanonicalMemo v1 requires inline JSON content")
    self._canonical = CanonicalMemo.from_block_content(raw_content)

  @classmethod
  def create_block(cls, content: CanonicalMemo, storage=None) -> BlockModel:
    if storage is not None:
      raise ValueError("CanonicalMemo v1 root content must be inline")
    return BlockModel(
      resolver=cls.__rsotype__,
      content=content.to_block_content(),
    )

  async def _get_solved_content(self) -> SolvedMemo:
    relations = await self.get_relations(include_in=False, include_out=True)
    links = solve_memo_links(self.block_id, relations)
    from .schema import SolvedAttachment

    attachments: list[SolvedAttachment] = []
    for attachment_id in links.attachment_ids:
      # Lazy imports preserve the core block/resolver registration boundary.
      from app.business.info_base.block import BlockManager
      from app.business.info_base.resolver import ResolverManager

      block = BlockManager.get(attachment_id)
      if block is None:
        raise ValueError(f"Attachment block {attachment_id} does not exist")
      solved = await ResolverManager.get(block).get_solved_content()
      if not isinstance(solved, SolvedAttachment):
        raise TypeError(f"Block {attachment_id} is not a solved attachment")
      attachments.append(solved)
    return SolvedMemo(
      block_id=self.block_id,
      canonical=self._canonical,
      attachments=tuple(attachments),
      parent_id=links.parent_id,
      reference_ids=links.reference_ids,
    )

  async def get_text(self) -> str:
    return self._canonical.body

  async def get_str_for_embedding(self) -> str:
    return self._canonical.body


__all__ = ["MemoResolver"]
