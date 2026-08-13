"""Static guards for repeat delivery of an already-running Heroku image."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_preview_treats_same_images_as_success():
  delivery = (PROJECT_ROOT / ".github/actions/preview-delivery/action.yml").read_text(
    encoding="utf-8"
  )

  assert 'if [ "$guard_release" != "$before_guard_release" ]; then' in delivery
  assert 'if [ "$web_release" != "$before_web_release" ]; then' in delivery
  assert 'if [ "$postgrest_release" != "$before_postgrest_release" ]; then' in delivery
  assert 'test "$guard_release" != "$before_guard_release"' not in delivery
  assert 'test "$web_release" != "$before_web_release"' not in delivery
  assert 'test "$postgrest_release" != "$before_postgrest_release"' not in delivery


def test_production_reuses_last_deployed_release_when_heroku_returns_noop():
  delivery = (PROJECT_ROOT / ".github/actions/production-delivery/action.yml").read_text(
    encoding="utf-8"
  )

  assert 'web_release="$previous_release"' in delivery
  assert 'postgrest_release="$previous_postgrest_release"' in delivery
  assert 'test "$guard_release" != "$before_guard_release"' not in delivery
  assert 'test "$web_release" != "$before_web_release"' not in delivery
  assert 'test "$postgrest_release" != "$before_postgrest_release"' not in delivery
