import abc
from app.business.block import BlockManager
from app.business.relation import RelationManager
from app.schemas.block import BlockModel
from app.schemas.storage import StorageType


class StorageManager:
    storages: dict[StorageType, type["Storage"]] = {}
    """Map StorageType to Storage class
    """

    @classmethod
    def register_storage(cls, resolver_cls: type["Storage"]):
        cls.storages[resolver_cls.__stgtype__] = resolver_cls

    @classmethod
    def new_storage(cls, block: BlockModel) -> "Storage":
        """Create storage instance from block."""
        if not block.storage:
            return Storage(block)
        try:
            resolver_cls = cls.storages[block.storage]
        except KeyError:
            raise NotImplementedError(f"Storage {block.storage} not implemented.")
        return resolver_cls(block)


class Storage(abc.ABC):
    """

    Responsible for `actual content` relation.

    Initialize this class for storage:None block.
    """

    __stgtype__: StorageType
    """Storage type"""

    def __init_subclass__(cls, rso_type: str, **kwargs) -> None:
        cls.__rsotype__ = rso_type
        StorageManager.register_storage(cls)
        return super().__init_subclass__(**kwargs)

    def __init__(self, block: BlockModel):
        self._block = block

    def get_content(self) -> str:
        """Get the actual content of the block."""
        if self._block.storage is None:
            return self._block.content
        else:
            # by out relation `content`
            out_relations = RelationManager.get(
                self._block.id, include_in=False, content="actual content"
            )
            if out_relations:
                # TODO what if multiple actual content relations?
                block = BlockManager.get(out_relations[0].to_)
                if block:
                    storage = StorageManager.new_storage(block)
                    return storage.get_content()
            return self.get_actual_content()

    def get_actual_content(self) -> str:
        """

        Conrete storage should implement this method.
        """
        return self._block.content
