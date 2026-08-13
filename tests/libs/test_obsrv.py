import importlib
import logging
from unittest.mock import patch

from libs.obsrv.main import setup_obsrv


def test_none_backend_keeps_console_logging_without_warning(
  monkeypatch,
) -> None:
  settings_module = importlib.import_module("app.settings")
  monkeypatch.setattr(settings_module.settings.obsrv, "logging_backend", "none")

  with patch.object(logging.Logger, "warning") as warning:
    logger = setup_obsrv()

  warning.assert_not_called()
  assert len(logger.handlers) == 1
