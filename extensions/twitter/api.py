import abc
import asyncio
import datetime
from pathlib import Path
import re
import typing
from authlib.integrations.httpx_client import AsyncOAuth2Client  # pyrefly: ignore[untyped-import]
from authlib.integrations.base_client.errors import OAuthError  # pyrefly: ignore[untyped-import]
import httpx
import sqlmodel
import twikit
import twikit.media
from typing import Optional as Opt
from dd import dd
from utils.datetime_ import get_timestamp
from .schema import TweetPhoto, TweetVideo, VideoVariant
from . import Extension


class Tweet(sqlmodel.SQLModel):
  id: int
  user_id: str
  """推文用户ID"""
  conversation_id: Opt[int] = None
  text: str
  """推文文本内容
    
    - 移除回复提及
    - 移除媒体、网页链接（用 `[photo]`、`[video]`、`[link]` 占位）
    """
  quote: Opt[int] = None
  """引用推文ID"""
  photos: tuple[TweetPhoto, ...] = ()
  videos: tuple[TweetVideo, ...] = ()
  urls: tuple[str, ...] = ()


class TwitterAPIResult(sqlmodel.SQLModel):
  next_page: Opt[str] = None
  previous_page: Opt[str] = None
  tweets: tuple[Tweet, ...] = ()


class TwitterAPI(abc.ABC):
  """Twitter API client.

  Should be singleton.
  """

  SINGLETON: Opt["TwitterAPI"] = None

  @classmethod
  async def close_singleton(cls) -> None:
    """Close and forget the singleton so a later enable gets a fresh client."""
    singleton = cls.SINGLETON
    if singleton is None:
      return
    await singleton.close()
    cls.SINGLETON = None

  @classmethod
  def new(
    cls,
    *,
    expected_authorization_id: str | None = None,
  ) -> "TwitterAPI":
    """Create an instance of the Twitter API client.

    Use `config.backend` to determine which backend to use.
    """
    config = Extension.get_config()
    backend_type = config.backend
    if backend_type == "official":
      return OfficialAPI.from_extension(expected_authorization_id=expected_authorization_id)
    if cls.SINGLETON is not None:
      return cls.SINGLETON
    if backend_type == "twikit":
      cls.SINGLETON = TwikitAPI(
        email=config.email,
        username=config.username,
        password=config.password,
        totp_secret=config.totp_secret,
        language=config.api_language,
        proxy=config.proxy,
      )
      return cls.SINGLETON
    raise ValueError(f"Unknown backend type: {backend_type}")

  async def close(self): ...

  @property
  @abc.abstractmethod
  def user_handle(self) -> str: ...

  @property
  @abc.abstractmethod
  def user_id(self) -> str: ...

  @abc.abstractmethod
  async def get_bookmarks(
    self, max_results: int = 20, page: Opt[str] = None
  ) -> TwitterAPIResult: ...

  @abc.abstractmethod
  async def get_tweets(
    self, query: str, max_results: int = 20, page: Opt[str] = None
  ) -> TwitterAPIResult: ...

  @abc.abstractmethod
  async def get_replies(
    self, *conversation_ids: str, from_: Opt[str] = None, max_results: int = 20
  ) -> TwitterAPIResult: ...


class OfficialAPI(TwitterAPI):
  """Official Twitter API client."""

  request_records: dict[str, tuple[int, datetime.datetime]] = {}
  """How many requests made to each endpoint for last 15 mins.
    """
  rate_limit_reset: dict[str, int] = {}
  """When the rate limit for each endpoint will reset.
    """

  def __init__(  # noqa: PLR0913
    self,
    client_id: str,
    client_secret: str,
    *,
    token: dict[str, typing.Any],
    user_id: str,
    user_handle: str,
    authorization_id: str,
  ):
    self.__client_id = client_id
    self.__client_secret = client_secret
    self.__token = token
    self.__user_id = user_id
    self.__user_handle = user_handle
    self.__authorization_id = authorization_id

  @classmethod
  def from_extension(
    cls,
    *,
    expected_authorization_id: str | None = None,
  ) -> "OfficialAPI":
    from .setup_flow import TwitterExtensionState, TwitterSetupConflict, _fingerprint

    config = Extension.get_config()
    state = TwitterExtensionState.model_validate(Extension.get_state().model_dump())
    account = state.account
    if (
      account is None
      or account.reconnect_required
      or account.app_fingerprint != _fingerprint(config)
    ):
      raise TwitterSetupConflict("Twitter account is not connected")
    if (
      expected_authorization_id is not None
      and account.authorization_id != expected_authorization_id
    ):
      raise TwitterSetupConflict("Twitter authorization changed before collection")
    return cls(
      config.client_id,
      config.client_secret,
      token=dict(account.token),
      user_id=account.user_id,
      user_handle=account.handle,
      authorization_id=account.authorization_id,
    )

  @property
  def user_handle(self) -> str:
    if self.__user_handle is None:
      raise ValueError("User handle is not set. Please authorize first.")
    return self.__user_handle

  @property
  def user_id(self) -> str:
    if self.__user_id is None:
      raise ValueError("User ID is not set. Please authorize first.")
    return self.__user_id

  async def _request(  # noqa: PLR0913
    self,
    method: str,
    endpoint: str,
    path_params: Opt[dict] = None,
    query: Opt[dict] = None,
    body: Opt[dict] = None,
    retried: int = 0,
  ) -> dict:
    """Make a request to the Twitter API.

    :param method: HTTP method (GET, POST, etc.)
    :param endpoint: API endpoint (e.g., "/users/me")
        Must start with a slash ("/").
        Use "{variable}" to mark path parameters.
    :param path_params: List of path parameters to format into the endpoint
    :param query: Query parameters as a dictionary
    :param body: Request body as a dictionary (for POST/PUT requests)

    - Auto authorization header
    - Auto refresh access token
    - Rate limit
      - Failed requests also count
    - TODO Monthly limit
    - Error handling
    - Resopnse body parsing
    """
    from .setup_flow import TwitterExtensionState, TwitterSetupConflict, _fingerprint

    latest = TwitterExtensionState.model_validate(Extension.get_state().model_dump())
    latest_config = Extension.get_config()
    if (
      latest.account is None
      or latest.account.reconnect_required
      or latest.account.authorization_id != self.__authorization_id
      or latest.account.app_fingerprint != _fingerprint(latest_config)
    ):
      raise TwitterSetupConflict("Twitter authorization changed before provider access")
    self.__token = dict(latest.account.token)
    request_token = dict(self.__token)
    endpoint_with_params = endpoint.format(**path_params) if path_params else endpoint

    rate_limit_reset_at = self.rate_limit_reset.get(endpoint)
    if rate_limit_reset_at:
      await asyncio.sleep((rate_limit_reset_at - get_timestamp()) + 5)
      del self.request_records[endpoint]

    # request_record = cls.request_records.get(endpoint)
    # if request_record:
    #     last_request_count, last_15m_start_at = request_record
    #     if last_15m_start_at + datetime.timedelta(minutes=15) < datetime.datetime.now():
    #         del cls.request_records[endpoint]
    #     else:
    #         limit = Extension.config.api_rate_limit", {}).get(endpoint, 1)
    #         if last_request_count >= limit:
    #             # wait until the rate limit resets
    #             await asyncio.sleep((
    #                 last_15m_start_at + datetime.timedelta(minutes=15)
    #                 - datetime.datetime.now()
    #             ).total_seconds() + 5) # add a buffer of 5 seconds
    #             # reset
    #             cls.request_records[endpoint] = (0, datetime.datetime.now())
    # else:
    #     last_request_count, last_15m_start_at = 0, datetime.datetime.now()

    async def update_token(
      token: dict[str, typing.Any],
      **_: typing.Any,
    ) -> None:
      from .setup_flow import TwitterExtensionState, TwitterSetupConflict

      def update(model: sqlmodel.SQLModel) -> sqlmodel.SQLModel:
        state = TwitterExtensionState.model_validate(model.model_dump())
        if (
          state.account is None or state.account.authorization_id != self.__authorization_id
        ):
          raise TwitterSetupConflict("Twitter authorization changed during refresh")
        if dict(state.account.token) != request_token:
          raise TwitterSetupConflict("Twitter token changed during refresh")
        state.account.token = dict(token)
        return state

      Extension.mutate_state(update)
      self.__token = dict(token)

    def require_reconnect() -> None:
      from .setup_flow import TwitterExtensionState

      def update(model: sqlmodel.SQLModel) -> sqlmodel.SQLModel:
        state = TwitterExtensionState.model_validate(model.model_dump())
        if (
          state.account is not None
          and state.account.authorization_id == self.__authorization_id
        ):
          state.account.reconnect_required = True
        return state

      Extension.mutate_state(update)

    client = AsyncOAuth2Client(
      client_id=self.__client_id,
      client_secret=self.__client_secret,
      token=self.__token,
      token_endpoint="https://api.x.com/2/oauth2/token",
      token_endpoint_auth_method="client_secret_basic",
      update_token=update_token,
      timeout=10,
    )
    try:
      response = await client.request(
        method,
        f"https://api.x.com/2{endpoint_with_params}",
        params=query,
        json=body,
      )
      if response.status_code == 429:
        x_rate_limit_reset = response.headers.get("x-rate-limit-reset")
        if x_rate_limit_reset:
          self.rate_limit_reset[endpoint] = int(x_rate_limit_reset)

          # # Rate limit exceeded but not expected, set request count to max
          # # and request again when rate limit reset
          # cls.request_records[endpoint] = (
          #     Extension.config.api_rate_limit", {}).get(endpoint, 1),
          #     datetime.datetime.now()
          # )

        if retried < 3:
          return await self._request(
            method, endpoint, path_params, query, body, retried + 1
          )
        raise RuntimeError("Twitter API rate limit exceeded after retries")

      response.raise_for_status()
      payload = response.json()
      if not isinstance(payload, dict):
        raise RuntimeError("Twitter API returned an invalid response")
      return payload
    except OAuthError:
      require_reconnect()
      raise RuntimeError("Twitter authorization requires reconnection") from None
    except httpx.HTTPStatusError as error:
      if error.response.status_code == 401:
        require_reconnect()
        raise RuntimeError("Twitter authorization requires reconnection") from None
      raise RuntimeError("Twitter API request failed") from error
    except httpx.HTTPError as error:
      raise RuntimeError("Twitter API request failed") from error
    finally:
      await typing.cast(httpx.AsyncClient, client).aclose()

  async def close(self) -> None:
    """Official clients are operation-scoped and hold no open transport."""

  async def get_user(self) -> tuple[str, str]:
    """Get the user info the token represents and store to state.

    :returns: (user ID, user handle)
    """
    user_info = await self._request("GET", "/users/me")
    user_id = user_info.get("data", {}).get("id")
    if not user_id:
      raise ValueError("Failed to get user ID from Twitter API.")
    user_handle = user_info.get("data", {}).get("username")
    if not user_handle:
      raise ValueError("Failed to get user handle from Twitter API.")

    # Extension.state["user_id"] = user_id
    # Extension.state["user_handle"] = user_handle
    self.__user_id = user_id
    self.__user_handle = user_handle
    return user_id, user_handle

  def _resolve_tweets(
    self, raw_tweets: list[dict], includes: dict[str, list[dict]]
  ) -> list[Tweet]:
    include_medias = includes.get("media", ())

    tweets: list[Tweet] = []
    for tweet in raw_tweets:
      tweet = dd(tweet)
      tweet_id = tweet.id()

      # resolve medias
      media_keys = tweet._.attachments.media_keys() or ()
      photos: list[TweetPhoto] = []
      videos: list[TweetVideo] = []
      for media_key in media_keys:
        for include_media in include_medias:
          include_media = dd(include_media)
          if include_media._.media_key() == media_key:
            media_type = include_media._.type()
            if media_type == "video":
              videos.append(
                TweetVideo(
                  id=media_key,
                  variants=tuple(
                    VideoVariant(**variant)
                    for variant in (include_media._.variants() or ())
                  ),
                )
              )
            elif media_type == "photo":
              photos.append(
                TweetPhoto(
                  id=media_key,
                  url=include_media.url(lambda x: x or ""),
                )
              )
            else:
              # TODO log warning for unsupported media type
              pass
            break

      # resolve conversation ID
      conversation_id = tweet._.conversation_id()
      if conversation_id == tweet_id:
        conversation_id = None

      # resolve url entities
      urls: list[str] = []
      for entity in tweet._.entities.urls() or []:
        url = entity.get("expanded_url")
        if url:
          urls.append(url)

      # resolve text
      tweet_text = tweet.text()
      tweet_text = re.sub(r"^(?:@\w+\s*)+", "", tweet_text)

      tweets.append(
        Tweet(
          id=tweet_id,
          # user_id=tweet._.user  # TODO
          text=tweet_text,
          conversation_id=conversation_id,
          photos=tuple(photos),
          videos=tuple(videos),
          urls=tuple(urls),
        )
      )

    return tweets

  async def get_bookmarks(
    self, max_results: int = 20, page: str | None = None
  ) -> TwitterAPIResult:
    """Get user bookmarks.

    Rate limit:
    - Free: 1 req per 15 minutes
    - Basic: 5 req per 15 minutes
    - Pro: 50 req per 15 minutes
    """
    bookmarks_query = {
      "max_results": max_results,
      "tweet.fields": "attachments,entities,lang,conversation_id",
      "media.fields": "alt_text,media_key,url,type",
      "expansions": "attachments.media_keys,attachments.media_source_tweet",
    }
    if page:
      bookmarks_query["pagination_token"] = page
    res = await self._request(
      "GET",
      "/users/{id}/bookmarks",
      path_params={"id": self.__user_id},
      query=bookmarks_query,
    )
    tweets = self._resolve_tweets(res.get("data", []), res.get("includes", {}))
    return TwitterAPIResult(
      next_page=res.get("meta", {}).get("next_token"),
      previous_page=res.get("meta", {}).get("previous_token"),
      tweets=tuple(tweets),
    )

  async def get_tweets(
    self, query: str, max_results: int = 20, page: str | None = None
  ) -> TwitterAPIResult:
    res = await self._request(
      "GET",
      "/tweets/search/recent",
      query={
        "query": query,
        "max_results": max_results,
        "tweet.fields": "attachments,entities,lang,conversation_id",
        "media.fields": "alt_text,media_key,url,type",
        "expansions": "attachments.media_keys,attachments.media_source_tweet",
      },
    )
    tweets = self._resolve_tweets(res.get("data", []), res.get("includes", {}))
    return TwitterAPIResult(
      next_page=res.get("meta", {}).get("next_token"),
      previous_page=res.get("meta", {}).get("previous_token"),
      tweets=tuple(tweets),
    )

  async def get_replies(
    self, *conversation_ids: str, from_: str | None = None, max_results: int = 20
  ) -> TwitterAPIResult:
    # TODO add query lenth limit auto adapt
    conversations = " OR ".join(
      f"conversation_id:{conversation_id}" for conversation_id in conversation_ids
    )
    res = await self.get_tweets(
      query=f"from:{from_} ({conversations})",
      max_results=max_results,
    )
    return res


class TwikitAPI(TwitterAPI):
  """Twikit API client."""

  DATA_DIRECTORY = Path("data/extensions/twitter")
  COOKIES_FILE = DATA_DIRECTORY / "twikit_cookies.json"

  @classmethod
  def _prepare_data_directory(cls) -> None:
    cls.DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)

  def __init__(  # noqa: PLR0913
    self,
    email: str,
    username: str,
    password: str,
    totp_secret: Opt[str] = None,
    language: Opt[str] = None,
    proxy: Opt[str] = None,
  ):
    """
    :param language: The language code to use in API requests.
        Keep the same with your daily use of Twitter.
    """
    if not language:
      language = "en-US"
    self._client = twikit.Client(language=language, proxy=proxy)
    self._email = email
    self._username = username
    self._password = password
    self._totp_secret = totp_secret

  async def close(self):
    self._prepare_data_directory()
    self._client.save_cookies(str(self.COOKIES_FILE))

  @property
  def user_handle(self) -> str:
    return self._username

  @property
  def user_id(self) -> str:
    if not self._client._user_id:
      raise ValueError("User ID is not set. Please login first.")
    return self._client._user_id

  async def _login(self):
    self._prepare_data_directory()
    await self._client.login(
      auth_info_1=self._email,
      auth_info_2=self._username,
      password=self._password,
      totp_secret=self._totp_secret,
      cookies_file=str(self.COOKIES_FILE),
    )

  @staticmethod
  def _resolve_tweet(tweet: twikit.Tweet) -> Tweet:
    # resolve text
    # remove reply mentions
    tweet_text = re.sub(r"^(?:@\w+\s*)+", "", tweet.text)

    # resolve medias
    photos: list[TweetPhoto] = []
    videos: list[TweetVideo] = []
    for media in tweet.media:
      media_url = media.url
      if isinstance(media, twikit.media.Photo):
        photos.append(TweetPhoto(id=media.id, url=media.media_url))
        tweet_text = tweet_text.replace(media_url, "[photo]")
      elif isinstance(media, twikit.media.Video):
        videos.append(
          TweetVideo(
            id=media.id,
            variants=tuple(
              VideoVariant(
                bitrate=variant.bitrate,
                content_type=variant.content_type,
                url=variant.url or "",
              )
              for variant in media.streams
            ),
          )
        )
        tweet_text = tweet_text.replace(media_url, "[video]")

    # resolve urls
    urls: list[str] = []
    for i in typing.cast(dict, tweet.urls):
      i = dd(i)
      ex_url = i._.expanded_url()
      url = i._.url()
      if ex_url:
        urls.append(ex_url)
        if url:
          tweet_text = tweet_text.replace(url, "[link]")

    return Tweet(
      id=int(tweet.id),
      conversation_id=int(tweet.in_reply_to) if tweet.in_reply_to else None,
      user_id=tweet.user.screen_name,
      text=tweet_text,
      photos=tuple(photos),
      videos=tuple(videos),
      urls=tuple(),
    )

  @classmethod
  def _resolve_tweets(cls, result: twikit.utils.Result[twikit.Tweet]) -> tuple[Tweet, ...]:
    return tuple(cls._resolve_tweet(tweet) for tweet in result)

  async def get_bookmarks(
    self, max_results: int = 20, page: str | None = None
  ) -> TwitterAPIResult:
    if not self._client._user_id:
      await self._login()
    res = await self._client.get_bookmarks(count=max_results, cursor=page)
    return TwitterAPIResult(
      next_page=res.next_cursor,
      previous_page=res.previous_cursor,
      tweets=tuple(self._resolve_tweets(res)),
    )

  async def get_tweets(
    self, query: str, max_results: int = 20, page: str | None = None, tried: int = 0
  ) -> TwitterAPIResult:
    if not self._client._user_id:
      await self._login()
    try:
      res = await self._client.search_tweet(
        query=query, product="Latest", count=max_results, cursor=page
      )
    except twikit.errors.NotFound:
      if tried < 3:
        await asyncio.sleep(3)
        return await self.get_tweets(query, max_results, page, tried + 1)
      else:
        return TwitterAPIResult()
    else:
      return TwitterAPIResult(
        next_page=res.next_cursor,
        previous_page=res.previous_cursor,
        tweets=tuple(self._resolve_tweets(res)),
      )

  async def _get_a_reply_of(
    self, from_: str, replies: twikit.utils.Result[twikit.Tweet]
  ) -> Tweet | None:
    if len(replies) == 0:
      return None
    for reply in replies:
      if reply.user.screen_name == from_:
        return self._resolve_tweet(reply)
    else:
      await asyncio.sleep(5)  # avoid rate limit
      replies = await replies.next()
      return await self._get_a_reply_of(from_, replies)

  async def get_replies(
    self, *conversation_ids: str, from_: str | None = None, max_results: int = 20
  ) -> TwitterAPIResult:
    res_tweets: list[Tweet] = []
    for cid in conversation_ids:
      await asyncio.sleep(3)  # avoid rate limit
      try:
        tweet = await self._client.get_tweet_by_id(cid)
      except twikit.errors.TweetNotAvailable:
        # TODO log warning
        continue
      else:
        replies = tweet.replies
        if not replies:
          continue
        else:
          if from_:
            the_reply = await self._get_a_reply_of(from_, replies)
            if the_reply:
              res_tweets.append(the_reply)
          else:
            res_tweets.extend(self._resolve_tweets(replies))

    return TwitterAPIResult(tweets=tuple(res_tweets))
