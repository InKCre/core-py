"""Session-bound embedding profiles and derived retrieval records."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.ai import EmbeddingProfileID, EmbeddingProfileModel


class SemanticRetrievalRepository:
  def __init__(self, session: AsyncSession) -> None:
    self._session = session

  async def get_profile(
    self, profile_id: EmbeddingProfileID
  ) -> EmbeddingProfileModel | None:
    return await self._session.get(EmbeddingProfileModel, profile_id)
