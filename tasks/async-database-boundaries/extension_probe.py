"""Task-scoped Extension Store/Host acceptance against the isolated task database."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import uuid

import fastapi
import httpx

from app.business.extension import ExtensionBase, ExtensionHost
from app.business.extension.state import ExtensionStateService
from app.business.extension.runtime import ExtensionRuntimeClaim
from app.business.peer import PeerManager
from app.engine import ASYNC_DB_ENGINE, SessionLocal
from app.schemas.peer import PeerModel


async def exercise():
  name = "inkcre/async-probe-" + uuid.uuid4().hex[:12]
  extension_id = name.split("/")[1]
  peer_id = uuid.uuid4()
  with SessionLocal() as session:
    session.add(PeerModel(id=peer_id, name="async-host-probe"))
    session.commit()

  class Probe(ExtensionBase, ext_id=extension_id):
    @classmethod
    def api_dependencies(cls):
      return []

    @classmethod
    def _register_apis(cls, router):
      @router.get("/alive")
      def alive():
        return {"alive": True}

  class Modules:
    def __init__(self, acquired):
      pass

    def load(self, base):
      return Probe

    def assert_origins(self):
      pass

  store = ExtensionStateService()
  host = ExtensionHost(store=store)
  app = fastapi.FastAPI()
  association = SimpleNamespace(entry_point=SimpleNamespace(name=extension_id))

  async def acquire(state):
    return association, object()

  try:
    await store.install(name, "1.0.0", "Probe")
    await store.mutate_state(name, lambda _: {"count": 0})
    await asyncio.gather(
      *(store.mutate_state(name, lambda s: {"count": s["count"] + 1}) for _ in range(8))
    )
    assert await store.read_state(name) == {"count": 8}

    def rejected(config, state):
      state["count"] = 999
      raise ValueError("abort atomic change")

    try:
      await store.mutate_config_and_state(name, rejected)
    except ValueError:
      pass
    else:
      raise AssertionError("mutation did not abort")
    assert await store.read_state(name) == {"count": 8}

    with (
      patch("app.business.extension.main.DistributionModules", Modules),
      patch.object(host, "_acquire", acquire),
      patch.object(PeerManager, "get_current_peer_ref", return_value=peer_id),
    ):
      async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
      ) as client:
        enabled = await host.enable(name, app=app)
        assert peer_id in enabled.enabled
        assert (await client.get(f"/{extension_id}/alive")).status_code == 200
        with patch.object(
          store, "set_peer_enabled", AsyncMock(side_effect=RuntimeError("RPC failed"))
        ):
          try:
            await host.disable(name)
          except RuntimeError as error:
            assert str(error) == "RPC failed"
          else:
            raise AssertionError("disable swallowed persistence failure")
        assert name in host.running
        assert (await client.get(f"/{extension_id}/alive")).status_code == 200
        assert peer_id in (await store.get(name)).enabled
        disabled = await host.disable(name)
        assert peer_id not in disabled.enabled
        assert (await client.get(f"/{extension_id}/alive")).status_code == 404

        entered = asyncio.Event()

        async def blocked_schema(*args):
          entered.set()
          await asyncio.Event().wait()

        with patch.object(store, "update_config_schema", blocked_schema):
          starting = asyncio.create_task(host.enable(name, app=app))
          try:
            async with asyncio.timeout(5):
              await entered.wait()
          finally:
            starting.cancel()
          try:
            await starting
          except asyncio.CancelledError:
            pass
          else:
            raise AssertionError("cancellation swallowed")
        assert name not in host.running
        assert (await client.get(f"/{extension_id}/alive")).status_code == 404
        claim = ExtensionRuntimeClaim.acquire(extension_id)
        claim.release()
        assert peer_id not in (await store.get(name)).enabled
        await host.enable(name, app=app)
        with (
          patch.object(Probe, "peer_inbounds", return_value=(object(),)),
          patch.object(
            PeerManager,
            "refresh_self",
            AsyncMock(side_effect=RuntimeError("refresh failed")),
          ),
        ):
          try:
            await host.disable(name)
          except RuntimeError as error:
            assert str(error) == "refresh failed"
          else:
            raise AssertionError("failed advertisement was hidden")
        assert name not in host.running
        assert peer_id not in (await store.get(name)).enabled
        assert (await client.get(f"/{extension_id}/alive")).status_code == 404

    print(
      "Extension async locking, rollback, RPC, startup cancellation and restart: passed"
    )
  finally:
    await host.close_running()
    state = await store.get(name)
    if state is not None:
      if peer_id in state.enabled:
        await store.set_peer_enabled(name, peer_id, False)
      await store.uninstall(name)
    with SessionLocal() as session:
      peer = session.get(PeerModel, peer_id)
      if peer is not None:
        session.delete(peer)
        session.commit()
    await ASYNC_DB_ENGINE.dispose()


if __name__ == "__main__":
  asyncio.run(exercise())
