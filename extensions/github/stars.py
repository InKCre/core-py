"""GitHub Stars Source for collecting starred repositories."""

import asyncio
from datetime import datetime

import sqlmodel
from app.business.source import SourceBase
from app.engine import SessionLocal
from app.business.info_base.root import RootManager
from app.schemas.info_base.main import StarGraphForm
from app.schemas.info_base.block import BlockID
from app.schemas.source import SourceCollectJobModel
from extensions.github.resolver import GithubRepoResolver
from libs.obsrv.main import get_logger
from .schema import GithubRepo, GithubUser

LOGGER = get_logger().getChild(__name__)


class SourceConfig(sqlmodel.SQLModel):
  """Configuration of GitHub Stars Source."""

  github_token: str = ""
  """GitHub personal access token for API access"""
  username: str = ""
  """GitHub username to fetch starred repos for"""
  include_private: bool = False
  """Whether to include private repositories (requires appropriate token permissions)"""


class Source(SourceBase[SourceConfig], config_cls=SourceConfig):
  """GitHub Stars Source - collects starred repositories from GitHub."""

  async def collect(self, job: SourceCollectJobModel) -> None:
    """Collect starred repositories from GitHub.

    By default, collects new stars since last collection.
    If this is the first run or 'full' is specified in job config, collects all stars.
    """
    logger = LOGGER.getChild(f"collect.{job.id}")
    config = self.get_config()
    job_config = job.config or {}
    full = job_config.get("full", False)

    logger.info(
      "Starting GitHub stars collection",
      extra={"job_id": job.id, "source": job.source, "full": full},
    )

    # Import PyGithub
    try:
      from github import Github, GithubException
    except ImportError:
      logger.error("PyGithub not installed. Please install with: pip install PyGithub")
      raise ImportError("PyGithub is required for GitHub Stars source")

    # Initialize GitHub client
    try:
      gh = Github(config.github_token)
      # Verify authentication
      user = gh.get_user(config.username)
      logger.info(
        "Connected to GitHub",
        extra={"username": config.username},
      )
    except GithubException as e:
      logger.error(
        "Failed to authenticate with GitHub",
        extra={"username": config.username, "error": str(e)},
        exc_info=True,
      )
      raise e

    collected: list[StarGraphForm] = []
    try:
      # Get starred repositories
      try:
        starred = user.get_starred()
        logger.info("Fetching starred repositories")
      except GithubException as e:
        logger.error(
          "Failed to fetch starred repositories",
          extra={"error": str(e)},
          exc_info=True,
        )
        raise e

      # Get state for tracking
      state = self.get_state()
      last_starred_id = state.get("last_starred_id")
      
      # Process starred repositories
      processed_count = 0
      new_stars_count = 0
      reached_last_star = False
      
      for starred_repo in starred:
        processed_count += 1
        
        # Stop if we've reached the last collected star (not in full mode)
        if not full and last_starred_id and starred_repo.id == last_starred_id:
          logger.info(
            "Reached last collected star, stopping",
            extra={"repo_id": starred_repo.id},
          )
          reached_last_star = True
          break

        # Skip private repos if not configured to include them
        if starred_repo.private and not config.include_private:
          logger.debug(
            "Skipping private repository",
            extra={"repo": starred_repo.full_name},
          )
          continue

        logger.info(
          "Processing starred repository",
          extra={"repo": starred_repo.full_name, "count": processed_count},
        )

        # Extract repository data
        try:
          # Note: starred_at timestamp requires GitHub's Star API which is not
          # directly available in PyGithub's starred repos. We use None here.
          starred_at = None

          repo = GithubRepo(
            id=starred_repo.id,
            name=starred_repo.name,
            full_name=starred_repo.full_name,
            description=starred_repo.description,
            html_url=starred_repo.html_url,
            homepage=starred_repo.homepage,
            language=starred_repo.language,
            stargazers_count=starred_repo.stargazers_count,
            watchers_count=starred_repo.watchers_count,
            forks_count=starred_repo.forks_count,
            open_issues_count=starred_repo.open_issues_count,
            topics=starred_repo.get_topics() if starred_repo.get_topics else [],
            created_at=starred_repo.created_at,
            updated_at=starred_repo.updated_at,
            pushed_at=starred_repo.pushed_at,
            starred_at=starred_at,
          )

          # Extract owner data
          owner = GithubUser(
            login=starred_repo.owner.login,
            id=starred_repo.owner.id,
            name=starred_repo.owner.name if starred_repo.owner.name else None,
            avatar_url=starred_repo.owner.avatar_url,
            html_url=starred_repo.owner.html_url,
          )

          # Create graph
          collected.append(GithubRepoResolver.create_graph(repo, owner))
          new_stars_count += 1
          
          # Update state to track the most recent star
          if processed_count == 1:
            state["last_starred_id"] = starred_repo.id
            self.set_state(state)
            logger.debug("Updated last starred ID", extra={"repo_id": starred_repo.id})

          logger.info(
            "Collected starred repository",
            extra={
              "repo": starred_repo.full_name,
              "stars": starred_repo.stargazers_count,
            },
          )

        except Exception as e:
          logger.warning(
            "Failed to process starred repository",
            extra={"repo": starred_repo.full_name, "error": str(e)},
            exc_info=True,
          )
          continue

        # Small delay to respect rate limits
        await asyncio.sleep(0.1)

    finally:
      # PyGithub doesn't require explicit connection closing
      logger.info("GitHub collection session ended")

    logger.info(
      "Saving collected stars to database",
      extra={"count": len(collected), "new_stars": new_stars_count},
    )
    try:
      with SessionLocal() as db:
        for graph in collected:
          await RootManager.add_star_graph_to_session(graph, db)
        db.commit()
      logger.info(
        "GitHub stars collection completed",
        extra={
          "job_id": job.id,
          "stars_collected": len(collected),
          "processed": processed_count,
        },
      )
    except Exception as e:
      logger.error(
        "Failed to save stars to database",
        extra={"job_id": job.id, "error": str(e)},
        exc_info=True,
      )
      raise e

  async def _organize(self, block_id: BlockID) -> None:
    """Organize collected GitHub repository block.

    Currently no additional organization needed for GitHub repos.
    """
    pass
