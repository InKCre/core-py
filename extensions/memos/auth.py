"""Bearer authentication owned by the Memos protocol surface."""

import secrets

import fastapi


def require_memos_pat(request: fastapi.Request) -> None:
  """Require the currently configured deployment-scoped Memos PAT."""
  from . import Extension

  auth_header = request.headers.get("Authorization")
  if not auth_header or not auth_header.startswith("Bearer "):
    raise _unauthorized()

  presented = auth_header[7:]
  configured = Extension.config.personal_access_token
  if configured is None or not secrets.compare_digest(presented, configured):
    raise _unauthorized()


def _unauthorized() -> fastapi.HTTPException:
  return fastapi.HTTPException(
    status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
    detail="Invalid Memos personal access token",
    headers={"WWW-Authenticate": "Bearer"},
  )
