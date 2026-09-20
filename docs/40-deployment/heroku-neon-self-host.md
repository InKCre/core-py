# Self-Hosting On Heroku And Neon

## Purpose And Boundary

The checked-in `Deploy self-hosted InKCre to Heroku` workflow gives a repository owner a
browser-only path from a public `core-py` fork to two Heroku Container Stack apps backed by
the owner's Neon default branch:

- `HEROKU_APP_PREFIX-core` runs the complete `core-py` Peer;
- `HEROKU_APP_PREFIX-postgrest` exposes the executable peer database contract.

The workflow builds the selected commit as `linux/amd64` images, creates missing apps in the
Heroku US region, and runs one Eco web dyno for each app. Heroku charges and Eco sleep behavior
remain the deployment owner's responsibility. This deployment is independent from InKCre's
canonical production environment.

The `JWT_SECRET` grants full admitted-Peer authority. Keep it private. The two database-role
passwords are also persistent deployment credentials: reruns must use the same values unless the
database roles and both app configurations are rotated together.

## Browser-Only Onboarding

1. Fork this repository and enable GitHub Actions for the fork.
2. Create a Neon project and an API key that can access it. Its default branch must retain the
   standard `neondb` database and `neondb_owner` role. Copy the project ID.
3. Create a Heroku account with billing enabled and an API key.
4. In **Settings → Secrets and variables → Actions**, add these repository settings.

| Kind | Exact name | Meaning |
| --- | --- | --- |
| Secret | `NEON_API_KEY` | Can resolve and mutate `NEON_PROJECT_ID` |
| Secret | `HEROKU_API_KEY` | Can create, configure, release, and scale the two apps |
| Secret | `JWT_SECRET` | At least 32 bytes; owner-only Peer signing authority |
| Secret | `CORE_DATABASE_PASSWORD` | At least 32 bytes; persistent `inkcre_core` role password |
| Secret | `POSTGREST_DATABASE_PASSWORD` | At least 32 bytes; persistent `authenticator` role password |
| Variable | `NEON_PROJECT_ID` | Target Neon project identity |
| Variable | `HEROKU_APP_PREFIX` | Unique 3–18 character lowercase app prefix |

Use independently generated values for all three credential secrets. Do not reuse a provider API
key or another password as the JWT secret.

5. Open **Actions → Deploy self-hosted InKCre to Heroku → Run workflow** and select the branch
   to deploy.
6. Read the workflow summary for the public app URLs, Peer identity, exact commit, and Heroku
   releases. Keep using the repository's private `JWT_SECRET` when an admitted client asks for
   the signing key.

## Convergence And Safety

The workflow validates all settings before provider mutation, builds the exact selected commit,
resolves the Neon default branch owner coordinates, creates missing Heroku apps, and refuses an
existing app unless its deployment profile matches the same Neon project. It then initializes the
database contract, stores only role-specific URLs in Heroku config, releases both images, converges
the Core Peer's public address, and verifies Core readiness plus the authenticated PostgREST
read/write/deny contract.

The Neon owner URL exists only in the GitHub Actions job. It is never placed in either Heroku app.
Workflow output contains no JWT, database password, or database URL. Rerunning the workflow is a
convergence operation and does not infer credential rotation or cleanup authority.

Heroku's [Container Registry documentation](https://devcenter.heroku.com/articles/container-registry-and-runtime)
defines the image release and `linux/amd64` requirements. Its
[config-var documentation](https://devcenter.heroku.com/articles/config-vars) describes the
persistent runtime configuration used by this profile.

## Cleanup

Delete the two exact Heroku apps when the deployment is no longer wanted. Delete the Neon project
only if it is dedicated to this deployment and its data is disposable. Both actions are explicitly
owner-controlled and intentionally absent from the deployment workflow.
