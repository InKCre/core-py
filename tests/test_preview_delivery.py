"""The pull-request preview exposes both browser-facing Peer transports."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_preview_builds_releases_probes_and_cleans_postgrest():
  workflow = (PROJECT_ROOT / ".github/workflows/preview-deploy.yml").read_text()
  delivery = (PROJECT_ROOT / ".github/actions/preview-delivery/action.yml").read_text()

  assert "Dockerfile.postgrest" in workflow
  assert "inkcre-preview-postgrest:$HEAD_SHA" in workflow
  assert '"inkcre-postgrest-pr-$PR_NUMBER"' in workflow
  assert 'heroku apps:destroy --app "$app_name"' in workflow

  assert 'postgrest_app_name="inkcre-postgrest-pr-$PR_NUMBER"' in delivery
  assert "TARGET_DATABASE_ROLE=authenticator" in delivery
  assert "--scheme postgresql" in delivery
  assert "PGRST_DB_PRE_REQUEST=inkcre_internal.check_jwt" in delivery
  assert "PGRST_JWT_AUD=inkcre-api" in delivery
  assert "jwt_secret: ${{ secrets.JWT_SECRET }}" in workflow
  assert "JWT_SECRET: ${{ inputs.jwt_secret }}" in delivery
  assert "PREVIEW_JWT_SEED" not in workflow
  assert "derive_preview_jwt_secret.py" not in delivery
  assert "registry.heroku.com/$POSTGREST_APP_NAME/web" in delivery
  assert 'heroku ps:scale web=1:eco --app "$POSTGREST_APP_NAME"' in delivery
  assert 'Path("/app/scripts/configure_peer_runtime.py").is_file()' in delivery
  assert "Peer advertisement: skipped for a pre-Peer Client image" in delivery
  assert "scripts/verify_postgrest_contract.py" in delivery
  assert '--base-url "$POSTGREST_URL"' in delivery


def test_preview_keeps_database_principals_separated():
  delivery = (PROJECT_ROOT / ".github/actions/preview-delivery/action.yml").read_text()

  core_config = delivery[
    delivery.index("configure_app() {") : delivery.index("configure_postgrest() {")
  ]
  postgrest_config = delivery[
    delivery.index("configure_postgrest() {") : delivery.index(
      'test -n "$JWT_SECRET"',
      delivery.index("configure_postgrest() {"),
    )
  ]

  assert "DATABASE_URL=$DATABASE_URL" in core_config
  assert "PGRST_DB_URI" not in core_config
  assert "PGRST_DB_URI=$POSTGREST_DATABASE_URL" in postgrest_config
  assert "DATABASE_URL=" not in postgrest_config
  assert "MIGRATION_DATABASE_URL" not in postgrest_config


def test_preview_uses_repository_jwt_authority_directly():
  workflow = (PROJECT_ROOT / ".github/workflows/preview-deploy.yml").read_text()
  delivery = (PROJECT_ROOT / ".github/actions/preview-delivery/action.yml").read_text()

  assert 'JWT_SECRET="$(heroku config:get JWT_SECRET' not in delivery
  assert "openssl rand -hex" not in delivery
  assert "preview_jwt_seed" not in delivery
  assert "jwt_secret: ${{ secrets.JWT_SECRET }}" in workflow
  assert "JWT_SECRET: ${{ inputs.jwt_secret }}" in delivery
