"""Real PostgreSQL proof for lexical projection, freshness, and ranking."""

import asyncio
import os

import pytest
import sqlalchemy

from app.business.info_base import BlockManager
from app.business.info_base.resolver import register_core_resolvers
from app.business.cron import CronManager
from app.business.job import JobManager
from app.business.lexical_retrieval import (
  LEXICAL_MAINTAIN_JOB_TYPE,
  LEXICAL_REBUILD_JOB_TYPE,
  LexicalRetrievalManager,
)
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockForm
from app.schemas.cron import CronModel
from app.schemas.job import JobModel, JobStatus
from app.schemas.lexical_retrieval import LexicalMaintenanceOptions


pytestmark = pytest.mark.skipif(
  not os.getenv("INKCRE_TEST_DATABASE_URL"),
  reason="requires an explicitly selected migrated PostgreSQL runtime",
)


def _reset() -> None:
  with SessionLocal() as db:
    db.connection().execute(
      sqlalchemy.text(
        "TRUNCATE TABLE inkcre.block_lexical_records, inkcre.relations, "
        "inkcre.blocks RESTART IDENTITY CASCADE"
      )
    )
    db.commit()


def _text(content: str) -> int:
  block = BlockManager.create(BlockForm(resolver="core.text.v1", content=content))
  assert block.id is not None
  return block.id


def test_literal_chinese_ranking_freshness_and_cascade():
  _reset()
  register_core_resolvers()
  phrase = _text("alpha beta is one continuous technical identifier")
  terms_only = _text("alpha appears here while unrelated details separate beta")
  chinese = _text("这段材料记录了星间链路故障注入的完整过程")
  deleted = _text("ephemeral deletion clue")

  report = asyncio.run(
    LexicalRetrievalManager.maintain(
      LexicalMaintenanceOptions(max_records=20, scan_page_size=2)
    )
  )
  assert report.indexed == 4
  assert report.failed == report.unavailable == 0

  ranked = LexicalRetrievalManager.retrieve_local("alpha beta")
  assert [match.block.id for match in ranked.matches[:2]] == [phrase, terms_only]
  assert ranked.matches[0].evidence == "label_substring"
  assert ranked.matches[1].evidence == "terms"

  chinese_result = LexicalRetrievalManager.retrieve_local("链路故障")
  assert chinese_result.matches[0].block.id == chinese
  assert chinese_result.matches[0].evidence == "label_substring"

  BlockManager.edit_block(phrase, content="replacement clue after authoritative edit")
  assert not LexicalRetrievalManager.retrieve_local("continuous technical").matches
  update = asyncio.run(LexicalRetrievalManager.maintain())
  assert update.indexed == 1
  updated_result = LexicalRetrievalManager.retrieve_local("replacement clue")
  assert updated_result.matches[0].block.id == phrase

  assert BlockManager.delete(deleted)
  with SessionLocal() as db:
    remaining = (
      db.connection()
      .execute(
        sqlalchemy.text(
          "SELECT count(*) FROM inkcre.block_lexical_records WHERE block = :block"
        ),
        {"block": deleted},
      )
      .scalar_one()
    )
  assert remaining == 0


def test_unknown_resolver_is_bounded_unavailable_diagnostic():
  _reset()
  block = BlockManager.create(BlockForm(resolver="unknown.lexical.v1", content="opaque"))
  assert block.id is not None

  report = asyncio.run(
    LexicalRetrievalManager.maintain(
      LexicalMaintenanceOptions(max_records=1, diagnostic_limit=1)
    )
  )

  assert report.indexed == report.failed == 0
  assert report.unavailable == 1
  assert report.diagnostics[0].block == block.id
  assert report.diagnostics[0].reason == "unknown_resolver"


def test_direct_and_cron_created_jobs_share_exact_handler_path():
  _reset()
  register_core_resolvers()
  _text("scheduled lexical maintenance clue")
  JobManager.sync_job_types()

  direct = JobManager.create(
    LEXICAL_MAINTAIN_JOB_TYPE,
    {"options": {"max_records": 10, "scan_page_size": 10}},
  )
  assert direct.id is not None
  assert asyncio.run(JobManager.run(direct.id))
  with SessionLocal() as db:
    persisted = db.get(JobModel, direct.id)
    assert persisted is not None
    assert persisted.status == JobStatus.FINISHED
    assert persisted.state["indexed"] == 1

    cron = CronModel(
      schedule="* * * * *",
      job_type=LEXICAL_REBUILD_JOB_TYPE,
      job_parameters={"options": {"max_records": 10}},
    )
    db.add(cron)
    db.commit()
    db.refresh(cron)
    assert cron.id is not None
    cron_id = cron.id

  scheduled = CronManager.run_now(cron_id)
  assert scheduled.type == LEXICAL_REBUILD_JOB_TYPE
  assert scheduled.id is not None
  assert asyncio.run(JobManager.run(scheduled.id))
  with SessionLocal() as db:
    persisted = db.get(JobModel, scheduled.id)
    assert persisted is not None
    assert persisted.status == JobStatus.FINISHED
    assert persisted.state["indexed"] == 1
