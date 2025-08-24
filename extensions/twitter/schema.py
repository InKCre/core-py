import sqlmodel
import typing
from typing import Optional as Opt
from .resolver import TweetResolver


TweetID: typing.TypeAlias = int
TweetMediaKey: typing.TypeAlias = str


class VideoVariant(sqlmodel.SQLModel):
    bitrate: Opt[int] = None
    content_type: Opt[str] = None
    """Content type of this video variant.
    
    None is video/mp4
    """
    url: str


class TweetVideo(sqlmodel.SQLModel):
    id: TweetMediaKey
    variants: tuple[VideoVariant, ...]


class TweetPhoto(sqlmodel.SQLModel):
    id: TweetMediaKey
    url: str
    alt_text: Opt[str] = None


class Tweet(sqlmodel.SQLModel):
    __resolver__ = TweetResolver

    id: TweetID
    user_id: str
    text: str
    """推文文本
    
    - 移除回复提及
    - 用 `[photo]`、`[video]`、`[link]` 占位媒体、网页链接
    """
