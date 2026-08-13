"""Exact JSON wire models for the supported Memos 0.29.1 subset."""

import datetime
import typing

import pydantic


def _to_camel(name: str) -> str:
  head, *tail = name.split("_")
  return head + "".join(part.capitalize() for part in tail)


class WireModel(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(
    alias_generator=_to_camel,
    populate_by_name=True,
    extra="forbid",
  )


class InstanceProfile(WireModel):
  version: typing.Literal["0.29.1"] = "0.29.1"


class User(WireModel):
  name: typing.Literal["users/inkcre"] = "users/inkcre"
  role: typing.Literal["ADMIN"] = "ADMIN"
  username: typing.Literal["inkcre"] = "inkcre"
  display_name: typing.Literal["InKCre"] = "InKCre"
  state: typing.Literal["NORMAL"] = "NORMAL"


class GetCurrentUserResponse(WireModel):
  user: User = pydantic.Field(default_factory=User)


class GeneralSetting(WireModel):
  memo_visibility: typing.Literal["PRIVATE"] = "PRIVATE"


class UserSetting(WireModel):
  general_setting: GeneralSetting = pydantic.Field(default_factory=GeneralSetting)


MemosVisibility = typing.Literal["PRIVATE", "PROTECTED", "PUBLIC"]
MemosState = typing.Literal["NORMAL", "ARCHIVED"]


class Attachment(WireModel):
  name: str | None = None
  create_time: datetime.datetime | None = None
  filename: str | None = None
  external_link: str | None = None
  type: str | None = None
  size: str | None = None
  memo: str | None = None


class CreateMemoRequest(WireModel):
  content: str
  visibility: MemosVisibility | None = None
  attachments: list[Attachment] | None = None
  create_time: datetime.datetime | None = None


class Memo(WireModel):
  name: str
  state: MemosState
  creator: typing.Literal["users/inkcre"] = "users/inkcre"
  create_time: datetime.datetime | None
  update_time: datetime.datetime | None
  content: str
  visibility: MemosVisibility
  pinned: bool
  attachments: list[Attachment] = pydantic.Field(default_factory=list)
  parent: str | None = None


class ListMemosResponse(WireModel):
  memos: list[Memo]
  next_page_token: str


class ListMemoCommentsResponse(WireModel):
  memos: list[Memo]
  next_page_token: str
  total_size: int


class UpdateMemoRequest(WireModel):
  content: str | None = None
  visibility: MemosVisibility | None = None
  state: MemosState | None = None
  pinned: bool | None = None
  update_time: datetime.datetime | None = None
  attachments: list[Attachment] | None = None


class CreateAttachmentRequest(WireModel):
  filename: str
  type: str
  content: str
  memo: str | None = None


class ListAttachmentsResponse(WireModel):
  attachments: list[Attachment]
