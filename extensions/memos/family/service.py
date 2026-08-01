"""Application commands over memo-family graph authority."""

import sqlmodel

from app.business.info_base.block import BlockManager
from app.business.info_base.relation import RelationManager
from app.business.info_base.resolver import ResolverManager
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel
from libs.obsrv.main import get_logger

from .graph import (
  MEMO_RESOLVER,
  PARENT_RELATION,
  MemoGraphRepository,
  select_top_level_roots,
)
from .attachment import AttachmentGraphRepository
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
    with SessionLocal() as db_session:
      block = MemoGraphRepository.create_root(canonical, db_session)
      if block.id is None:
        raise RuntimeError("Persisted memo root has no ID")
      AttachmentGraphRepository.set_memo_attachments(
        block.id,
        attachment_ids,
        db_session,
      )
      db_session.commit()
      db_session.refresh(block)

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
    with SessionLocal() as db_session:
      parent = MemoGraphRepository.get_root(parent_id, db_session)
      if parent is None:
        raise MemoNotFoundError(f"Memo memos/{parent_id} not found")
      parent_canonical = CanonicalMemo.from_block_content(parent.content)
      comment_canonical = canonical.model_copy(
        update={"visibility": parent_canonical.visibility}
      )
      block = MemoGraphRepository.create_comment(
        parent_id,
        comment_canonical,
        db_session,
      )
      if block.id is None:
        raise RuntimeError("Persisted memo comment has no ID")
      AttachmentGraphRepository.set_memo_attachments(
        block.id,
        attachment_ids,
        db_session,
      )
      db_session.commit()
      db_session.refresh(block)

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
    with SessionLocal() as db_session:
      block = MemoGraphRepository.get_root(block_id, db_session)
      if block is None:
        raise MemoNotFoundError(f"Memo memos/{block_id} not found")
      if patch is not None:
        canonical = CanonicalMemo.from_block_content(block.content)
        updated = patch.apply(canonical)
        parents = RelationManager.get(
          block_id,
          include_in=False,
          include_out=True,
          content=PARENT_RELATION,
          db_session=db_session,
        )
        if len(parents) > 1:
          raise ValueError(f"Memo memos/{block_id} has multiple parent relations")
        if parents:
          parent = MemoGraphRepository.get_root(parents[0].to_, db_session)
          if parent is None:
            raise ValueError(f"Memo memos/{block_id} has a missing parent")
          parent_canonical = CanonicalMemo.from_block_content(parent.content)
          updated = updated.model_copy(update={"visibility": parent_canonical.visibility})
        block = BlockManager.edit_block(
          block_id,
          content=updated.to_block_content(),
          db_session=db_session,
        )
      if attachment_ids is not None:
        AttachmentGraphRepository.set_memo_attachments(
          block_id,
          attachment_ids,
          db_session,
        )
      db_session.commit()
      db_session.refresh(block)

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
    with SessionLocal() as db_session:
      blocks = tuple(
        db_session.exec(
          sqlmodel.select(BlockModel).where(BlockModel.resolver == MEMO_RESOLVER)
        ).all()
      )
      parent_root_ids = set(
        db_session.exec(
          sqlmodel.select(RelationModel.from_).where(
            RelationModel.content == PARENT_RELATION
          )
        ).all()
      )

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
    with SessionLocal() as db_session:
      try:
        blocks, next_block_id, total_size = MemoGraphRepository.list_comment_roots(
          parent_id,
          limit=limit,
          after_block_id=after_block_id,
          db_session=db_session,
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
  def delete(cls, block_id: int) -> None:
    with SessionLocal() as db_session:
      try:
        plan = MemoGraphRepository.owned_deletion_plan(block_id, db_session)
      except LookupError as error:
        raise MemoNotFoundError(str(error)) from error
      if not BlockManager.delete(block_id, db_session):
        raise MemoNotFoundError(f"Memo memos/{block_id} not found")
      db_session.commit()

    for comment_id in plan.comment_ids:
      try:
        with SessionLocal() as db_session:
          BlockManager.delete(comment_id, db_session)
          db_session.commit()
      except Exception:
        logger.exception(
          "Best-effort memo comment cleanup failed",
          extra={"memo_id": block_id, "comment_id": comment_id},
        )

    for attachment_id in plan.attachment_ids:
      try:
        with SessionLocal() as db_session:
          AttachmentGraphRepository.delete_component(attachment_id, db_session)
          db_session.commit()
      except Exception:
        logger.exception(
          "Best-effort memo attachment cleanup failed",
          extra={"memo_id": block_id, "attachment_id": attachment_id},
        )
