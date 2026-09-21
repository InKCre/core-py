"""Bearer authentication owned by the Memos protocol surface."""

import secrets

import fastapi
import pydantic

from app.business.extension import EXTENSION_HOST
from .config import MemosConfig


async def require_memos_pat(request: fastapi.Request) -> None:
  """Require the currently configured deployment-scoped Memos PAT."""
  auth_header = request.headers.get("Authorization")
  if not auth_header or not auth_header.startswith("Bearer "):
    raise _unauthorized()

  presented = auth_header[7:]
  # Other admitted Peers can save configuration directly. Read its authority
  # here so replacing or revoking a PAT does not require restarting this Host.
  installed = await EXTENSION_HOST.get("inkcre/memos")
  try:
    configured = MemosConfig.model_validate(installed.config).personal_access_token
  except pydantic.ValidationError:
    # Validation details may echo credentials from an invalid direct DB write.
    raise _unauthorized() from None
  if configured is None or not secrets.compare_digest(presented, configured):
    raise _unauthorized()


def _unauthorized() -> fastapi.HTTPException:
  return fastapi.HTTPException(
    status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
    detail="Invalid Memos personal access token",
    headers={"WWW-Authenticate": "Bearer"},
  )
