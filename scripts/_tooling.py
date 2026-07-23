"""Shared process helpers for repository tooling."""

from collections.abc import Sequence
from pathlib import Path
import os
import shutil
import subprocess


def executable_candidates(command: str):
  """Yield PATH candidates portably, including entries after broken shims."""
  seen: set[str] = set()
  for directory in os.environ.get("PATH", "").split(os.pathsep):
    candidate = shutil.which(command, path=directory or os.curdir)
    if candidate is not None and candidate not in seen:
      seen.add(candidate)
      yield candidate


def run_command(
  command: str,
  arguments: Sequence[str],
  cwd: Path,
) -> subprocess.CompletedProcess[str] | None:
  """Run the first launchable PATH candidate and skip stale executable shims."""
  for executable in executable_candidates(command):
    try:
      return subprocess.run(  # noqa: S603
        [executable, *arguments],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
      )
    except OSError:
      continue
  return None


def run_pdm(arguments: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str] | None:
  """Run the first working PDM executable without leaking subprocess output."""
  return run_command("pdm", arguments, cwd)
