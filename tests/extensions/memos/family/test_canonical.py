"""CanonicalMemo v1 content and graph resolver contracts."""

import asyncio
import datetime
from pathlib import Path

import pydantic
import pytest

from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel
from extensions.memos.family.graph import MemoGraphRepository
from extensions.memos.family.resolver import MemoResolver
from extensions.memos.family.schema import (
  CanonicalAttachment,
  CanonicalMemo,
  SolvedAttachment,
)


FIXTURE = Path(__file__).with_name("fixtures") / "canonical_memo_v1.json"
ATTACHMENT_FIXTURE = Path(__file__).with_name("fixtures") / "canonical_attachment_v2.json"


def _canonical() -> CanonicalMemo:
  return CanonicalMemo(
    body="A small thought #inkcre",
    created_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.timezone.utc),
    updated_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.timezone.utc),
    archived=False,
    visibility="private",
    pinned=False,
  )


def test_canonical_v1_has_deterministic_exact_root_content():
  canonical = _canonical()

  assert canonical.to_block_content() == FIXTURE.read_text(encoding="utf-8").strip()
  assert CanonicalMemo.from_block_content(canonical.to_block_content()) == canonical


def test_canonical_attachment_v2_has_deterministic_exact_content():
  canonical = CanonicalAttachment(
    filename="photo.png",
    media_type="image/png",
    size=3,
    created_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
  )

  assert (
    canonical.to_block_content() == ATTACHMENT_FIXTURE.read_text(encoding="utf-8").strip()
  )
  assert CanonicalAttachment.from_block_content(canonical.to_block_content()) == canonical


@pytest.mark.parametrize(
  "content",
  [
    '{"body":"x","created_at":null,"updated_at":null,"archived":false,'
    '"visibility":"private","pinned":false,"attachments":[]}',
    '{"body":"x","created_at":"2026-08-01T08:00:00",'
    '"updated_at":null,"archived":false,"visibility":"private","pinned":false}',
  ],
)
def test_canonical_v1_rejects_unknown_root_facts_and_naive_time(content):
  with pytest.raises(pydantic.ValidationError):
    CanonicalMemo.from_block_content(content)


def test_resolver_assembles_graph_owned_links_without_copying_them_into_content(
  monkeypatch,
):
  block = BlockModel(
    id=10,
    resolver=MemoResolver.__rsotype__,
    content=_canonical().to_block_content(),
  )
  relations = (
    RelationModel(id=1, from_=10, to_=21, content="attachment:1"),
    RelationModel(id=2, from_=10, to_=20, content="attachment:0"),
    RelationModel(id=3, from_=10, to_=5, content="parent"),
    RelationModel(id=4, from_=10, to_=30, content="reference"),
    RelationModel(id=5, from_=99, to_=10, content="reference"),
  )

  attachment_blocks = {
    attachment_id: BlockModel(
      id=attachment_id,
      resolver="extensions.memos.attachment.v2",
      content="{}",
    )
    for attachment_id in (20, 21)
  }

  class _SolvedAttachmentResolver:
    def __init__(self, attachment_id: int):
      self.attachment_id = attachment_id

    async def get_solved_content(
      self,
      *,
      refresh: bool = False,
      materialize_missing: bool = True,
    ):
      del refresh, materialize_missing
      return SolvedAttachment(
        block_id=self.attachment_id,
        content_block_id=self.attachment_id + 100,
        canonical=CanonicalAttachment(
          filename=f"{self.attachment_id}.png",
          media_type="image/png",
          size=1,
          created_at=datetime.datetime(2026, 8, 1, tzinfo=datetime.UTC),
        ),
        owner_memo_id=10,
      )

  monkeypatch.setattr(
    "app.business.info_base.block.BlockManager.get",
    classmethod(lambda _cls, attachment_id: attachment_blocks.get(attachment_id)),
  )
  monkeypatch.setattr(
    "app.business.info_base.resolver.ResolverManager.get",
    classmethod(lambda _cls, child: _SolvedAttachmentResolver(child.id)),
  )

  solved = asyncio.run(MemoResolver(block, relations).get_solved_content())

  assert solved.canonical == _canonical()
  assert solved.attachment_ids == (20, 21)
  assert solved.parent_id == 5
  assert solved.reference_ids == (30,)
  assert "attachment" not in block.content
  assert "parent" not in block.content
  assert "reference" not in block.content


@pytest.mark.parametrize(
  "relations",
  [
    (
      RelationModel(from_=10, to_=20, content="attachment:0"),
      RelationModel(from_=10, to_=21, content="attachment:0"),
    ),
    (RelationModel(from_=10, to_=20, content="attachment:1"),),
    (RelationModel(from_=10, to_=20, content="attachment:not-an-index"),),
  ],
)
def test_resolver_rejects_ambiguous_attachment_order(relations):
  block = BlockModel(
    id=10,
    resolver=MemoResolver.__rsotype__,
    content=_canonical().to_block_content(),
  )

  with pytest.raises(ValueError):
    asyncio.run(MemoResolver(block, relations).get_solved_content())


class _IdentitySession:
  def __init__(self):
    self.next_id = 1

  def add(self, block):
    if block.id is None:
      block.id = self.next_id
      self.next_id += 1

  def flush(self):
    return None

  def refresh(self, _block):
    return None


def test_equal_canonical_bodies_create_distinct_root_identities():
  session = _IdentitySession()

  first = MemoGraphRepository.create_root(_canonical(), session)  # type: ignore[arg-type]
  second = MemoGraphRepository.create_root(_canonical(), session)  # type: ignore[arg-type]

  assert first.content == second.content
  assert first.id == 1
  assert second.id == 2
