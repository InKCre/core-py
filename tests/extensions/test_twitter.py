import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import parse_qs, urlparse

from extensions.twitter.api import OfficialAPI


COOKIE_CONVERTER = (
  Path(__file__).resolve().parents[2]
  / "extensions"
  / "twitter"
  / "scripts"
  / "cookie-string-to-json.py"
)


def test_get_oauth_authorize_url(monkeypatch):
  monkeypatch.setenv("API_BASE_URL", "https://preview.example")
  api = OfficialAPI(client_id="test-client", client_secret="test-secret")

  parsed = urlparse(api.get_oauth_authorize_url())
  query = parse_qs(parsed.query)

  assert parsed.scheme == "https"
  assert parsed.netloc == "x.com"
  assert query["client_id"] == ["test-client"]
  assert query["redirect_uri"] == ["https://preview.example/twitter/auth/callback"]
  assert query["code_challenge_method"] == ["plain"]


def test_cookie_converter_reads_sensitive_input_from_stdin():
  result = subprocess.run(  # noqa: S603
    [sys.executable, str(COOKIE_CONVERTER)],
    input="session=secret; preference=compact",
    check=False,
    capture_output=True,
    text=True,
  )

  assert result.returncode == 0
  assert json.loads(result.stdout) == {
    "session": "secret",
    "preference": "compact",
  }
