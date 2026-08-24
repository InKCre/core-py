# Memos Backend MVP — Authentication Contract

> Confirmed task-state contract（D-039）。This is not durable truth or implementation authorization。

## Contract Summary

- The backend accepts exactly one deployment-scoped Memos-compatible Personal Access Token (PAT)。It
  authenticates access to this InKCre deployment，not a terminal user、tenant、session or `ClientModel`。
- The deployment owner supplies the token through the existing peer-authenticated
  `PUT /extensions/memos/config` surface，then enters the same token in MoeMemos。The MVP does not add a
  Memos administration endpoint or a one-time secret issuance response。
- The token is long-lived until replacement or revocation。Replacement has no overlap window；the old
  token becomes invalid when the update succeeds。
- The PAT is ordinary Memos extension configuration。Its raw value is persisted in
  `extensions.config`、loaded into runtime config and returned by the existing peer-authenticated config
  surface。The current deployment treats database/config peers as trusted operators；the MVP does not
  create a Memos-only secret boundary that the rest of the config system does not have。
- Only `GET /memos/api/v1/instance/profile` is public。`GET /memos/api/v1/status` intentionally remains
  unimplemented (`404`) so MoeMemos falls through from its v0 probe to v1 detection。Every other
  implemented Memos route，including `/memos/file/*`，requires the Memos PAT。

## Evidence Behind the Boundary

- MoeMemos 2.0.4 calls v0 `status` without a token and treats any successful version-bearing response as
  a v0 server；only after failure does it call v1 `instance/profile`。See the tagged
  [`detectAccountCaseAndVersion`](https://github.com/mudkipme/MoeMemosAndroid/blob/2.0.4/app/src/main/java/me/mudkip/moememos/data/service/AccountService.kt#L496-L511)。
- MoeMemos then validates the supplied Bearer token through tagged
  [`GET api/v1/auth/me`](https://github.com/mudkipme/MoeMemosAndroid/blob/2.0.4/app/src/main/java/me/mudkip/moememos/data/api/MemosV1Api.kt#L17-L20)。
- Memos 0.29.1 exposes `GetInstanceProfile` publicly and treats PATs as long-lived tokens。Its tagged
  implementation generates `memos_pat_` plus 32 cryptographically random alphanumeric characters and
  stores SHA-256，see
  [`token.go`](https://github.com/usememos/memos/blob/v0.29.1/server/auth/token.go#L189-L203) and
  [`acl_config.go`](https://github.com/usememos/memos/blob/v0.29.1/server/router/api/v1/acl_config.go#L11-L47)。
- Current core-py persists extension config as JSONB and returns it as part of `ExtensionModel`。Existing
  extension/source configs already keep recoverable Twitter password/TOTP、Telegram bot token、IMAP
  password and GitHub token values。Hashing only the Memos PAT would reduce one credential's exposure while
  leaving the same database/config trust boundary intact，and would add a second update/read lifecycle。
- The external update currently saves an unvalidated raw dict before applying runtime config。D-039
  therefore requires a generic validate-before-persist update mechanism，not Memos-specific transform or
  projection hooks。

Memos upstream evidence informs the compatible external shape；it does not require copying upstream's
multi-user PAT storage boundary、list、expiry、last-used tracking or token-management endpoints。

## Route Authentication Matrix

| Route class | Credential | Result |
| --- | --- | --- |
| `GET /memos/api/v1/instance/profile` while extension is enabled | none、peer JWT、Memos PAT or malformed header | `200` with at least `{"version":"0.29.1"}`；authentication is not evaluated |
| `GET /memos/api/v1/status` | any | `404`；do not return a version-bearing v0 status object |
| Implemented `/memos/api/v1/*` except profile | valid active Memos PAT | route handler runs |
| Implemented protected Memos route | missing、malformed、old、revoked or unknown token；peer JWT | `401` with `WWW-Authenticate: Bearer` |
| `/memos/file/*` | same as protected protocol routes | valid PAT required；attachment knowledge does not grant access |
| Core/default-extension protected route | Memos PAT | `401`；only peer JWT is accepted |
| Any Memos route while extension is disabled | any | `404` because D-038 removes the route set |

Upstream Memos makes additional read routes public for its multi-user visibility model。The backend MVP
does not inherit that larger public surface：MoeMemos sends its token after login，and InKCre has no public
memo-browsing product requirement。

## Configuration Update and Persistence

### Config update

The existing peer-authenticated extension config update accepts one ordinary config field：

```json
{
  "personal_access_token": "memos_pat_0123456789abcdefghijklmnopqrstuv"
}
```

- The exact accepted format is `^memos_pat_[0-9A-Za-z]{32}$`，matching the selected Memos generation。
- Field present with a valid string means establish or replace。
- Field present as `null` means revoke。
- Core shallow-merges the update with the current config before validation；field absence therefore
  preserves the current token and lets other fields change without re-sending it。
- Invalid type/format returns `422` and leaves persisted and running state unchanged。

The deployment owner is responsible for generating the 32-character suffix with a cryptographically
secure generator。Server-side issuance is excluded from the MVP because it would add a parallel token
management API without improving MoeMemos compatibility。

### Persisted and read authority

`extensions.config`、runtime config and peer-authenticated config reads share one shape：

```json
{
  "personal_access_token": "memos_pat_0123456789abcdefghijklmnopqrstuv"
}
```

Authentication compares the presented Bearer value with the configured PAT using constant-time string
comparison。A separate verifier、credential table、password KDF、token ID、expiry、description、last-used
timestamp and history are not justified for one deployment token。

This explicitly accepts that a database reader or peer authorized to read extension configuration can
recover the Memos PAT。That is the current config trust boundary，not an accidental omission。If InKCre
later creates a generic encrypted/redacted secret-config facility，Memos should adopt it together with
other credential-bearing configs rather than inventing a private exception now。The current client-web
config path mismatch still needs correction if this GUI is included，but it can otherwise edit the same
config shape。

## State Transitions and Atomicity

| Current state | Command | Successful next state | Observable consequence |
| --- | --- | --- | --- |
| unconfigured | valid token | configured(new) | new token works immediately if running |
| configured(old) | valid different token | configured(new) | old fails immediately；new works；no overlap |
| configured | `null` | unconfigured | all protected Memos routes return `401`；public profile remains available |
| unconfigured | `null` | unconfigured | idempotent success |
| either | field absent | unchanged | generic config merge has no credential effect |
| either | invalid input or persistence failure | unchanged | error；no partially applied runtime state |

The update order is merge complete next config → validate → persist → assign the already-validated runtime
config。There is no `await` or fallible external work between persistence and assignment。Configuration is
allowed while the extension is disabled；the PAT is loaded on the next enable。Enabling without a
configured PAT is also allowed but fails closed：only the public profile can be used until configuration。

## Minimal Core Change

No Memos-specific config hooks are required。Core needs one generic config-update operation：merge the
patch into current state、validate through the target's existing `config_cls`、persist the validated shape，
then update the live object。Extension is the first required target；the same operation should later be
reused by source and other configurable runtime owners once their addressing and lifecycle are designed。

```python
class MemosConfig(SQLModel):
  personal_access_token: str | None = Field(
    default=None,
    pattern=r"^memos_pat_[0-9A-Za-z]{32}$",
  )


# ExtensionManager config update, before any database write.
candidate = {**extension.config, **request_body}
normalized = extension_class.__configcls__(**candidate)
persist(normalized.model_dump(mode="json"))
if extension_is_running:
  extension_class.config = normalized
```

Core owns update ordering but not Memos semantics。The Memos config schema owns the PAT's nullable type and
format；the Memos auth dependency owns comparison。Source/storage reuse must not be claimed merely because
they also expose `config_cls`：their durable owner、instance address and live-reconfiguration consequences
must first be traced。

## Explicit Exclusions

- `/memos/admin/*` and Memos PAT list/create/delete endpoints；
- login/password、short-lived access JWT、refresh cookie or session；
- multiple simultaneous tokens、rotation overlap or grace period；
- time expiry、automatic rotation、last-used/audit history or rate limiting；
- reusing peer JWT as a Memos credential or creating a core User；
- generic extension secret vault/table、auth-specific config hooks or config projection framework in this
  MVP。

## Acceptance Obligations

- U-01：public v1 detection followed by PAT-authenticated `auth/me` and GENERAL settings；
- U-06：raw attachment download uses the same PAT dependency；
- U-11：public、peer and Memos auth matrix，including cross-token rejection；
- config fixture：establish、read-back、hot replace、revoke、omitted-field preservation、invalid input
  rollback、validation-before-persistence and persisted/runtime consistency；
- lifecycle fixture：configured while disabled，enable without config fails closed，disable returns `404`。

O-018 is closed by D-039。Technical/Acceptance are now complete；implementation still waits for the Impact
Handshake and Sir's explicit start。
