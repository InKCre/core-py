"""Versioned attachment metadata and owner resolver."""

from app.business.info_base.block import BlockManager
from app.business.info_base.resolver import Resolver, ResolverManager
from app.business.info_base.resolver.label import format_label

from .graph import ATTACHMENT_RELATION_PREFIX, ATTACHMENT_RESOLVER, CONTENT_RELATION
from .schema import CanonicalAttachment, SolvedAttachment


class AttachmentResolver(
  Resolver[SolvedAttachment, bytes],
  rso_type=ATTACHMENT_RESOLVER,
):
  def __post_init__(self, raw_content: bytes | None = None) -> None:
    self._canonical = CanonicalAttachment.from_block_content(self._block.content)

  async def _get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> SolvedAttachment:
    del materialize_missing
    if refresh:
      self._canonical = CanonicalAttachment.from_block_content(self._block.content)
    relations = await self.get_relations(refresh=refresh)
    owners = tuple(
      relation
      for relation in relations
      if relation.to_ == self.block_id
      and relation.content.startswith(ATTACHMENT_RELATION_PREFIX)
    )
    content_relations = tuple(
      relation
      for relation in relations
      if relation.from_ == self.block_id and relation.content == CONTENT_RELATION
    )
    if len(owners) > 1:
      raise ValueError(f"Attachment attachments/{self.block_id} has multiple owners")
    if len(content_relations) != 1:
      raise ValueError(
        f"Attachment attachments/{self.block_id} must have exactly one content relation"
      )
    content_block = BlockManager.get(content_relations[0].to_)
    if content_block is None:
      raise ValueError(
        f"Attachment content block {content_relations[0].to_} does not exist"
      )
    ResolverManager.get(content_block)
    return SolvedAttachment(
      block_id=self.block_id,
      content_block_id=content_relations[0].to_,
      canonical=self._canonical,
      owner_memo_id=owners[0].from_ if owners else None,
    )

  async def get_text(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str:
    del materialize_missing
    if refresh:
      self._canonical = CanonicalAttachment.from_block_content(self._block.content)
    return self._canonical.filename

  async def get_label(self, *, refresh: bool = False) -> str:
    if refresh:
      self._canonical = CanonicalAttachment.from_block_content(self._block.content)
    return format_label("memo attachment", self._canonical.filename)


__all__ = ["AttachmentResolver"]
