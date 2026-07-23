from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_revision_graph_has_one_base_and_one_head():
  config = Config(PROJECT_ROOT / "alembic.ini")
  scripts = ScriptDirectory.from_config(config)

  assert len(scripts.get_bases()) == 1
  assert len(scripts.get_heads()) == 1

  revisions = list(scripts.walk_revisions(base="base", head="heads"))
  assert revisions
  assert len({revision.revision for revision in revisions}) == len(revisions)
