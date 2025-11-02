from typing import AsyncGenerator
from app.business.source import SourceBase
from app.schemas.root import StarGraphForm
from app.schemas.block import BlockModel
from .api import GitHubAPI
from .schemas import GithubRepository

class GithubStarSource(SourceBase):
    source_id = "star"

    async def _collect(self, nickname: str) -> AsyncGenerator[StarGraphForm, None]:
        api = GitHubAPI.new()
        starred_repos = await api.get_starred_repos(nickname)

        for repo in starred_repos:
            yield StarGraphForm(
                block=BlockModel(
                    resolver=GithubRepository.__resolver__.__rsotype__,
                    content=repo.model_dump_json()
                )
            )
