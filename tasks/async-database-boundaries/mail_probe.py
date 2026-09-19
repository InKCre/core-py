"""Task-scoped Mail graph and checkpoint invariants on isolated PostgreSQL."""

import asyncio
import uuid
from unittest.mock import patch

from app.business.source import SourceManager
from app.engine import ASYNC_DB_ENGINE
from app.persistence.source.uow import source_uow
from extensions.mail.source import Source
from extensions.mail.reconcile import MailGraphReconciler
from extensions.mail.schema import (
  BodyFact,
  CanonicalEmail,
  CanonicalMailbox,
  IMAPCheckpoint,
  MailboxFact,
  MailSourceState,
  MessageFact,
  ParticipantFact,
)


async def exercise():
  key = uuid.uuid4().hex
  await SourceManager.sync_source_types_async()
  source = await SourceManager.create(
    f"{Source.__module__}.{Source.__qualname__}",
    config={
      "protocol": "imap",
      "parameters": {"host": "example.test", "username": key, "password": "probe"},
    },
  )
  assert source.id is not None
  instance = Source(source.id)
  try:
    mailbox = await instance._ensure_mailbox(
      MailboxFact(mailbox=CanonicalMailbox(name="Inbox"), uid_validity=1), MailSourceState()
    )
    message = MessageFact(
      uid=1,
      uid_validity=1,
      root=CanonicalEmail(message_id=key, subject="probe"),
      bodies=(BodyFact(part_id="1", media_type="text/plain", content=key),),
      participants=(ParticipantFact(role="from", order=0, address=key + "@example.test"),),
      flags=("\\Seen",),
    )
    await instance._persist_message(mailbox, message)
    await instance._persist_message(mailbox, message)
    async with source_uow() as uow:
      relations = await uow.graph.relations.get(mailbox, include_in=False)
      occurrences = [r for r in relations if '"contains"' in r.content]
      assert len(occurrences) == 1
    proposed = IMAPCheckpoint(uid_validity=1, last_uid=1)
    await instance._merge_checkpoint(mailbox, None, proposed)
    await instance._merge_checkpoint(
      mailbox, None, IMAPCheckpoint(uid_validity=1, last_uid=8)
    )
    stored = await SourceManager.get(source.id)
    assert stored is not None and stored.state["checkpoints"][str(mailbox)]["last_uid"] == 1

    original = MailGraphReconciler._reconcile_references

    async def fail(self, block, fact):
      await original(self, block, fact)
      raise RuntimeError("injected after primary writes")

    with patch.object(MailGraphReconciler, "_reconcile_references", fail):
      try:
        await instance._persist_message(
          mailbox,
          message.model_copy(
            update={"uid": 2, "root": CanonicalEmail(message_id=key + "-other")}
          ),
        )
      except RuntimeError:
        pass
      else:
        raise AssertionError("expected failure")
    async with source_uow() as uow:
      assert not await uow.graph.blocks.find_json_field(
        "extensions.mail.email.v1", "message_id", key + "-other"
      )
    assert await instance._remove_occurrence(mailbox, 1, 1)
    assert not await instance._remove_occurrence(mailbox, 1, 1)
    print("PASS: Mail replay, checkpoint, rollback and occurrence removal")
  finally:
    async with source_uow() as uow:
      stored = await uow.sources.get(source.id)
      if stored is not None:
        pending = [stored.block] if stored.block is not None else []
        seen = set()
        # The unique probe identities cannot be shared with another Source.
        while pending:
          block_id = pending.pop()
          if block_id in seen:
            continue
          seen.add(block_id)
          for relation in await uow.graph.relations.get(block_id):
            pending.extend((relation.from_, relation.to_))
        # Removed occurrences no longer reach the Email; include its probe root.
        for block in await uow.graph.blocks.find_json_field(
          "extensions.mail.email.v1", "message_id", key
        ):
          if block.id is not None:
            for relation in await uow.graph.relations.get(block.id):
              seen.update((relation.from_, relation.to_))
            seen.add(block.id)
        for block_id in seen:
          await uow.graph.blocks.delete(block_id)
        await uow.sources.delete(stored)
    await ASYNC_DB_ENGINE.dispose()


if __name__ == "__main__":
  asyncio.run(exercise())
