"""One protocol-neutral Mail Source backed by the selected public adapter."""

from __future__ import annotations

import typing

import pydantic
import sqlmodel

from app.business.source import SourceBase
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockModel
from app.schemas.job import JobModel
from app.schemas.source import SourceModel
from libs.obsrv.main import get_logger

from .adapter import create_mail_adapter
from .repository import MailGraphRepository
from .schema import (
  IMAPCheckpoint,
  MailBackfillConfig,
  MailCollectConfig,
  MailboxExclusionPolicy,
  MailSourceConfig,
  MailSourceState,
)


LOGGER = get_logger().getChild(__name__)


class MailSourceBindingError(RuntimeError):
  """A configured Source no longer points at its accepted access context."""


def _mail_extension_default_exclusions() -> MailboxExclusionPolicy:
  """Read current extension defaults without requiring a running API mount."""
  from app.business.extension.main import ExtensionManager
  from . import Extension

  running = ExtensionManager.RUNNING_EXTENSIONS.get("mail")
  if running is not None:
    return typing.cast(type[Extension], running).config.default_excluded_mailboxes
  persisted = ExtensionManager.get("mail")
  config = Extension.validate_config({} if persisted is None else persisted.config or {})
  return config.default_excluded_mailboxes


class Source(
  SourceBase[MailSourceConfig],
  config_cls=MailSourceConfig,
  collect_config_cls=MailCollectConfig,
  backfill_config_cls=MailBackfillConfig,
):
  """Collect Mail through one configured public protocol access context."""

  async def collect(self, job: JobModel, config: pydantic.BaseModel) -> None:
    MailCollectConfig.model_validate(config)
    source, setup = self._load_effective_source()
    state = MailSourceState.model_validate(source.state or {})
    diagnostics: list[dict[str, typing.Any]] = []
    counts = {"messages": 0, "flag_changes": 0, "removals": 0, "mailboxes": 0}
    job.state = {"diagnostics": diagnostics, "counts": counts}

    adapter = create_mail_adapter(setup.protocol, setup.parameters)
    async with adapter:
      state = self._accept_binding(state, adapter.binding)
      self._persist_state(state)
      exclusions = setup.excluded_mailboxes
      if exclusions is None:  # pragma: no cover - materialization postcondition
        raise RuntimeError("Mail Source exclusions were not materialized")
      mailboxes = await adapter.discover_mailboxes(exclusions)
      for mailbox_fact in mailboxes:
        try:
          mailbox_id = self._ensure_mailbox(mailbox_fact, state)
          checkpoint = state.checkpoints.get(str(mailbox_id))
          changes = await adapter.read_ordinary_changes(
            mailbox_fact,
            checkpoint,
            source.created_at,
          )
          for message in changes.messages:
            self._persist_message(mailbox_id, message)
            counts["messages"] += 1
            if setup.ordinary_mark_as_seen and "\\seen" not in {
              flag.casefold() for flag in message.flags
            }:
              try:
                await adapter.mark_seen(mailbox_fact.mailbox.name, message.uid)
              except Exception as error:
                diagnostics.append(
                  {
                    "scope": "seen",
                    "mailbox": mailbox_fact.mailbox.name,
                    "uid": message.uid,
                    "message": str(error),
                  }
                )
              else:
                self._persist_seen(mailbox_id, message)
          for change in changes.flag_changes:
            if self._persist_flag_change(mailbox_id, change):
              counts["flag_changes"] += 1
          if setup.synchronize_deletions:
            for uid in changes.removed_uids:
              if self._remove_occurrence(
                mailbox_id,
                changes.next_checkpoint.uid_validity,
                uid,
              ):
                counts["removals"] += 1
          self._merge_checkpoint(mailbox_id, checkpoint, changes.next_checkpoint)
          state.checkpoints[str(mailbox_id)] = changes.next_checkpoint
          counts["mailboxes"] += 1
        except Exception as error:
          LOGGER.exception(
            "Mail mailbox collection failed",
            extra={"source": self._id, "mailbox": mailbox_fact.mailbox.name},
          )
          diagnostics.append(
            {
              "scope": "mailbox",
              "mailbox": mailbox_fact.mailbox.name,
              "message": str(error),
            }
          )

  async def backfill(self, job: JobModel, config: pydantic.BaseModel) -> None:
    interval = MailBackfillConfig.model_validate(config)
    _source, setup = self._load_effective_source()
    state = MailSourceState.model_validate(self.get_state())
    diagnostics: list[dict[str, typing.Any]] = []
    count = 0
    job.state = {"diagnostics": diagnostics, "messages": count}

    adapter = create_mail_adapter(setup.protocol, setup.parameters)
    async with adapter:
      state = self._accept_binding(state, adapter.binding)
      self._persist_state(state)
      exclusions = setup.excluded_mailboxes
      if exclusions is None:  # pragma: no cover - materialization postcondition
        raise RuntimeError("Mail Source exclusions were not materialized")
      for mailbox_fact in await adapter.discover_mailboxes(exclusions):
        try:
          mailbox_id = self._ensure_mailbox(mailbox_fact, state)
          for message in await adapter.read_backfill(mailbox_fact, interval):
            self._persist_message(mailbox_id, message)
            count += 1
            if setup.backfill_mark_as_seen and "\\seen" not in {
              flag.casefold() for flag in message.flags
            }:
              try:
                await adapter.mark_seen(mailbox_fact.mailbox.name, message.uid)
              except Exception as error:
                diagnostics.append(
                  {
                    "scope": "seen",
                    "mailbox": mailbox_fact.mailbox.name,
                    "uid": message.uid,
                    "message": str(error),
                  }
                )
              else:
                self._persist_seen(mailbox_id, message)
        except Exception as error:
          LOGGER.exception(
            "Mail mailbox backfill failed",
            extra={"source": self._id, "mailbox": mailbox_fact.mailbox.name},
          )
          diagnostics.append(
            {
              "scope": "mailbox",
              "mailbox": mailbox_fact.mailbox.name,
              "message": str(error),
            }
          )
    job.state["messages"] = count

  def _load_effective_source(self) -> tuple[SourceModel, MailSourceConfig]:
    """Materialize extension exclusions once when the Source still inherits them."""
    with SessionLocal() as db:
      source = db.exec(
        sqlmodel.select(SourceModel).where(SourceModel.id == self._id).with_for_update()
      ).one()
      config = MailSourceConfig.model_validate(source.config)
      if config.excluded_mailboxes is None:
        config = config.model_copy(
          update={"excluded_mailboxes": _mail_extension_default_exclusions()}
        )
        source.config = config.model_dump(mode="json")
        db.add(source)
        db.commit()
        db.refresh(source)
      return source, config

  @staticmethod
  def _accept_binding(state: MailSourceState, binding) -> MailSourceState:
    if state.binding is not None and state.binding != binding:
      raise MailSourceBindingError(
        "Mail Source access binding changed; create a new Source for a different context"
      )
    return state.model_copy(update={"binding": binding})

  def _persist_state(self, state: MailSourceState) -> None:
    self.set_state(state.model_dump(mode="json"))

  def _ensure_mailbox(self, fact, state: MailSourceState) -> int:
    with SessionLocal() as db:
      source = db.get(SourceModel, self._id)
      if source is None:  # pragma: no cover - Job eligibility invariant
        raise ValueError("Mail Source no longer exists")
      repository = MailGraphRepository(db, source)
      mailbox = repository.ensure_mailbox(fact)
      if mailbox.id is None:
        raise RuntimeError("Persisted Mailbox has no ID")
      previous = state.checkpoints.get(str(mailbox.id))
      if previous is not None and previous.uid_validity != fact.uid_validity:
        repository.clear_stale_epoch(mailbox.id, fact.uid_validity)
      db.commit()
      return mailbox.id

  def _persist_message(self, mailbox_id: int, fact) -> None:
    with SessionLocal() as db:
      source = db.get(SourceModel, self._id)
      mailbox = db.get(BlockModel, mailbox_id)
      if source is None or mailbox is None:
        raise ValueError("Mail graph provenance is no longer available")
      MailGraphRepository(db, source).reconcile_message(mailbox, fact)
      db.commit()

  def _persist_seen(self, mailbox_id: int, fact) -> None:
    flags = tuple((*fact.flags, "\\Seen"))
    with SessionLocal() as db:
      source = db.get(SourceModel, self._id)
      mailbox = db.get(BlockModel, mailbox_id)
      if source is None or mailbox is None:
        return
      MailGraphRepository(db, source).reconcile_flag_change(
        mailbox,
        fact.uid_validity,
        fact.uid,
        flags,
      )
      db.commit()

  def _persist_flag_change(self, mailbox_id: int, change) -> bool:
    with SessionLocal() as db:
      source = db.get(SourceModel, self._id)
      mailbox = db.get(BlockModel, mailbox_id)
      if source is None or mailbox is None:
        return False
      changed = MailGraphRepository(db, source).reconcile_flag_change(
        mailbox,
        change.uid_validity,
        change.uid,
        change.flags,
      )
      db.commit()
      return changed

  def _remove_occurrence(self, mailbox_id: int, uid_validity: int, uid: int) -> bool:
    with SessionLocal() as db:
      source = db.get(SourceModel, self._id)
      mailbox = db.get(BlockModel, mailbox_id)
      if source is None or mailbox is None:
        return False
      removed = MailGraphRepository(db, source).remove_occurrence(
        mailbox,
        uid_validity,
        uid,
      )
      db.commit()
      return removed

  def _merge_checkpoint(
    self,
    mailbox_id: int,
    observed: IMAPCheckpoint | None,
    proposed: IMAPCheckpoint,
  ) -> None:
    """Advance one mailbox only when its persisted base is still observed."""
    with SessionLocal() as db:
      source = db.exec(
        sqlmodel.select(SourceModel).where(SourceModel.id == self._id).with_for_update()
      ).one()
      state = MailSourceState.model_validate(source.state or {})
      current = state.checkpoints.get(str(mailbox_id))
      if current != observed:
        return
      state.checkpoints[str(mailbox_id)] = proposed
      source.state = state.model_dump(mode="json")
      db.add(source)
      db.commit()
