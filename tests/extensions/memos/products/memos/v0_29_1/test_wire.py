"""Pinned Memos 0.29.1 startup wire fixtures."""

import json
from pathlib import Path

import pytest

from extensions.memos.products.memos.v0_29_1.wire import (
  GetCurrentUserResponse,
  InstanceProfile,
  UserSetting,
)


FIXTURES = Path(__file__).with_name("fixtures")


@pytest.mark.parametrize(
  ("model", "fixture_name"),
  [
    (InstanceProfile(), "instance_profile.json"),
    (GetCurrentUserResponse(), "current_user.json"),
    (UserSetting(), "general_setting.json"),
  ],
)
def test_startup_wire_model_matches_pinned_fixture(model, fixture_name):
  expected = json.loads((FIXTURES / fixture_name).read_text(encoding="utf-8"))

  assert model.model_dump(mode="json", by_alias=True) == expected
