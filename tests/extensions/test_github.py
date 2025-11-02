import asyncio
from unittest.mock import patch, MagicMock
from extensions.github.api import GitHubAPI
from extensions.github.source import GithubStarSource
from extensions.github.schemas import GithubRepository
import datetime

async def run_collect_and_get_results(source, nickname):
    results = []
    async for result in source._collect(nickname):
        results.append(result)
    return results

@patch('extensions.github.api.GitHubAPI.new')
def test_github_star_source_collect(mock_github_api_new):
    mock_api = MagicMock()
    mock_github_api_new.return_value = mock_api

    mock_repo = GithubRepository(
        id=1,
        name='test-repo',
        full_name='test-user/test-repo',
        private=False,
        html_url='https://github.com/test-user/test-repo',
        description='A test repository',
        fork=False,
        url='https://api.github.com/repos/test-user/test-repo',
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        pushed_at=datetime.datetime.now(),
        git_url='git://github.com/test-user/test-repo.git',
        ssh_url='git@github.com:test-user/test-repo.git',
        clone_url='https://github.com/test-user/test-repo.git',
        svn_url='https://github.com/test-user/test-repo',
        homepage='https://github.com',
        size=100,
        stargazers_count=10,
        watchers_count=10,
        language='Python',
        has_issues=True,
        has_projects=True,
        has_downloads=True,
        has_wiki=True,
        has_pages=False,
        forks_count=1,
        mirror_url=None,
        archived=False,
        disabled=False,
        open_issues_count=1,
        license=None,
        allow_forking=True,
        is_template=False,
        topics=['test', 'python'],
        visibility='public',
        forks=1,
        open_issues=1,
        watchers=10,
        default_branch='main'
    )

    async def mock_get_starred_repos(nickname):
        return [mock_repo]

    mock_api.get_starred_repos = mock_get_starred_repos

    source = GithubStarSource("test_source", "test_nickname")
    results = asyncio.run(run_collect_and_get_results(source, 'test-user'))

    assert len(results) == 1
    assert results[0].block.resolver == GithubRepository.__resolver__.__rsotype__
    assert results[0].block.content == mock_repo.model_dump_json()
