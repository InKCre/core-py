import abc
import datetime
import importlib
import logging
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel
import typing
from typing import Optional as Opt
from app.business.root import RootManager
from app.engine import SessionLocal
from app.schemas.root import StarGraphForm
from app.schemas.block import BlockID, BlockModel
from app.schemas.source import SourceModel, SourceID, SourceTypesModel
from app.schemas.source import SourceCollectJobModel, SourceCollectJobStatus
from app.scheduler import scheduler
from utils.datetime_ import get_datetime


LOGGER = logging.getLogger(__name__)

ConfigTV = typing.TypeVar("ConfigTV", bound=dict)


class SourceBase(abc.ABC, typing.Generic[ConfigTV]):
    """InkCre Source Base class."""

    def __init_subclass__(cls, **kwargs) -> None:
        SourceManager.add_source_type(cls)
        return super().__init_subclass__()

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
                    misfire_grace_time=None,
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
    _SOURCE_CLASSES: dict[str, type[SourceBase]] = {}

    @classmethod
    def add_source_type(cls, source_cls: type[SourceBase]) -> None:
        """Register a new source type."""
        source_type = source_cls.__module__ + "." + source_cls.__qualname__
        cls._SOURCE_CLASSES[source_type] = source_cls

        stmt = sqlalchemy.dialects.postgresql.insert(SourceTypesModel).values(
            id=source_type,
            description=source_cls.__doc__ or "No description.",
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[SourceTypesModel.id],
            set_=dict(description=stmt.excluded.description),
        )
        session = SessionLocal()
        session.exec(stmt)  # type: ignore
        session.commit()

    @classmethod
    def set_up_collect_jobs(cls):
        with SessionLocal() as db:
            sources = db.exec(
                sqlmodel.select(SourceModel).where(SourceModel.collect_at is not None)
            ).all()

        for source in sources:
            if source.collect_at is None:
                continue
            # TODO create a source collect job instead of directly scheduling the collect
            scheduler.add_job(
                func=cls._get_source_ins(
                    typing.cast(SourceID, source.id), source.type
                ).collect,
                trigger=source.collect_at.to_trigger(),
                id=f"source.{source.id}.collect",
                replace_existing=True,
                misfire_grace_time=None,
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
            source_class = cls._SOURCE_CLASSES.get(source_type, None)
            if source_class is None:
                raise ValueError(f"Source class {source_type} not registered.")
            ins = source_class(_id=typing.cast(SourceID, source_id))
            cls.SOURCES[source_id] = ins
        return ins

    @classmethod
    async def run_a_collect(cls, source_id: int, full: bool = False) -> list[BlockModel]:
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


class SourceCollectJobManager:
    """Manager for source collect jobs."""

    @classmethod
    async def handle_created(cls, job_id_str: str):
        """Handle a source collect job created."""

        try:
            job_id = int(job_id_str)
        except ValueError:
            LOGGER.error(f"Invalid source collect job_id: {job_id_str}")
            return

        with SessionLocal() as db:
            job = db.exec(
                sqlmodel.select(SourceCollectJobModel).where(
                    SourceCollectJobModel.id == job_id
                )
            ).one_or_none()
            if not job:
                LOGGER.error(f"Job {job_id} not found")
                return

            # Update status to RUNNING
            job.status = SourceCollectJobStatus.RUNNING
            job.started_at = datetime.datetime.now(datetime.timezone.utc)
            db.add(job)
            db.commit()

        # Schedule the collect
        scheduler.add_job(
            func=cls.run,
            args=[job_id],
            misfire_grace_time=None,
        )

    @classmethod
    async def run(cls, job_id: int):
        with SessionLocal() as db:
            job = db.exec(
                sqlmodel.select(SourceCollectJobModel).where(
                    SourceCollectJobModel.id == job_id
                )
            ).one()

            try:
                # Run the collect
                await SourceManager.run_a_collect(job.source)
                job.status = SourceCollectJobStatus.FINISHED
            except Exception as e:
                LOGGER.error(f"Error running job {job_id}: {e}")
                job.status = SourceCollectJobStatus.FAILED
                job.state = {"error": str(e)}
            finally:
                job.closed_at = datetime.datetime.now(datetime.timezone.utc)
                db.add(job)
                db.commit()
