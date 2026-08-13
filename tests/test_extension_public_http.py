"""Public Extension callback authority stays exact and publication-scoped."""

import fastapi
from fastapi.testclient import TestClient
import pytest

from app.business.extension.runtime import PublicHTTPRoute, PublicHTTPRouteClaim
from app.middleware import JWTMiddleware


def test_exact_claimed_callback_bypasses_jwt_but_other_methods_do_not():
  app = fastapi.FastAPI()

  @app.get("/twitter/auth/callback")
  def callback():
    return {"ok": True}

  claim = PublicHTTPRouteClaim.acquire(
    "twitter",
    (PublicHTTPRoute(method="GET", path="/auth/callback"),),
    tuple(app.routes),
  )
  assert claim is not None
  app.add_middleware(JWTMiddleware)
  try:
    with TestClient(app, raise_server_exceptions=False) as client:
      assert client.get("/twitter/auth/callback?code=secret").status_code == 200
      assert client.post("/twitter/auth/callback").status_code != 200
      assert client.get("/twitter/setup").status_code != 200
  finally:
    claim.release()

  assert not PublicHTTPRouteClaim.permits("GET", "/twitter/auth/callback")


@pytest.mark.parametrize(
  "path",
  ["callback", "/callbacks/{provider}", "/callback*", "/callback?mode=x"],
)
def test_public_route_declaration_rejects_non_exact_paths(path: str):
  with pytest.raises(ValueError, match="exact relative path"):
    PublicHTTPRoute(method="GET", path=path)
