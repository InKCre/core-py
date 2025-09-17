import abc
import datetime
import importlib
import sqlmodel
import typing
from typing import Optional as Opt
from app.business.root import RootManager
from app.engine import SessionLocal
from app.schemas.root import StarGraphForm
from app.schemas.block import BlockID, BlockModel
from app.schemas.source import SourceModel, SourceID
from app.task import scheduler
from utils.datetime_ import get_datetime


ConfigTV = typing.TypeVar("ConfigTV", bound=dict)


class SourceBase(abc.ABC, typing.Generic[ConfigTV]):
    def __init__(self, _id: SourceID) -> None:
        self._id = _id

    async def collect(self, full: bool = False) -> list[BlockModel]:
        """Collect new data from the source.

        :param full:
            If True, collect all data, otherwise only new data.
            If True, collected data blocks will be inserted in reverse order.

        The order of collected blocks inserted into the database is the same
        as the order of blocks yielded by the generator.
        """
        collected: list[StarGraphForm] = []
        collected_blocks: list[BlockModel] = []
        generator = self._collect(full=full)
        async for item in generator:  # type: ignore[assignment] pyright bug
            collected.append(item)

        with SessionLocal() as db:
            for i, graph in enumerate((reversed(collected) if full else collected)):
                RootManager.add_star_graph_to_session(graph, db)
                # therotically, self._organize will be run after all committed
                scheduler.add_job(
                    func=self._organize,
                    kwargs={"block_id": graph.block.id},
                    trigger="date",
                    run_date=get_datetime()
                    + datetime.timedelta(seconds=(i * 1.5) + 30),
                )
                collected_blocks.append(graph.block)
            db.commit()

        return collected_blocks

    @abc.abstractmethod
    async def _collect(
        self, full: bool = False
    ) -> typing.AsyncGenerator[StarGraphForm, None]:
        """The real collect implementation."""

    @abc.abstractmethod
    async def _organize(self, block_id: BlockID) -> None:
        """Organize the collected block.

        Organization to collected blocks are concurrently.
        """

    def get_config(self) -> ConfigTV:
        """Get the configuration of the source."""
        raise NotImplementedError


class SourceManager:
    """

    - Run collect method of all configured sources
    - Add, remove and configure source instances
    - Add, remove sources
    """

    SOURCES: dict[SourceID, SourceBase] = {}

    @classmethod
    def set_up_collect_jobs(cls):
        with SessionLocal() as db:
            sources = db.exec(
                sqlmodel.select(SourceModel).where(SourceModel.collect_at is not None)
            ).all()

        for source in sources:
            if source.collect_at is None:
                continue
            scheduler.add_job(
                func=cls._get_source_ins(
                    typing.cast(SourceID, source.id), source.type
                ).collect,
                trigger=source.collect_at.to_trigger(),
                id=f"source.{source.id}.collect",
                replace_existing=True,
            )

    @classmethod
    def _get_source_ins(
        cls, source_id: SourceID, source_type: Opt[str] = None
    ) -> SourceBase:
        ins = cls.SOURCES.get(source_id, None)
        if ins is None:
            if source_type is None:
                raise ValueError(
                    f"Source {source_id} not instantiated and path to the class not defined."
                )
            source_module = importlib.import_module(source_type)
            source_class = typing.cast(
                type[SourceBase], getattr(source_module, "Source")
            )
            ins = source_class(_id=typing.cast(SourceID, source_id))
            cls.SOURCES[source_id] = ins
        return ins

    @classmethod
    async def run_a_collect(
        cls, source_id: int, full: bool = False
    ) -> list[BlockModel]:
        with SessionLocal() as db:
            source_model = db.exec(
                sqlmodel.select(SourceModel).where(SourceModel.id == source_id)
            ).one()

        return await cls._get_source_ins(
            typing.cast(SourceID, source_model.id), source_model.type
        ).collect(full=full)

    @classmethod
    def create(cls, type_: str, nickname: Opt[str] = None) -> SourceModel:
        """Add a new source."""
        with SessionLocal() as db:
            source = SourceModel(type=type_, nickname=nickname)
            db.add(source)
            db.commit()
            db.refresh(source)

        return source
