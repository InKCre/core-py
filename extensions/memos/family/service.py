"""Application commands over memo-family graph authority."""

from app.business.info_base.resolver import ResolverManager
from app.persistence.info_base.uow import graph_uow
from libs.obsrv.main import get_logger

from .graph import (
  MEMO_RESOLVER,
  PARENT_RELATION,
  MemoGraph,
  select_top_level_roots,
)
from .attachment import AttachmentGraph
from .schema import (
  CanonicalMemo,
  CanonicalMemoPatch,
  CommentPage,
  MemoCursor,
  MemoPage,
  SolvedMemo,
)


logger = get_logger()


class MemoNotFoundError(LookupError):
  pass


class MemoApplicationService:
  """Coordinate memo commands while leaving protocol mapping to product adapters."""

  @classmethod
  async def create(
    cls,
    canonical: CanonicalMemo,
    *,
    attachment_ids: tuple[int, ...] = (),
  ) -> SolvedMemo:
    async with graph_uow() as uow:
      block = await MemoGraph.create_root(canonical, uow)
      if block.id is None:
        raise RuntimeError("Persisted memo root has no ID")
      await AttachmentGraph.set_memo_attachments(
        block.id,
        attachment_ids,
        uow,
      )

    solved = await ResolverManager.get(block).get_solved_content()
    if not isinstance(solved, SolvedMemo):
      raise TypeError("Memo resolver returned an unexpected solved value")
    return solved

  @classmethod
  async def create_comment(
    cls,
    parent_id: int,
    canonical: CanonicalMemo,
    *,
    attachment_ids: tuple[int, ...] = (),
  ) -> SolvedMemo:
    async with graph_uow() as uow:
      parent = await MemoGraph.get_root(parent_id, uow)
      if parent is None:
        raise MemoNotFoundError(f"Memo memos/{parent_id} not found")
      parent_canonical = CanonicalMemo.from_block_content(parent.content)
      comment_canonical = canonical.model_copy(
        update={"visibility": parent_canonical.visibility}
      )
      block = await MemoGraph.create_comment(
        parent_id,
        comment_canonical,
        uow,
      )
      if block.id is None:
        raise RuntimeError("Persisted memo comment has no ID")
      await AttachmentGraph.set_memo_attachments(
        block.id,
        attachment_ids,
        uow,
      )

    solved = await ResolverManager.get(block).get_solved_content()
    if not isinstance(solved, SolvedMemo):
      raise TypeError("Memo resolver returned an unexpected solved value")
    return solved

  @classmethod
  async def update(
    cls,
    block_id: int,
    patch: CanonicalMemoPatch | None,
    *,
    attachment_ids: tuple[int, ...] | None = None,
  ) -> SolvedMemo:
    if patch is None and attachment_ids is None:
      raise ValueError("Memo update must select root fields or attachments")
    async with graph_uow() as uow:
      block = await MemoGraph.get_root(block_id, uow, lock=True)
      if block is None:
        raise MemoNotFoundError(f"Memo memos/{block_id} not found")
      if patch is not None:
        canonical = CanonicalMemo.from_block_content(block.content)
        updated = patch.apply(canonical)
        parents = await uow.relations.get(
          block_id, include_in=False, include_out=True, content=PARENT_RELATION
        )
        if len(parents) > 1:
          raise ValueError(f"Memo memos/{block_id} has multiple parent relations")
        if parents:
          parent = await MemoGraph.get_root(parents[0].to_, uow)
          if parent is None:
            raise ValueError(f"Memo memos/{block_id} has a missing parent")
          parent_canonical = CanonicalMemo.from_block_content(parent.content)
          updated = updated.model_copy(update={"visibility": parent_canonical.visibility})
        block = await uow.blocks.edit_block(block_id, content=updated.to_block_content())
      if attachment_ids is not None:
        await AttachmentGraph.set_memo_attachments(
          block_id,
          attachment_ids,
          uow,
        )

    solved = await ResolverManager.get(block).get_solved_content()
    if not isinstance(solved, SolvedMemo):
      raise TypeError("Memo resolver returned an unexpected solved value")
    return solved

  @classmethod
  async def list_top_level(
    cls,
    *,
    archived: bool,
    limit: int,
    after: MemoCursor | None = None,
  ) -> MemoPage:
    async with graph_uow() as uow:
      blocks = await uow.blocks.get_by_resolvers((MEMO_RESOLVER,))
      parent_root_ids = {
        relation.from_
        for relation in await uow.relations.get_outgoing_many(
          tuple(block.id for block in blocks if block.id is not None),
          content=PARENT_RELATION,
        )
      }

    selected, next_cursor = select_top_level_roots(
      blocks,
      parent_root_ids=parent_root_ids,
      archived=archived,
      after=after,
      limit=limit,
    )
    solved_memos: list[SolvedMemo] = []
    for block in selected:
      solved = await ResolverManager.get(block).get_solved_content()
      if not isinstance(solved, SolvedMemo):
        raise TypeError("Memo resolver returned an unexpected solved value")
      solved_memos.append(solved)
    return MemoPage(memos=tuple(solved_memos), next_cursor=next_cursor)

  @classmethod
  async def list_comments(
    cls,
    parent_id: int,
    *,
    limit: int,
    after_block_id: int | None = None,
  ) -> CommentPage:
    async with graph_uow() as uow:
      try:
        blocks, next_block_id, total_size = await MemoGraph.list_comment_roots(
          parent_id,
          limit=limit,
          after_block_id=after_block_id,
          uow=uow,
        )
      except LookupError as error:
        raise MemoNotFoundError(str(error)) from error

    comments: list[SolvedMemo] = []
    for block in blocks:
      solved = await ResolverManager.get(block).get_solved_content()
      if not isinstance(solved, SolvedMemo):
        raise TypeError("Memo resolver returned an unexpected solved value")
      comments.append(solved)
    return CommentPage(
      comments=tuple(comments),
      next_block_id=next_block_id,
      total_size=total_size,
    )

  @classmethod
  async def delete(cls, block_id: int) -> None:
    async with graph_uow() as uow:
      try:
        plan = await MemoGraph.owned_deletion_plan(block_id, uow)
      except LookupError as error:
        raise MemoNotFoundError(str(error)) from error
      if not await uow.blocks.delete(block_id):
        raise MemoNotFoundError(f"Memo memos/{block_id} not found")

    for comment_id in plan.comment_ids:
      try:
        async with graph_uow() as uow:
          await uow.blocks.delete(comment_id)

      except Exception:
        logger.exception(
          "Best-effort memo comment cleanup failed",
          extra={"memo_id": block_id, "comment_id": comment_id},
        )

    for attachment_id in plan.attachment_ids:
      try:
        async with graph_uow() as uow:
          await AttachmentGraph.delete_component(attachment_id, uow)

      except Exception:
        logger.exception(
          "Best-effort memo attachment cleanup failed",
          extra={"memo_id": block_id, "attachment_id": attachment_id},
        )
