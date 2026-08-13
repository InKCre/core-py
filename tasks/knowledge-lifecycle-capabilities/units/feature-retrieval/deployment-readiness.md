# Feature Retrieval Deployment Readiness（Implemented Baseline）

## Product Pressure

This increment needs a real preview because it changes migrations、PostgreSQL extensions、runtime readiness、Peer capabilities
and the built browser journey。Sir also wants the resulting repository to support a GitHub-only self-host trial：a friend forks
`core-py`、creates provider accounts、sets a small documented input set and deploys without cloning locally。

This is a delivery-supporting slice of the active increment，not feature-retrieval product semantics。`client-web` fork delivery is
out of scope；the public client remains a consumer of an owner-selected deployment profile。

Two journeys must remain separate：

1. **Fork owner**：sets their own private JWT signing secret and receives full deployment-Peer authority；
2. **Canonical public demo participant**：may receive intentionally public full-Peer write authority only when every credential
   reachable through that authority is also deliberately public/disposable。This is a mutable scratch deployment，not a reader。

## Correct Credential Boundary

The current `JWT_SECRET` is an HS256 signing key，not a role-scoped password。A holder can choose every claim before signing；
publishing it as an “anonymous secret” therefore lets an untrusted caller mint the exact admitted
`role=authenticated, iss=inkcre-peer, aud=inkcre-api` token and become a full Peer。The intended read-only result cannot be
obtained by documenting a different role next to the same public key。

Actor/boundary analysis：

| Value | Actor capability if public | Protected asset/harm | Classification |
| --- | --- | --- | --- |
| Provider API token、Neon/API host authorization | anonymous infrastructure/provider operation | deployment takeover、data deletion、external cost | boundary violation |
| database owner/runtime-role password | anonymous direct database connection | bypass application admission、full data/config control | boundary violation |
| current HS256 Peer signing secret | mint any accepted Peer claims | read credentials、mutate/delete info-base、invoke charged work | boundary violation |
| fixed already-signed read-only token | only its immutable claims until expiry | bounded by the admitted read-only principal | potentially valid，but it is a token，not a public signing secret |
| project IDs、service names、base URLs、model IDs | discovery only | no admission by itself | public variable |

The current `anonymous` database role deliberately has no privileges and `inkcre_internal.check_jwt` admits only
`authenticated`。A real public-read journey therefore needs an explicit guest/anonymous product surface and safe projections；
it is not a README-only change。In particular，lexical `materialize_missing` may mutate graph and incur provider cost，so a public
reader cannot merely receive the existing full retrieval command。

Sir instead selected an intentionally public-writable canonical demo。That removes graph integrity/availability as protected demo
assets，but it does not automatically make unrelated provider/source credentials public：`authenticated` currently has `GRANT
ALL` over the complete `inkcre` schema，and `ai_providers.config` plus Source/Extension configs can contain raw API keys、mail
passwords and tokens。A published full-Peer key is therefore valid only for a credential-free scratch database or one containing
credentials deliberately treated as public and loss-bounded。Fork deployments remain owner-private by default。

## Deployment Secret Set

`INKCRE_DEPLOYMENT_SECRET` is withdrawn。It had been proposed only as a derivation root for database-role passwords。On first
deployment，the trusted controller generates both role passwords in memory、initializes the database and creates Render services
with complete runtime URLs。On later runs，Render's owner-authorized API returns the existing service environment values；the
controller recovers the runtime-role passwords from those URLs and converges the database before deploying。This avoids both an
extra derivation secret and needless per-deploy credential rotation。

Fork owner inputs should therefore be：

- private repository secrets：host API authorization、`NEON_API_KEY`、`JWT_SECRET`；
- public repository variables：Neon project ID、unique service names/prefixes and other non-authorizing deployment identity；
- generated first-run values：database role passwords，then retained only in Render runtime configuration and PostgreSQL role
  state；masked before any command can emit them。

AI provider keys remain deployment config entered after admission，not GitHub delivery secrets。

## Cloudflare Python Worker Fit

Cloudflare now officially supports FastAPI through its Python ASGI bridge，so route compatibility is real。A complete current
`core-py` Peer is nevertheless not a drop-in Python Worker：

- Python Workers run in Pyodide and accept pure/PyEmscripten packages；the fixed core artifact includes native/runtime-heavy
  dependencies such as `psycopg[binary]`、PyAV、lxml and Pillow，while Cloudflare's documented Hyperdrive drivers are currently
  JavaScript/TypeScript and Rust oriented。The existing SQLAlchemy + psycopg database boundary cannot consume Hyperdrive by
  changing a URL。
- current `run.py` owns process-lifetime APScheduler loops for Peer lease renewal、Cron checks、Job checks and maintenance。
  Workers execute request/scheduled invocations；post-response work is bounded，and their Scheduled handler has a 15-minute wall
  bound。A Worker host would need an event-driven runtime adapter，not merely another ASGI entry point。
- current Peer discovery uses an expiring live lease。A platform service can be logically routable while no isolate is resident，
  but the present process-owned renewal stops and the Peer disappears from routing。Scale-to-zero hosting therefore exposes a
  real missing availability/activation contract rather than a TTL tuning problem。
- the Free plan's 10 ms CPU and 3 MB Worker bundle bounds are not credible for the current full artifact。Cloudflare Containers
  can run the existing Docker image，but Containers require the $5/month Workers Paid plan and therefore do not remove the
  cost barrier that motivated this branch。

Cloudflare remains valuable as a future specialized/event-driven Peer target and as a cheap external scheduled wake-up，but
porting full `core-py` there would be a separate implementable unit with runtime-host、database-port、dependency-profile and
scale-to-zero discovery work。It must not be smuggled into feature-retrieval implementation readiness。

## Neon Data API / PostgREST Spike

Neon's managed Data API is included in its Free plan and presents a PostgREST-compatible HTTPS surface。A disposable real Neon
branch was used on 2026-08-12 to test the exact InKCre protocol rather than infer compatibility from marketing：

- exposed `inkcre` schema table read：passed；
- `create_storage_blob(bytea)` raw `application/octet-stream` request：passed；
- `read_storage_blob(uuid)` custom octet-stream response domain：passed；
- pointer-stable `storage_blobs` PATCH and DELETE：passed。

The transport can therefore replace the standalone PostgREST binary in principle。The current deployment contract cannot adopt
it unchanged：

- Data API refuses enablement when `authenticator`、`authenticated` or `anonymous` already exist，then creates and controls those
  exact roles itself；this conflicts with `db provision-roles` and InKCre's executable role authority。
- Data API validates Managed Better Auth or an external JWKS。It does not accept the current raw HS256 secret configuration，and
  the available settings do not expose the current `inkcre_internal.check_jwt` pre-request contract。
- Managed Better Auth can issue a short-lived `role=anonymous` token without login，which is a promising public-demo mechanism，
  but adopting it for owner/Peer writes would introduce a different admission model。Publishing an HS256 key through JWKS would
  simply recreate the original signing-authority leak。
- Data API cannot be enabled on an expiring Neon branch，which conflicts with current TTL preview branches unless preview cleanup
  becomes controller-owned rather than Neon expiration-owned。

Conclusion：keep standalone PostgREST for the immediate implementation/fork path。Treat Neon Data API as a proven transport and
a later deployment/auth migration，not as a protocol risk or an immediate switch。

The disposable Data API and branch were deleted after the spike；no production data or contract was changed。

## Immediate Free-Host Direction

A conventional free Docker web host is a better near-term fit than Python Workers because it can run the checked core and
PostgREST artifacts without changing their domain/runtime boundaries。Render currently supports free Docker web services and a
repository Blueprint，but free services sleep after 15 minutes and share 750 running hours per workspace。That is acceptable for
interactive use with cold starts，not for reliable scheduled collection or continuously live Peer leases。

The accepted target is a **Render + Neon self-host deployment profile with demo-grade Free-plan availability**，not a projection
of InKCre's canonical production environment：

```text
fork GitHub workflow
  -> validate exact commit and required GitHub inputs
  -> obtain the Neon owner URL only inside the controller
  -> recover or first-run generate runtime-role passwords
  -> converge database before service deployment
  -> create/converge two auto-deploy-disabled Render Free Docker web services
  -> deploy the exact commit and wait for terminal status
  -> publish non-secret deployment profile
  -> owner wakes core before capability discovery and configures the public client
```

Render's API can create Docker services with full environment、select `Dockerfile` vs `Dockerfile.postgrest` and trigger a
specific commit。Render also translates configured `SOURCE_REVISION` into the existing Docker build argument，preserving the
artifact's source evidence without another Dockerfile。The current process-import baseline is about 147 MiB RSS before live
database bootstrap against a 512 MiB Free instance；this is sufficient preflight headroom but not a substitute for the required
real Render startup/operation probe。The 0.1 CPU allocation primarily predicts cold-start/Job latency，not a semantic change。

After 15 minutes without user traffic，both services may sleep。A browser request wakes PostgREST automatically，but an expired
core Peer lease means database discovery cannot itself activate core；the documented demo journey must first open/wake core and
wait for `/readyz`，then enter client retrieval。Inventing activation-aware discovery is outside this delivery slice。

Heroku remains the exact always-on/reference delivery until a second host passes the same black-box contract。A second conventional
container Peer can later be attached to the same Neon database for multi-Peer claim/scheduling evidence；Cloudflare Python Worker
is not required to obtain that evidence。

## Acceptance Direction

- use a disposable real GitHub fork，not a renamed local checkout；
- perform onboarding only through provider and GitHub web surfaces；
- one manual workflow starts checked artifact -> database -> services -> readiness；
- the public client consumes a non-secret profile and the fork owner's locally supplied JWT secret；the canonical public demo may
  separately document its intentionally public signing key only after credential sanitation；
- no provider/source credential、database credential or host authorization appears in README、workflow summary、logs、artifacts、
  deployment profile or client build；
- missing inputs fail once with exact GitHub setting names before provider mutation；
- free-host cold start and missed scheduled work are stated limits，not silently represented as full Peer equivalence；
- canonical InKCre deployment retains its stricter exact identity/lineage checks。

## Remaining Operational Evidence

Public signing-key publication is withdrawn for this increment。Self-host deployments and the canonical public-demo environment
both keep signing authority private by default；an owner may still share a JWT privately during a live demonstration。Public
read-only admission and Cloudflare-native Peer execution remain separate follow-up design problems。

The controller、workflow、README journey and simulated Render API contract are implemented。A real Render account is not
currently available，so exact service creation、Free cold-start behavior and host-side `/readyz`/PostgREST probes remain one
explicit operational gate rather than an implementation uncertainty。
