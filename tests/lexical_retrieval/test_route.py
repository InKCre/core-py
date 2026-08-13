"""Fixed lexical retrieval inbound contract."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.business.lexical_retrieval import LexicalRetrievalManager
from app.routes.lexical_retrieval import ROUTER
from app.schemas.lexical_retrieval import LexicalRetrievalResult


def test_route_calls_non_delegating_local_path(monkeypatch):
  captured = []

  def retrieve_local(_cls, query, limit):
    captured.append((query, limit))
    return LexicalRetrievalResult(matches=())

  monkeypatch.setattr(
    LexicalRetrievalManager,
    "retrieve_local",
    classmethod(retrieve_local),
  )
  app = FastAPI()
  app.include_router(ROUTER)

  response = TestClient(app).post(
    "/lexical-retrieval",
    json={"query": "链路故障", "limit": 4},
  )

  assert response.status_code == 200
  assert response.json() == {"matches": []}
  assert captured == [("链路故障", 4)]
