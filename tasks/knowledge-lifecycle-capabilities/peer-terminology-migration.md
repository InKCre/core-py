# Peer Terminology Migration Evidence

> D-109 的 cross-unit working ledger。它记录迁移地址与边界，不是 durable protocol owner，也不授权实现。

## Selected Semantic Diff

```text
technical runtime-node domain: Client -> Peer
user-facing product/app language: Client remains Client
```

这是 technical domain hard rename，不是给旧词增加“其实是 peer”的注释，也不是全仓字符串替换。

## Proven Migration Surfaces

### Shared database/runtime protocol

- `clients` relation and its row/schema names；the structural migration renames it to `peers`，but D-195's clean shared-
  database rebuild removes any retained-row compatibility requirement。
- development baseline client constants and catalog/readiness SQL。
- deployment profile `client` section and `core.client_id`。
- peer JWT's current exact issuer value `inkcre-client`。
- extension enablement references whose values are current client IDs。
- generated database/runtime contracts and migrations consumed by equal peers。

### core-py

- `ClientID`、`ClientModel`、`ClientManager` and `app.schemas.client` / `app.business.client`。
- `client_id`、`client_name`、`client_base_url` settings and corresponding `CLIENT_*` environment names when they denote
  the local InKCre runtime node。
- bootstrap registration、tests and local durable docs that use the domain concept。

### client-web and other peer implementations

- `packages/core/src/client/client.ts` currently mixes a database Client record with peer-to-peer behavior；the domain
  record/API should become Peer/PeerRef and a peer module。
- active-record mappings、extension enablement APIs、generated DB types、runtime profile fields、JWT contract、tests and
  developer/admin UI labels that explicitly expose technical runtime topology。Ordinary user-facing UI remains Client。
- Hub Product TDD and technical glossary currently preserve the Client domain and must be corrected through the Hub
  workflow after implementation evidence。PRD/user-facing product language can retain Client；only claims that explicitly
  explain peer topology need the technical term。
  `docs/_shared/**` is not edited from the Spoke working context。

## Excluded from Mechanical Rename

- FastAPI/HTTP/TestClient variables and third-party HTTP library client classes。
- OAuth/Twitter/GitHub native `client_id`、`client_secret` or SDK client vocabulary。
- Memos/MoeMemos and other external apps when they genuinely act as clients of an extension backend。
- marketing、landing、non-technical/user-facing documents and first-party product/repository identities such as
  `client-web`、`client-ios` and `client-webext`。
- historical migration filenames/revision history；a new migration expresses the protocol rename。

## Closed Product/Repository Boundary

First-party repository/product slugs remain user-facing Client identities and are not renamed。Within those repositories，
technical domain symbols、database contracts and runtime topology still use Peer。`rokid-studio-client` likewise receives
no rename merely from this decision；if its internal architecture participates as an InKCre Peer，only that technical
surface enters the semantic migration。

## Approved Implementation Shape（semantic-retrieval unit）

1. inventory technical Peer surfaces across participating repositories/deployments without renaming product/repository
   identities；
2. update Hub technical contracts and each peer implementation as coordinated owner-specific changes；
3. rename persisted protocol state in place and hard-cut technical symbols/env/wire names without indefinite
   compatibility aliases；
4. regenerate projections and verify cross-peer bootstrap、authentication、extension enablement and shared DB access；
5. keep user-facing and genuine external-client vocabulary unchanged and prove this with targeted search/static checks。
