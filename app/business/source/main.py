import abc
import datetime
import logging
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlmodel
import typing
from typing import Optional as Opt
from app.engine import SessionLocal
from libs.obsrv.main import get_logger
from app.schemas.block import BlockID
from app.schemas.source import SourceCollectJobID, SourceModel, SourceID, SourceTypesModel
from app.schemas.source import SourceCollectJobModel, SourceCollectJobStatus
from app.scheduler import scheduler, with_trace_id


LOGGER = get_logger().getChild(__name__)

ConfigTV = typing.TypeVar("ConfigTV", bound=sqlmodel.SQLModel)


class SourceBase(abc.ABC, typing.Generic[ConfigTV]):
    """InkCre Source Base class."""

    __configschema__: dict
    """Source configuration JSON schema"""
    __configcls__: type[ConfigTV]

    def __init_subclass__(cls, config_cls: type[ConfigTV], **kwargs) -> None:
        cls.__configcls__ = config_cls
        cls.__configschema__ = config_cls.model_json_schema()
        SourceManager.add_source_type(cls)
        return super().__init_subclass__(**kwargs)

    def __init__(self, _id: SourceID) -> None:
        self._id = _id

    @abc.abstractmethod
    async def collect(self, job: "SourceCollectJobModel") -> None:
        """Collect new data from the source.

        :param job: The collect job containing config and state.
        """

    @abc.abstractmethod
    async def _organize(self, block_id: BlockID) -> None:
        """Organize the collected block.

        Organization to collected blocks are concurrently.
        """

    def get_config(self) -> ConfigTV:
        """Get the configuration of the source."""
        with SessionLocal() as db:
            source = db.exec(
                sqlmodel.select(SourceModel).where(SourceModel.id == self._id)
            ).one()
            return typing.cast(ConfigTV, self.__configcls__.model_validate(source.config))

    def get_state(self) -> dict:
        """Get the source state from database."""
        with SessionLocal() as db:
            source = db.exec(
                sqlmodel.select(SourceModel).where(SourceModel.id == self._id)
            ).one()
            return source.state or {}

    def set_state(self, state: dict) -> None:
        """Save the source state to database."""
        with SessionLocal() as db:
            source = db.exec(
                sqlmodel.select(SourceModel).where(SourceModel.id == self._id)
            ).one()
            source.state = state
            db.add(source)
            db.commit()


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
            config_schema=source_cls.__configschema__,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[SourceTypesModel.id],
            set_=dict(
                description=stmt.excluded.description,
                config_schema=stmt.excluded.config_schema,
            ),
        )

        with SessionLocal() as db:
            db.exec(stmt)  # type: ignore
            db.commit()
            # return db.exec(
            #     sqlmodel.select(SourceTypesModel).where(SourceTypesModel.id == source_type)
            # ).one()

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
                with SessionLocal() as db:
                    source_type = db.exec(
                        sqlmodel.select(SourceModel.type).where(SourceModel.id == source_id)
                    ).one()
            source_class = cls._SOURCE_CLASSES.get(source_type, None)
            if source_class is None:
                raise ValueError(f"Source class {source_type} not registered.")
            ins = source_class(_id=typing.cast(SourceID, source_id))
            cls.SOURCES[source_id] = ins
        return ins

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
    async def run(cls, job_id: SourceCollectJobID):
        with SessionLocal() as db:
            job = db.exec(
                sqlmodel.select(SourceCollectJobModel).where(
                    SourceCollectJobModel.id == job_id
                )
            ).one()

            job.status = SourceCollectJobStatus.RUNNING
            job.started_at = datetime.datetime.now(datetime.timezone.utc)
            db.add(job)
            db.commit()
            db.refresh(job)

            try:
                # Fetch source instance and run collect
                source_ins = SourceManager._get_source_ins(job.source)

                await source_ins.collect(job)
                job.status = SourceCollectJobStatus.FINISHED
            except Exception as e:
                LOGGER.error(f"Error running job {job_id}: {e}")
                job.status = SourceCollectJobStatus.FAILED
                job.state = {"error": str(e)}
            finally:
                job.closed_at = datetime.datetime.now(datetime.timezone.utc)
                db.add(job)
                db.commit()

    @classmethod
    async def check_pending(cls):
        """Check for pending source collect jobs and handle them."""
        with SessionLocal() as db:
            pending_jobs = db.exec(
                sqlmodel.select(SourceCollectJobModel).where(
                    SourceCollectJobModel.status == SourceCollectJobStatus.PENDING
                )
            ).all()

        for job in pending_jobs:
            # Schedule the collect
            scheduler.add_job(
                func=with_trace_id(f"source_collect_job.{job.id}", cls.run),
                args=[job.id],
                misfire_grace_time=None,
            )
