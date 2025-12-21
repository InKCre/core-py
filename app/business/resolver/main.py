import abc
import typing
from typing import Optional as Opt

import sqlmodel

from app.business.storage.main import StorageManager

from app.schemas.root import StarGraphForm
from app.schemas.block import ResolverType, BlockModel
from app.schemas.relation import RelationModel


class ResolverManager:
    RESOLVERS: dict[ResolverType, type["Resolver"]] = {}
    """Global resolver registry.

    Map ResolverType to Resolver class
    """

    @classmethod
    def register_resolver(cls, resolver_cls: type["Resolver"]):
        cls.RESOLVERS[resolver_cls.__rsotype__] = resolver_cls

    @classmethod
    def new_resolver(cls, block: BlockModel) -> "Resolver":
        """Create resolver instance from block."""
        try:
            resolver_cls = cls.RESOLVERS[block.resolver]
        except KeyError:
            raise NotImplementedError(f"Resolver {block.resolver} not implemented.")
        return resolver_cls(block)


class Resolver(abc.ABC):
    """Resolver resolves a block and its (direct) relations."""

    __rsotype__: ResolverType
    """Resolver type
    """

    BorRT: typing.TypeAlias = BlockModel | RelationModel
    """Union type of BlockModel and RelationModel
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
        self._relations = relations or tuple()
        self._solved_content: typing.Any
        self.__post_init__()

    def __post_init__(self): ...

    @classmethod
    # @abc.abstractmethod TODO
    def create_graph(cls, *args, **kwargs) -> StarGraphForm: ...

    # @abc.abstractmethod TODO
    async def breakdown(self) -> typing.AsyncGenerator[BorRT, BorRT]:
        """Break down the block into smaller blocks and relations.

        :param block_id: The block the content to resolve belongs to.
        :return:
        """
        ...

    async def get_text(self) -> str:
        """Get block content in text format."""
        storage = StorageManager.new_storage(self._block)
        return await storage.get_content(self._block)

    def get_str_for_embedding(self) -> str:
        """Get string representation for embedding generation."""
        return self._block.content

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
