from scripts.check_migration_history import validate_worktree_manifest


def test_revision_integrity_manifest_matches_worktree():
  assert validate_worktree_manifest() == []
