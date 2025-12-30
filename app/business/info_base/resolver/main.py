import abc
import typing
from typing import Optional as Opt

import sqlmodel

from app.business.info_base.relation import RelationManager
from app.business.info_base.storage.main import StorageManager

from app.schemas.info_base.main import SubGraphForm
from app.schemas.info_base.block import BlockID, ResolverType, BlockModel
from app.schemas.info_base.relation import RelationModel
from app.schemas.info_base.storage import StorageID


class ResolverManager:
  RESOLVER_CLS: dict[ResolverType, type["Resolver"]] = {}
  """Global resolver registry.

  Map ResolverType to Resolver class
  """

  @classmethod
  def register_resolver(cls, resolver_cls: type["Resolver"]):
    cls.RESOLVER_CLS[resolver_cls.__rsotype__] = resolver_cls

  @classmethod
  def get(cls, block: BlockModel) -> "Resolver":
    """Create resolver instance from block."""
    try:
      resolver_cls = cls.RESOLVER_CLS[block.resolver]
    except KeyError:
      raise NotImplementedError(f"Resolver {block.resolver} not implemented/registered.")
    return resolver_cls(block)


SolvedContentTV = typing.TypeVar("SolvedContentTV")
RawContentTV = typing.TypeVar("RawContentTV")


class Resolver(abc.ABC, typing.Generic[SolvedContentTV, RawContentTV]):
  """Resolver resolves a star graph (a block and its direct relations)

  Generic parameters:
  - SolvedContentTV: The type of the solved content
  - RawContentTV: The type of the raw content
  """

  __rsotype__: ResolverType
  """Resolver type
  
  Extension resolver should follows `extensions.{extension_id}.{resolver_name}` pattern.
  """

  def __init_subclass__(cls, rso_type: str, **kwargs) -> None:
    cls.__rsotype__ = rso_type
    ResolverManager.register_resolver(cls)
    return super().__init_subclass__(**kwargs)

  def __init__(self, block: BlockModel, relations: Opt[tuple[RelationModel, ...]] = None):
    """Should never override __init__ in subclasses, use __post_init__ instead.

    :param block: Block to resolve.
    :param relations: Relations of the block.
    """
    self._block = block
    self.__relations = relations or None
    self.__raw_content: RawContentTV | None = None
    """The (real) content of the block, commonly fetched from storage. 
    If storage is None, uses block.content
    """
    if self._block.storage is None:
      self.__raw_content = typing.cast(RawContentTV, self._block.content)
    self.__solved_content: SolvedContentTV | None = None
    """Solved content is the content the resolver really works with,
    commonly from raw content.
    """
    self.__post_init__(self.__raw_content)

  def __post_init__(self, raw_content: Opt[RawContentTV] = None) -> None:
    """Subclass post-initialization hook.

    It's suggest to set __solved_content here if possible:
    ```python
    async def __post_init__(self, raw_content):
      if raw_content is not None:
        ... # anyhow from raw_content
        self.set_solved_content(solved_content)
    ```
    """
    ...

  @property
  def block_id(self) -> BlockID:
    """Get the block ID."""
    return typing.cast(BlockID, self._block.id)

  async def get_raw_content(self) -> RawContentTV:
    """Get the raw content of the block."""
    if self.__raw_content is None:
      if self._block.storage is None:
        self.__raw_content = typing.cast(RawContentTV, self._block.content)
      else:
        storage = StorageManager.get_storage(self._block.storage)
        self.__raw_content = typing.cast(
          RawContentTV, await storage.get_raw_content(self._block.content)
        )

    return self.__raw_content

  async def get_solved_content(self) -> SolvedContentTV:
    """Get the solved content of the block."""
    if self.__solved_content is None:
      raise NotImplementedError(
        f"{self.__class__.__name__}.get_solved_content() must be implemented by subclasses."
      )
    return self.__solved_content

  def set_solved_content(self, content: SolvedContentTV) -> None:
    self.__solved_content = content

  async def get_relations(self) -> tuple[RelationModel, ...]:
    """Get relations of the block."""
    if self.__relations is None:
      self.__relations = RelationManager.get(block_id=self.block_id)
    return self.__relations

  @classmethod
  # @abc.abstractmethod TODO
  def create_block(cls, content, storage: Opt[StorageID] = None) -> BlockModel: ...

  @classmethod
  # @abc.abstractmethod TODO
  def create_graph(cls, *args, **kwargs) -> SubGraphForm: ...

  @abc.abstractmethod
  async def get_text(self) -> str:
    """Get block content in text format."""
    ...

  @abc.abstractmethod
  async def get_str_for_embedding(self) -> str:
    """Get string representation for embedding generation."""
    ...

  def get_existing(self, db_session: sqlmodel.Session) -> Opt[BlockModel]:
    """Check if a block with the same content already exists in the database.

    :param db_session: Database session to use.
    :return: Existing BlockModel if found, else None.
    """
    existing_block = db_session.exec(
      sqlmodel.select(BlockModel).where(
        BlockModel.resolver == self._block.resolver,
        BlockModel.content == self._block.content,
      )
    ).one_or_none()
    return existing_block
