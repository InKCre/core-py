"""Memos 0.29.1 create mapping fixtures."""

import datetime
import json
from pathlib import Path
import uuid

from extensions.memos.family import CanonicalAttachment, SolvedAttachment, SolvedMemo
from extensions.memos.products.memos.v0_29_1.adapter import (
  attachment_from_solved,
  canonical_from_create,
  memo_from_solved,
  update_plan,
)
from extensions.memos.products.memos.v0_29_1.wire import (
  CreateMemoRequest,
  UpdateMemoRequest,
)
import pytest


FIXTURES = Path(__file__).with_name("fixtures")


def _fixture(name: str):
  return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_create_request_round_trips_through_family_without_product_leakage():
  request = CreateMemoRequest.model_validate(_fixture("create_memo.json"))

  canonical = canonical_from_create(request)
  response = memo_from_solved(SolvedMemo(block_id=17, canonical=canonical))

  assert response.model_dump(mode="json", by_alias=True, exclude_none=True) == _fixture(
    "create_memo_response.json"
  )


def test_attachment_response_matches_pinned_memos_fixture():
  solved = SolvedAttachment(
    block_id=23,
    canonical=CanonicalAttachment(
      filename="photo.png",
      media_type="image/png",
      size=3,
      created_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
      blob_id=uuid.UUID("00000000-0000-0000-0000-000000000017"),
    ),
  )

  assert attachment_from_solved(solved).model_dump(
    mode="json",
    by_alias=True,
    exclude_none=True,
  ) == _fixture("create_attachment_response.json")


def test_missing_mask_infers_false_and_empty_string_from_raw_key_presence():
  request = UpdateMemoRequest.model_validate({"content": "", "pinned": False})

  plan = update_plan(
    request,
    raw_keys={"content", "pinned"},
    update_mask=None,
  )

  assert plan.root_patch is not None
  assert plan.root_patch.model_fields_set == {"body", "pinned"}
  assert plan.root_patch.body == ""
  assert plan.root_patch.pinned is False


def test_explicit_mask_updates_only_selected_fields_and_uses_proto_defaults():
  request = UpdateMemoRequest.model_validate({"content": "ignored", "visibility": "PUBLIC"})

  plan = update_plan(
    request,
    raw_keys={"content", "visibility"},
    update_mask="content,pinned",
  )

  assert plan.root_patch is not None
  assert plan.root_patch.model_fields_set == {"body", "pinned"}
  assert plan.root_patch.body == "ignored"
  assert plan.root_patch.pinned is False


def test_attachment_omission_and_present_empty_are_distinct_update_plans():
  omitted = update_plan(
    UpdateMemoRequest.model_validate({"content": "x"}),
    raw_keys={"content"},
    update_mask=None,
  )
  present_empty = update_plan(
    UpdateMemoRequest.model_validate({"attachments": []}),
    raw_keys={"attachments"},
    update_mask=None,
  )

  assert omitted.replace_attachments is False
  assert present_empty.replace_attachments is True
  assert present_empty.attachments == ()


@pytest.mark.parametrize(
  ("payload", "mask"),
  [
    ({}, None),
    ({"content": None}, None),
    ({"content": "x"}, ""),
    ({"content": "x"}, "unknown"),
    ({"content": "x"}, "content,"),
  ],
)
def test_invalid_mask_or_selected_null_is_rejected(payload, mask):
  request = UpdateMemoRequest.model_validate(payload)

  with pytest.raises(ValueError):
    update_plan(request, raw_keys=set(payload), update_mask=mask)
