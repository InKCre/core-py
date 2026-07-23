"""InKCre GitHub Extension Schemas."""

__all__ = [
  "GithubUser",
  "GithubRepo",
]

from datetime import datetime
from typing import Optional as Opt
import sqlmodel
import pydantic


class GithubUser(sqlmodel.SQLModel):
  """GitHub user."""

  login: str
  """GitHub username (login)"""
  id: int
  """GitHub user ID"""
  name: Opt[str] = None
  """Display name of the user"""
  avatar_url: Opt[str] = None
  """URL to user's avatar"""
  html_url: str
  """URL to user's GitHub profile"""

  @pydantic.field_validator("login")
  @classmethod
  def normalize_login(cls, v: str) -> str:
    """Normalize GitHub login to lowercase."""
    return v.lower().strip()


class GithubRepo(sqlmodel.SQLModel):
  """GitHub repository block content model."""

  id: int
  """Repository ID from GitHub"""
  name: str
  """Repository name (e.g., 'core-py')"""
  full_name: str
  """Full repository name (e.g., 'InKCre/core-py')"""
  description: Opt[str] = None
  """Repository description"""
  html_url: str
  """URL to repository on GitHub"""
  homepage: Opt[str] = None
  """Repository homepage URL"""
  language: Opt[str] = None
  """Primary programming language"""
  stargazers_count: int = 0
  """Number of stars"""
  watchers_count: int = 0
  """Number of watchers"""
  forks_count: int = 0
  """Number of forks"""
  open_issues_count: int = 0
  """Number of open issues"""
  topics: list[str] = []
  """Repository topics/tags"""
  created_at: datetime
  """Repository creation time"""
  updated_at: datetime
  """Repository last update time"""
  pushed_at: Opt[datetime] = None
  """Last push time"""
  starred_at: Opt[datetime] = None
  """When the user starred this repo"""
