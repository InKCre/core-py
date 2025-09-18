import abc
import typing
from typing import Optional as Opt

from app.business.storage.main import StorageManager

from ...schemas.root import StarGraphForm
from ...schemas.block import ResolverType, BlockModel
from ...schemas.relation import RelationModel


class ResolverManager:
    resolvers: dict[ResolverType, type["Resolver"]] = {}
    """Map ResolverType to Resolver class
    """

    @classmethod
    def register_resolver(cls, resolver_cls: type["Resolver"]):
        cls.resolvers[resolver_cls.__rsotype__] = resolver_cls

    @classmethod
    def new_resolver(cls, block: BlockModel) -> "Resolver":
        """Create resolver instance from block."""
        try:
            resolver_cls = cls.resolvers[block.resolver]
        except KeyError:
            raise NotImplementedError(f"Resolver {block.resolver} not implemented.")
        return resolver_cls(block)


class Resolver(abc.ABC):
    """Resolver is used to resolve a block and its relations."""

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
        """
        :param block: Block to resolve.
        :param relations: Relations of the block.
        """
        self._block = block
        self._relations = relations or tuple()
        self.__post_init__()

    def __post_init__(self):
        pass

    @classmethod
    # @abc.abstractmethod TODO
    def create_brs(cls, *args, **kwargs) -> StarGraphForm: ...

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
        return storage.get_content()

    def get_str_for_embedding(self) -> str:
        """Get string representation for embedding generation."""
        return self._block.content
