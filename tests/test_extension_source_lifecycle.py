"""Extension-owned Source type, instance, and scheduler lifecycle proofs."""

from __future__ import annotations

import asyncio
import typing

import fastapi
import pytest
import sqlmodel

import app.business.source.main as source_module
import app.business.source.collect_job as collect_job_module
from app.business.extension.runtime import ExtensionPublicationSnapshot
from app.business.source.collect_job import SourceCollectJobManager
from app.business.source.main import (
  SourceBase,
  SourceManager,
)
from app.schemas.info_base.block import BlockID
from app.schemas.source import CollectAt, SourceCollectJobModel, SourceModel


class SourceConfig(sqlmodel.SQLModel): ...


class FakeScheduler:
  def __init__(self) -> None:
    self.jobs: dict[
      str,
      tuple[typing.Callable[..., typing.Any], tuple[object, ...]],
    ] = {}

  def add_job(self, func, *, id: str, args=(), **kwargs) -> None:
    self.jobs[id] = (func, tuple(args))

  def get_job(self, job_id: str):
    return self.jobs.get(job_id)

  def remove_job(self, job_id: str) -> None:
    self.jobs.pop(job_id)

  async def tick(self) -> None:
    for callback, args in tuple(self.jobs.values()):
      await callback(*args)


def make_source_class():
  class ExtensionSource(SourceBase[SourceConfig], config_cls=SourceConfig):
    collections = 0

    async def collect(self, job: SourceCollectJobModel) -> None:
      type(self).collections += 1

    async def _organize(self, block_id: BlockID) -> None: ...

  transient_key = f"{ExtensionSource.__module__}.{ExtensionSource.__qualname__}"
  SourceManager._SOURCE_CLASSES.pop(transient_key)
  ExtensionSource.__module__ = "extensions.fixture.source"
  ExtensionSource.__qualname__ = "Source"
  return ExtensionSource


def test_sync_source_types_persists_only_the_selected_publication(monkeypatch):
  source_class = make_source_class()
  source_type = "extensions.fixture.source.Source"
  other_type = "extensions.other.source.Source"
  statements: list[dict[str, object]] = []

  class FakeSession:
    def __enter__(self):
      return self

    def __exit__(self, *args):
      return None

    def exec(self, statement):
      statements.append(statement.compile().params)

    def commit(self):
      return None

  monkeypatch.setattr(source_module, "SessionLocal", FakeSession)
  SourceManager.sync_source_types({source_type: source_class})

  assert [statement["id"] for statement in statements] == [source_type]
  assert all(statement["id"] != other_type for statement in statements)


def test_publication_withdraws_only_its_jobs_and_instances_without_deleting_rows(
  monkeypatch,
):
  before_types = SourceManager.snapshot_source_types()
  before_sources = dict(SourceManager.SOURCES)
  before_rows = dict(SourceManager._SOURCE_ROW_TYPES)
  before_instances = dict(SourceManager._SOURCE_INSTANCE_TYPES)
  before_jobs = dict(SourceManager._SOURCE_JOB_TYPES)
  fake_scheduler = FakeScheduler()
  durable_rows = [
    SourceModel(
      id=41,
      type="extensions.fixture.source.Source",
      collect_at=CollectAt(hour=1, minute=2),
    ),
    SourceModel(id=42, type="extensions.other.source.Source"),
  ]
  synced: list[set[str]] = []
  try:
    app = fastapi.FastAPI()
    snapshot = ExtensionPublicationSnapshot.capture(app)
    source_class = make_source_class()
    source_type = "extensions.fixture.source.Source"
    SourceManager.add_source_type(source_class)
    publication = snapshot.finish()
    monkeypatch.setattr(source_module, "scheduler", fake_scheduler)
    monkeypatch.setattr(
      SourceManager,
      "sync_source_types",
      classmethod(lambda cls, selected=None: synced.append(set(selected or ()))),
    )
    monkeypatch.setattr(
      SourceManager,
      "_source_rows",
      classmethod(
        lambda cls, selected=None: tuple(
          row for row in durable_rows if selected is None or row.type in selected
        )
      ),
    )

    publication.activate_source_types()
    assert synced == [{source_type}]
    assert set(fake_scheduler.jobs) == {"source.41.collect"}
    assert isinstance(SourceManager.get_source_ins(41), source_class)
    assert isinstance(SourceManager.SOURCES[41], source_class)
    captured_collect = SourceManager.SOURCES[41].collect

    class CreateSession:
      def __enter__(self):
        return self

      def __exit__(self, *args):
        return None

      def add(self, source):
        self.source = source

      def commit(self):
        return None

      def refresh(self, source):
        source.id = 43
        durable_rows.append(source)

    monkeypatch.setattr(source_module, "SessionLocal", CreateSession)
    created = SourceManager.create(source_type, "Live")
    assert created.id == 43
    SourceManager.get_source_ins(43)
    assert 43 in SourceManager.SOURCES

    monkeypatch.setattr(
      SourceManager,
      "_source_rows",
      classmethod(
        lambda cls, selected=None: (_ for _ in ()).throw(
          AssertionError("teardown must not query durable Source rows")
        )
      ),
    )
    publication.restore()
    asyncio.run(fake_scheduler.tick())
    assert source_class.collections == 0
    assert captured_collect.__self__ is not None
    assert 41 not in SourceManager.SOURCES
    assert 43 not in SourceManager.SOURCES
    assert fake_scheduler.jobs == {}
    assert [row.id for row in durable_rows] == [41, 42, 43]

    reenable_snapshot = ExtensionPublicationSnapshot.capture(app)
    SourceManager.add_source_type(source_class)
    reenabled = reenable_snapshot.finish()
    monkeypatch.setattr(
      SourceManager,
      "_source_rows",
      classmethod(
        lambda cls, selected=None: tuple(
          row for row in durable_rows if selected is None or row.type in selected
        )
      ),
    )
    reenabled.activate_source_types()
    assert set(fake_scheduler.jobs) == {"source.41.collect"}
    assert isinstance(SourceManager.get_source_ins(41), source_class)
    reenabled.restore()
  finally:
    SourceManager._SOURCE_CLASSES = before_types
    SourceManager.SOURCES = before_sources
    SourceManager._SOURCE_ROW_TYPES = before_rows
    SourceManager._SOURCE_INSTANCE_TYPES = before_instances
    SourceManager._SOURCE_JOB_TYPES = before_jobs


def test_scheduled_callback_without_parameters_creates_and_runs_a_durable_job(
  monkeypatch,
):
  fake_scheduler = FakeScheduler()
  row = SourceModel(
    id=51,
    type="extensions.fixture.source.Source",
    collect_at=CollectAt(hour=3, minute=4),
  )
  created: list[SourceCollectJobModel] = []
  run_ids: list[int] = []

  class JobSession:
    def __enter__(self):
      return self

    def __exit__(self, *args):
      return None

    def add(self, job):
      created.append(job)

    def commit(self):
      return None

    def refresh(self, job):
      job.id = 71

  async def run_job(cls, job_id):
    run_ids.append(job_id)

  monkeypatch.setattr(source_module, "scheduler", fake_scheduler)
  monkeypatch.setattr(source_module, "SessionLocal", JobSession)
  monkeypatch.setattr(
    SourceManager,
    "_source_rows",
    classmethod(lambda cls, selected=None: (row,)),
  )
  monkeypatch.setattr(SourceCollectJobManager, "run", classmethod(run_job))
  activation = SourceManager.set_up_collect_jobs({row.type})

  asyncio.run(fake_scheduler.tick())

  assert [(job.source, job.config) for job in created] == [(51, {})]
  assert run_ids == [71]
  SourceManager.withdraw_runtime_activation(activation)


def test_partial_scheduler_activation_rolls_back_added_jobs_and_type_ownership(
  monkeypatch,
):
  class FailingScheduler(FakeScheduler):
    def add_job(self, func, *, id: str, args=(), **kwargs) -> None:
      if len(self.jobs) == 1:
        raise RuntimeError("scheduler failed")
      super().add_job(func, id=id, args=args, **kwargs)

  fake_scheduler = FailingScheduler()
  source_type = "extensions.fixture.source.Source"
  rows = (
    SourceModel(id=61, type=source_type, collect_at=CollectAt(hour=1)),
    SourceModel(id=62, type=source_type, collect_at=CollectAt(hour=2)),
  )
  monkeypatch.setattr(source_module, "scheduler", fake_scheduler)
  monkeypatch.setattr(
    SourceManager,
    "_source_rows",
    classmethod(lambda cls, selected=None: rows),
  )

  with pytest.raises(RuntimeError, match="scheduler failed"):
    SourceManager.set_up_collect_jobs({source_type})

  assert fake_scheduler.jobs == {}
  assert not {
    source_id
    for source_id, owner in SourceManager._SOURCE_ROW_TYPES.items()
    if owner == source_type
  }


def test_collect_job_claim_prevents_the_same_pending_job_from_running_twice(
  monkeypatch,
):
  job = SourceCollectJobModel(id=91, source=41)
  statements: list[typing.Any] = []
  collections = 0

  class Result:
    def one_or_none(self):
      return job if job.status.value == "pending" else None

  class JobSession:
    def __enter__(self):
      return self

    def __exit__(self, *args):
      return None

    def exec(self, statement):
      statements.append(statement)
      return Result()

    def add(self, model):
      return None

    def commit(self):
      return None

    def refresh(self, model):
      return None

  class FakeSource:
    async def collect(self, claimed_job):
      nonlocal collections
      collections += 1

  monkeypatch.setattr(collect_job_module, "SessionLocal", JobSession)
  monkeypatch.setattr(
    SourceManager,
    "_get_source_ins",
    classmethod(lambda cls, source_id, source_type=None: FakeSource()),
  )

  assert asyncio.run(SourceCollectJobManager.run(91)) is True
  assert asyncio.run(SourceCollectJobManager.run(91)) is False
  assert collections == 1
  assert statements[0]._for_update_arg.skip_locked is True
