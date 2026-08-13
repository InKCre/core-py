"""Composition-root proof for built-in Peer capabilities and lease refresh."""

from unittest.mock import MagicMock

import run

from app.business.extension import EXTENSION_MANAGEMENT_CAPABILITY
from app.business.info_base.storage import StorageManager
from app.business.lexical_retrieval import LEXICAL_RETRIEVAL_CAPABILITY
from app.business.organization import RUMINATION_CAPABILITY
from app.business.semantic_retrieval import SEMANTIC_RETRIEVAL_CAPABILITY


def test_bootstrap_publishes_all_fixed_inbounds_before_scheduling(monkeypatch):
  peer = MagicMock()
  ai = MagicMock()
  jobs = MagicMock()
  crons = MagicMock()
  scheduler = MagicMock()
  scheduler.running = False
  monkeypatch.setattr(run, "PeerManager", peer)
  monkeypatch.setattr(run, "AIManager", ai)
  monkeypatch.setattr(run, "JobManager", jobs)
  monkeypatch.setattr(run, "CronManager", crons)
  monkeypatch.setattr(run, "scheduler", scheduler)
  monkeypatch.setattr(run, "SKIP_EXTENSIONS_SYNC", True)
  monkeypatch.setattr(StorageManager, "setup_builtin_storages", MagicMock())

  run.bootstrap_runtime(MagicMock())

  capabilities = {call.args[0].capability for call in peer.register_inbound.call_args_list}
  assert capabilities == {
    SEMANTIC_RETRIEVAL_CAPABILITY,
    RUMINATION_CAPABILITY,
    EXTENSION_MANAGEMENT_CAPABILITY,
    LEXICAL_RETRIEVAL_CAPABILITY,
  }
  peer.refresh_self.assert_called_once_with(run.settings.peer_lease_ttl_seconds)
  refresh_job = next(
    call
    for call in scheduler.add_job.call_args_list
    if call.kwargs["id"] == "peer.refresh_self"
  )
  assert refresh_job.args[0] is peer.refresh_self
  assert refresh_job.kwargs["args"] == [run.settings.peer_lease_ttl_seconds]
  assert refresh_job.kwargs["seconds"] == run.settings.peer_lease_renew_interval_seconds
  jobs.sync_job_types.assert_called_once_with()
  scheduled = {call.kwargs["id"]: call for call in scheduler.add_job.call_args_list}
  assert scheduled["jobs.check"].args[0] is jobs.check
  assert scheduled["crons.check"].args[0] is crons.check
  assert "semantic_retrieval.maintain_default" not in scheduled
