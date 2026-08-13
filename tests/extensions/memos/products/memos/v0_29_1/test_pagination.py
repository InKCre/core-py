"""Memos 0.29.1 list query and opaque cursor contract."""

import datetime

import pytest

from extensions.memos.family import MemoCursor
from extensions.memos.products.memos.v0_29_1.pagination import (
  CREATOR_FILTER,
  decode_comment_page_token,
  decode_page_token,
  encode_comment_page_token,
  encode_page_token,
  parse_list_query,
  parse_comment_list_query,
)


def test_page_token_round_trip_is_bound_to_state_and_filter():
  cursor = MemoCursor(
    created_at=datetime.datetime(2026, 8, 1, 8, tzinfo=datetime.UTC),
    block_id=17,
  )
  token = encode_page_token(cursor, state="NORMAL", filter_=CREATOR_FILTER)

  assert (
    decode_page_token(
      token,
      state="NORMAL",
      filter_=CREATOR_FILTER,
    )
    == cursor
  )
  with pytest.raises(ValueError, match="does not belong"):
    decode_page_token(token, state="ARCHIVED", filter_=CREATOR_FILTER)


@pytest.mark.parametrize(
  "token",
  ["not-base64!", "", "e30"],
)
def test_invalid_or_foreign_page_token_is_rejected(token):
  with pytest.raises(ValueError):
    decode_page_token(token, state="NORMAL", filter_=CREATOR_FILTER)


def test_moememos_list_query_accepts_page_size_200():
  page_size, state, filter_, cursor = parse_list_query(
    {
      "pageSize": "200",
      "pageToken": "",
      "state": "ARCHIVED",
      "filter": CREATOR_FILTER,
    }
  )

  assert (page_size, state, filter_, cursor) == (
    200,
    "ARCHIVED",
    CREATOR_FILTER,
    None,
  )


def test_comment_page_token_is_bound_to_parent_and_uses_upstream_default_size():
  token = encode_comment_page_token(18, parent_id=17)

  assert decode_comment_page_token(token, parent_id=17) == 18
  assert parse_comment_list_query({}, parent_id=17) == (10, None)
  assert parse_comment_list_query({"pageToken": ""}, parent_id=17) == (10, None)
  with pytest.raises(ValueError, match="parent memo"):
    decode_comment_page_token(token, parent_id=19)


@pytest.mark.parametrize(
  "query",
  [
    {},
    {"filter": 'creator == "users/other"'},
    {"filter": CREATOR_FILTER, "state": "DELETED"},
    {"filter": CREATOR_FILTER, "pageSize": "many"},
    {"filter": CREATOR_FILTER, "orderBy": "update_time desc"},
  ],
)
def test_list_query_rejects_outside_the_bounded_contract(query):
  with pytest.raises(ValueError):
    parse_list_query(query)
