import datetime
from typing import Optional as Opt
import sqlmodel

class GithubRepository(sqlmodel.SQLModel):
    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    description: Opt[str] = None
    fork: bool
    url: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    pushed_at: datetime.datetime
    git_url: str
    ssh_url: str
    clone_url: str
    svn_url: Opt[str] = None
    homepage: Opt[str] = None
    size: int
    stargazers_count: int
    watchers_count: int
    language: Opt[str] = None
    has_issues: bool
    has_projects: bool
    has_downloads: bool
    has_wiki: bool
    has_pages: bool
    forks_count: int
    mirror_url: Opt[str] = None
    archived: bool
    disabled: bool
    open_issues_count: int
    license: Opt[dict] = None
    allow_forking: bool
    is_template: bool
    topics: list[str]
    visibility: str
    forks: int
    open_issues: int
    watchers: int
    default_branch: str
