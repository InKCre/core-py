from scripts.container import _resolve_command


def test_resolves_provider_neutral_command() -> None:
  assert _resolve_command(["db", "migrate"]) == "db"


def test_rejects_provider_shell_wrappers_and_expressions() -> None:
  assert _resolve_command(["/bin/sh", "-c", "migrate"]) is None
  assert _resolve_command(["/bin/sh", "-c", "migrate && web"]) is None


def test_rejects_unknown_or_ambiguous_arguments() -> None:
  assert _resolve_command(["unknown"]) is None
  assert _resolve_command(["db"]) is None
  assert _resolve_command(["migrate", "web"]) is None
  assert _resolve_command(["bash", "-c", "migrate"]) is None
