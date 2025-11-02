import asyncio
from typing import Optional as Opt
from github import Github
from . import Extension
from .schemas import GithubRepository

class GitHubAPI:
    SINGLETON: Opt["GitHubAPI"] = None

    @classmethod
    def new(cls) -> "GitHubAPI":
        if cls.SINGLEton is not None:
            return cls.SINGLETON

        access_token = Extension.config.access_token
        if not access_token:
            raise ValueError("GitHub access token is not set.")

        cls.SINGLETON = cls(access_token)
        return cls.SINGLETON

    def __init__(self, access_token: str):
        self._client = Github(access_token)

    async def get_starred_repos(self, nickname: str) -> list[GithubRepository]:
        def sync_get_starred():
            user = self._client.get_user(nickname)
            return user.get_starred()

        starred_repos = await asyncio.to_thread(sync_get_starred)

        repos = []
        for repo in starred_repos:
            repos.append(GithubRepository(
                id=repo.id,
                name=repo.name,
                full_name=repo.full_name,
                private=repo.private,
                html_url=repo.html_url,
                description=repo.description,
                fork=repo.fork,
                url=repo.url,
                created_at=repo.created_at,
                updated_at=repo.updated_at,
                pushed_at=repo.pushed_at,
                git_url=repo.git_url,
                ssh_url=repo.ssh_url,
                clone_url=repo.clone_url,
                svn_url=repo.svn_url,
                homepage=repo.homepage,
                size=repo.size,
                stargazers_count=repo.stargazers_count,
                watchers_count=repo.watchers_count,
                language=repo.language,
                has_issues=repo.has_issues,
                has_projects=repo.has_projects,
                has_downloads=repo.has_downloads,
                has_wiki=repo.has_wiki,
                has_pages=repo.has_pages,
                forks_count=repo.forks_count,
                mirror_url=repo.mirror_url,
                archived=repo.archived,
                disabled=repo.disabled,
                open_issues_count=repo.open_issues_count,
                license=repo.license.raw_data if repo.license else None,
                allow_forking=repo.allow_forking,
                is_template=repo.is_template,
                topics=repo.topics,
                visibility=repo.visibility,
                forks=repo.forks,
                open_issues=repo.open_issues,
                watchers=repo.watchers,
                default_branch=repo.default_branch,
            ))
        return repos
