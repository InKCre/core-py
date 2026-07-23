from urllib.parse import parse_qs, urlparse

from extensions.twitter.api import OfficialAPI


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
