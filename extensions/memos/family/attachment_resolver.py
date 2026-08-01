"""Versioned attachment metadata and owner resolver."""

from app.business.info_base.resolver import Resolver

from .graph import ATTACHMENT_RESOLVER
from .schema import CanonicalAttachment, SolvedAttachment


class AttachmentResolver(
  Resolver[SolvedAttachment, bytes],
  rso_type=ATTACHMENT_RESOLVER,
):
  def __post_init__(self, raw_content: bytes | None = None) -> None:
    self._canonical = CanonicalAttachment.from_block_content(self._block.content)

  async def _get_solved_content(self) -> SolvedAttachment:
    relations = await self.get_relations(include_in=True, include_out=False)
    owners = tuple(
      relation for relation in relations if relation.content.startswith("attachment:")
    )
    if len(owners) > 1:
      raise ValueError(f"Attachment attachments/{self.block_id} has multiple owners")
    return SolvedAttachment(
      block_id=self.block_id,
      canonical=self._canonical,
      owner_memo_id=owners[0].from_ if owners else None,
    )

  async def get_text(self) -> str:
    return self._canonical.filename

  async def get_str_for_embedding(self) -> str:
    return f"{self._canonical.filename} ({self._canonical.media_type})"


__all__ = ["AttachmentResolver"]
