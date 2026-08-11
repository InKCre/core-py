"""Shared RSS/Atom collection command and source-owned policy."""

from __future__ import annotations

import asyncio
import dataclasses

import pydantic

from app.business.info_base.block import BlockManager
from app.business.info_base.resolver import ResolverManager
from app.schemas.job import JobModel
from utils.datetime_ import get_datetimez

from .adapter import FeedParserContext, parse_feed_snapshot
from .http import HTTPFetchOptions, fetch_http_bytes
from .repository import FeedGraphRepository, ReconcileResult
from .schema import (
  FeedCollectJobConfig,
  FeedFamily,
  FeedSourceConfig,
  FeedSourceState,
  ParsedFeedItem,
  SolvedFeedItem,
)


@dataclasses.dataclass(frozen=True)
class EffectiveRunConfig:
  fetch_full_text: bool
  download_enclosures: bool
  target_storage_id: int


class FeedCollectionService:
  """Execute one bounded collection command for either protocol wrapper."""

  def __init__(self, source_instance_id: int, expected_family: FeedFamily):
    self._source_instance_id = source_instance_id
    self._expected_family = expected_family

  @staticmethod
  def _effective_run_config(
    source_config: FeedSourceConfig,
    job_config: FeedCollectJobConfig,
  ) -> EffectiveRunConfig:
    return EffectiveRunConfig(
      fetch_full_text=(
        source_config.fetch_full_text
        if job_config.fetch_full_text is None
        else job_config.fetch_full_text
      ),
      download_enclosures=(
        source_config.download_enclosures
        if job_config.download_enclosures is None
        else job_config.download_enclosures
      ),
      target_storage_id=(
        source_config.target_storage_id
        if job_config.target_storage_id is None
        else job_config.target_storage_id
      ),
    )

  @staticmethod
  def _admit_unidentified_item(
    item: ParsedFeedItem,
    source_config: FeedSourceConfig,
    previous_state: FeedSourceState,
  ) -> tuple[bool, str | None]:
    if item.item.identity() is not None:
      return True, None
    if source_config.unidentified_item_behavior == "discard":
      return False, "unidentified_item_discarded"
    watermark = previous_state.last_successful_contentful_snapshot_observed_at
    source_time = item.item.source_time()
    if source_time is not None and watermark is not None and source_time <= watermark:
      return False, "unidentified_item_before_watermark"
    return True, None

  async def collect(
    self,
    source_config: FeedSourceConfig,
    previous_state: FeedSourceState,
    job: JobModel,
    job_config: FeedCollectJobConfig,
  ) -> FeedSourceState:
    """Collect primary graphs and return state that may advance after success."""
    effective = self._effective_run_config(source_config, job_config)
    request_state = (
      previous_state
      if previous_state.snapshot_configured_url == source_config.feed_url
      else FeedSourceState()
    )
    diagnostics: list[dict[str, object]] = []
    job.state = {
      "family": self._expected_family,
      "feed_url": source_config.feed_url,
      "diagnostics": diagnostics,
    }

    response = await fetch_http_bytes(
      source_config.feed_url,
      options=HTTPFetchOptions(
        timeout_seconds=source_config.request_timeout_seconds,
        max_response_bytes=source_config.max_feed_bytes,
        user_agent=source_config.user_agent,
      ),
      etag=request_state.etag,
      last_modified=request_state.last_modified,
    )
    if response.status == 304:
      job.state.update(
        {
          "not_modified": True,
          "items": {"created": 0, "updated": 0, "unchanged": 0, "skipped": 0},
        }
      )
      return previous_state.model_copy(
        update={
          "etag": response.etag,
          "last_modified": response.last_modified,
        }
      )

    snapshot_observed_at = get_datetimez()
    snapshot = await asyncio.to_thread(
      parse_feed_snapshot,
      response.body,
      FeedParserContext(
        expected_family=self._expected_family,
        source_instance_id=self._source_instance_id,
        configured_url=source_config.feed_url,
        effective_url=response.effective_url,
        response_headers=response.headers,
      ),
    )
    diagnostics.extend(snapshot.diagnostics)
    feed_result = FeedGraphRepository.reconcile_feed(snapshot.feed)
    admission_state = (
      previous_state
      if previous_state.snapshot_feed_block_id == feed_result.block_id
      else FeedSourceState()
    )
    counts = {"created": 0, "updated": 0, "unchanged": 0, "skipped": 0}
    item_block_ids: list[int] = []
    reconciled_items: list[tuple[ParsedFeedItem, ReconcileResult]] = []

    for index, parsed_item in enumerate(snapshot.items):
      admitted, skip_code = self._admit_unidentified_item(
        parsed_item,
        source_config,
        admission_state,
      )
      if not admitted:
        counts["skipped"] += 1
        diagnostics.append(
          {
            "scope": "item",
            "code": skip_code or "item_not_admitted",
            "item_index": index,
          }
        )
        continue
      try:
        result = FeedGraphRepository.reconcile_item(
          feed_result.block_id,
          parsed_item.item,
          parsed_item.enclosures,
        )
      except Exception as error:
        diagnostics.append(
          {
            "scope": "item",
            "code": "primary_persistence_failed",
            "item_index": index,
            "message": str(error),
          }
        )
        job.state.update(
          {
            "snapshot_observed_at": snapshot_observed_at.isoformat(),
            "feed": dataclasses.asdict(feed_result),
            "items": counts,
          }
        )
        raise
      counts[result.action] += 1
      item_block_ids.append(result.block_id)
      reconciled_items.append((parsed_item, result))

    enrichment_counts = {
      "full_text_created": 0,
      "full_text_existing": 0,
      "full_text_updated": 0,
      "full_text_unavailable": 0,
      "enclosure_created": 0,
      "enclosure_existing": 0,
      "failed": 0,
    }
    if effective.fetch_full_text:
      from .enrichment import FullTextEnrichmentService

      for index, (_, result) in enumerate(reconciled_items):
        try:
          enriched = await FullTextEnrichmentService.materialize(
            result.block_id,
            refresh=result.alternate_url_changed,
          )
          enrichment_counts[f"full_text_{enriched.status}"] += 1
        except Exception as error:
          enrichment_counts["failed"] += 1
          diagnostics.append(
            {
              "scope": "full_text",
              "code": "enrichment_failed",
              "item_index": index,
              "message": str(error),
            }
          )

    if effective.download_enclosures:
      for index, (_, result) in enumerate(reconciled_items):
        block = BlockManager.get(result.block_id)
        if block is None:
          continue
        solved = await ResolverManager.get(block).get_solved_content(
          materialize_missing=False
        )
        if not isinstance(solved, SolvedFeedItem):
          raise TypeError("feed item resolver returned an unexpected solved value")
        for enclosure_block_id in solved.enclosure_block_ids:
          enclosure_block = BlockManager.get(enclosure_block_id)
          if enclosure_block is None:
            continue
          resolver = ResolverManager.get(enclosure_block)
          try:
            materialized = await resolver.materialize_content(  # type: ignore[attr-defined]
              target_storage_id=effective.target_storage_id
            )
            enrichment_counts[f"enclosure_{materialized.status}"] += 1
          except Exception as error:
            enrichment_counts["failed"] += 1
            diagnostics.append(
              {
                "scope": "enclosure",
                "code": "materialization_failed",
                "item_index": index,
                "enclosure_block_id": enclosure_block_id,
                "message": str(error),
              }
            )

    job.state.update(
      {
        "snapshot_observed_at": snapshot_observed_at.isoformat(),
        "feed": dataclasses.asdict(feed_result),
        "items": counts,
        "primary_item_block_ids": item_block_ids,
        "enrichment": {
          "fetch_full_text": effective.fetch_full_text,
          "download_enclosures": effective.download_enclosures,
          "target_storage_id": effective.target_storage_id,
          "results": enrichment_counts,
        },
      }
    )
    return FeedSourceState(
      etag=response.etag,
      last_modified=response.last_modified,
      last_successful_contentful_snapshot_observed_at=snapshot_observed_at,
      snapshot_configured_url=source_config.feed_url,
      snapshot_feed_block_id=feed_result.block_id,
    )


def validate_source_state(value: dict) -> FeedSourceState:
  try:
    return FeedSourceState.model_validate(value)
  except pydantic.ValidationError as error:
    raise ValueError("RSS source state is invalid") from error


__all__ = ["EffectiveRunConfig", "FeedCollectionService", "validate_source_state"]
