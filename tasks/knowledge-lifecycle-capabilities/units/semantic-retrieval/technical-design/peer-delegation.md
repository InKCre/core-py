# Peer Capability Delegation

> [Technical design index](index.md)

## T-016 Heterogeneous Peer Capability Delegation（approved through D-136）

### Rejected database-business implementation

- PostgREST/pgvector can technically execute the proposed mixed comparison，but feasibility does not assign ownership。
  Storage blob RPCs are narrow atomic helpers over opaque bytes；a semantic retrieval RPC would instead own Profile、
  freshness、ranking and result business behavior in SQL，making PostgreSQL a hidden SemanticRetrievalManager。
- withdraw the entire shared retrieval RPC topology。Embedding record tables remain shared state，but an application
  capability provider reads/compares them through maintainable peer-local implementation code。

### Product model

```text
shared database authority: Peers are equal
runtime execution ability: Peers are heterogeneous

asynchronous delegated work
  caller writes domain job -> capable worker Peer claims/executes -> durable outcome

synchronous delegated capability
  caller Peer -> selected provider Peer HTTP request -> typed response
```

- collect-job persistence is collection-domain behavior，not a generic delegation queue。Semantic retrieval's natural
  work model is request-response and receives no job table。
- C/S is a role on one interaction edge。A Peer may provide semantic retrieval while consuming another capability；this
  does not turn the whole deployment into one fixed client/server hierarchy。

### Existing code pressure

- the current legacy Client/ future Peer row already owns a nullable `rest_api_url`，while some Peers such as browsers are
  intentionally unreachable。It has labels but no exact capability declaration。
- client-web's current Client active record already performs peer-JWT HTTP requests to a selected Peer，but it conflates a
  hard-coded Core endpoint with generic peer communication and cannot discover/route by capability。
- source collect jobs already prove shared-job claim semantics；they do not solve synchronous provider discovery or typed
  request-response invocation。

### Approved manageability boundary

Introduce one exact versioned **Peer Capability** contract，for example `core.semantic_retrieval.v1`，and keep its registry
inside the total PeerManager rather than creating a separate CapabilityRegistry/Manager:

```text
Peer
  id / name / labels / config
  capabilities: exact capability + inbound descriptor snapshot
  lease_expires_at

PeerManager
  local exact-capability-ID registry
  self-advertisement
  provider discovery / routing
  authenticated connection/transport to a selected Peer

SemanticRetrievalCapability
  exact capability ID
  domain-owned typed request/response schemas and inbound codec
  domain-owned request-response behavior

provider Peer
  typed POST /semantic-retrieval
  -> local SemanticRetrievalManager
```

- PeerManager does not interpret protocol parameters、request/response schema or interaction shape。Its common boundary
  stops at exact-ID advertisement/discovery and authenticated connectivity；the owning domain provides its typed remote
  adapter and ordinary OpenAPI route。
- do not create a generic `/capabilities/{id}/invoke` raw-JSON endpoint or generic job relation。Semantic retrieval owns
  its request-response protocol；each job domain keeps its own state/claim/result semantics。
- advertise exact capability IDs as Peer-owned runtime state；do not repurpose human/admin `labels`。Persistence、lease and
  randomized provider selection are approved below。
- SemanticRetrievalManager is the unified typed facade on every implementing caller。Only a Peer with a non-delegating
  local implementation advertises the capability and serves its inbound；other callers delegate through PeerManager。

### Approved discovery semantics

Capability routing distinguishes three facts:

- **support**: this Peer runtime has an implementation of the exact capability contract；
- **liveness**: this Peer is currently online；
- **readiness**: the implementation's current dependencies/configuration allow it to serve a particular request。

D-119 limits discovery to support + Peer liveness。PeerManager routes an exact capability to an online provider so domain
callers do not inspect liveness；readiness remains service-internal and never becomes discovery metadata。Routing may not
blindly replay a post-dispatch failure because retry safety remains operation-specific。

### Approved liveness mechanism

- persist capability declarations as Peer-owned exact IDs rather than independent service rows；
- persist an expiry/lease fact rather than an `online` boolean，so abrupt process loss becomes offline without a graceful
  shutdown write；
- derive online using database time，avoiding caller/provider clock disagreement；
- keep the lease Peer-scoped rather than capability-scoped。A running Peer updates its declaration when a capability is
  enabled/disabled；readiness does not create capability heartbeats。

The caller-local renewal schedule is an implementation/runtime-config concern；the shared renewal and routing contracts
are approved below。

### Approved Peer persistence shape

```text
peers
  id                uuid primary key
  name              text not null
  labels            text[] not null default []
  config            jsonb not null default {}
  config_schema     jsonb not null default {}
  capabilities      jsonb not null default []
  lease_expires_at  timestamptz null
  created_at        timestamptz not null
  updated_at        timestamptz not null
```

`capabilities` is one validated full snapshot，not a child relation。`labels` remain administrative metadata and never
participate in capability matching or provider selection。`config/config_schema` keep the existing per-Peer owner scope；
they do not become deployment-scoped `configs`。There is no global endpoint、`online`、`last_seen` or readiness column。
The database-time renewal contract below prevents unrelated Peer-row updates from implying liveness。

### Approved lease renewal contract

```text
renew_peer_lease(peer: uuid, ttl_seconds: positive integer) -> timestamptz
```

The `SECURITY INVOKER` database helper requires an existing Peer，calculates expiry from `statement_timestamp()` and
returns the stored value。TTL is supplied by the lease owner because always-on and scale-to-zero deployments have
different renewal models；no fixed protocol duration or duplicate persisted TTL is added。A lease means that the
advertised inbound remains routable，not that one application process is continuously resident，so a deployment control
plane may renew for a wakeable scale-to-zero endpoint。Ordinary Peer-row updates never renew the lease。Graceful shutdown
sets the expiry to null；abrupt loss waits for expiry。

### Approved candidate selection

For one delegation，PeerManager loads candidates whose exact capability matches and whose lease is unexpired by database
time，then excludes the caller itself、malformed inbound descriptors and protocols missing from the caller-local outbound
registry。It randomly orders the remaining Peers once and walks that sequence only when D-129 proves non-execution。UUID、
labels、snapshot order and lease duration/expiry are not routing scores。No eligible candidate raises
`CapabilityDelegationUnavailable`。MVP has no shared round-robin state、weight、priority、load、stickiness or circuit
breaker。

### Approved module topology and delegate contract

The common surface is one deep logical `peer` module，not a new ServiceRegistry/CapabilityManager hierarchy:

```text
provider runtime
  SemanticRetrievalPeerInbound
    capability = exact SemanticRetrieval ID
    interface = {
      protocol: core.peer.protocol.http.v1,
      parameters: { method, absolute url }
    }
    controller -> local SemanticRetrievalManager
  -> PeerInboundRegistry
  -> PeerManager publishes capability + inbound-interface snapshot

caller without local SemanticRetrieval implementation
  SemanticRetrievalManager.retrieve(typed request)
  -> local implementation when registered；otherwise:
  -> PeerManager.delegate(exact capability ID, protocol payload)
       -> candidates advertising capability + live lease
       -> failover/select Peer and its advertised inbound interface
       -> PeerOutboundRegistry.resolve(interface.protocol)
       -> construct one-shot PeerHTTPOutbound(peer, inbound.parameters)
       -> execute and release outbound
  -> SemanticRetrieval validates typed result/domain failure
```

Dependency rules:

- PeerManager imports no Extension、SemanticRetrieval or other capability owner。It sees opaque capability IDs、provider
  candidates and discriminated inbound-interface protocol descriptors only。
- PeerManager may own internal lease/routing components，but they do not become separate public Managers。PeerConnection
  and PeerTarget are removed；neither has remaining distinct responsibility。
- outbound implementations are protocol-specific，not domain-specific。PeerHTTPOutbound is an explicit class/module
  implementing `core.peer.protocol.http.v1`：HTTP plus peer-JWT Authorization、wire encoding and protocol/connection
  failures。It receives the protocol-owned parameter object from the advertised HTTP inbound interface and does not
  interpret SemanticRetrieval payload meaning/domain failures。
- the semantic-retrieval domain owns typed request/result semantics and a provider inbound/controller，but no longer needs
  a SemanticRetrievalPeerOutbound merely to duplicate HTTP mapping。SemanticRetrievalManager delegates its serialized
  request and validates the returned payload when no local implementation is registered。
- D-126 fixes SemanticRetrievalManager as the unified facade。A provider inbound is registered only with a local
  implementation and invokes a non-delegating local execution path；it never re-enters local-or-delegate selection。
- Peer retains an intentional protocol-level relationship to opaque exact capability IDs。No concrete capability module
  is imported or interpreted by PeerManager；dependencies continue from concrete inbound/outbound toward the Peer module。
- core-py `run.py` remains a composition root only：mount/setup providers，start enabled Extensions，then publish the
  complete Peer capability snapshot and begin lease renewal。It does not implement discovery or maintain a manual service
  catalog。
- ExtensionManager integrates capability publication with existing hot lifecycle：start must mount/setup successfully
  before advertising；close withdraws advertisement before unmounting。Extension code does not mutate Peer rows directly。
- client-web may retain Active Record where useful，but arbitrary capability invocation stays off the Peer entity。Its
  peer module implements the same delegate pipeline and protocol-specific outbound registry；domain packages retain
  typed capability facades/contracts rather than HTTP path knowledge。

D-123 supersedes D-120's `capabilities: text[]` projection with structured Peer-owned snapshot entries shaped as:

```json
{
  "id": "core.semantic_retrieval.v1",
  "inbound": {
    "protocol": "core.peer.protocol.http.v1",
    "parameters": {
      "method": "POST",
      "url": "https://example.com/semantic-retrieval"
    }
  }
}
```

The protocol ID discriminates/owns validation of `parameters`；outbound remains caller-local code selected through its
registry。Parameters are published by inbound specifically for construction/configuration of the paired outbound；they
are not generic capability fields。D-124 fixes delegate as one-shot and defers long-lived WebSocket/session models。The
MVP delegation payload/result boundary is one normalized JSON value in each direction；the capability owner performs
typed conversion/validation outside PeerManager，and `core.peer.protocol.http.v1` owns JSON wire encoding。No generic
network invoke route or generic delegation job is introduced。

The advertised parameters and per-call payload are different values。For current SemanticRetrieval:

```json
{
  "parameters": {
    "method": "POST",
    "url": "https://example.com/semantic-retrieval"
  },
  "payload": {
    "query": null,
    "body": {
      "query": "...",
      "options": {}
    }
  }
}
```

`parameters` are static outbound-construction facts published by the inbound。`payload` is the one-shot protocol JSON
produced by the capability owner；an HTTP payload may contain `query` and `body` simultaneously，for example:

```json
{
  "query": {
    "trace": "compact"
  },
  "body": {
    "query": "..."
  }
}
```

PeerManager does not inspect either member；PeerHTTPOutbound interprets the HTTP envelope，while the domain-owned inbound
codec decides how typed values map to/from it。Do not add `request.location`。If future evidence requires representation
metadata，use the standard `content_type` name and decide from that use whether it is static parameters or per-call
payload；the current SemanticRetrieval contract needs neither an extra field nor an HTTP query。

The argument passed to `PeerManager.delegate()` is therefore the already-encoded protocol payload，not the typed
SemanticRetrieval request。`SemanticRetrievalManager` first validates and normalizes the domain request，then uses its
inbound-owned codec to produce the payload above；the provider inbound uses the matching contract to reconstruct the typed
request before entering the explicit non-delegating local path。`PeerManager` keeps that payload opaque，and the selected
outbound only interprets its Peer Protocol envelope。A future protocol needs a capability-owned codec，not a generic
mapping language inside peer routing。

The complete v1 normalized envelope is:

```text
request  = { query?: map<lowercase name, string[]>,
             headers?: map<lowercase name, string[]>,
             body?: JSON value }
response = { status: integer,
             headers: map<lowercase name, string[]>,
             body?: JSON value }
```

Query、headers and body may coexist。`PeerHTTPOutbound` owns peer-JWT Authorization、authority/framing and hop-by-hop
fields，so the capability payload cannot override them。It consumes the exact D-134 non-execution field before producing
an ordinary response envelope。All other status/header/body values remain available to the domain-owned codec。The current
SemanticRetrieval codec uses only a JSON request body；binary/streaming requires another exact Peer Protocol version。

The HTTP `url` is absolute。It replaces the previous method/path-plus-Peer-`rest_api_url` split and gives
`PeerHTTPOutbound` every static construction parameter through one protocol-owned descriptor。The Peer persistence model
therefore has no global HTTP endpoint field；repeated origins inside a small capability snapshot are accepted derived
state，and a future non-HTTP Peer Protocol does not force a new field onto Peer identity。

### Two orthogonal inbound/outbound views

Inbound/outbound is used at two different architectural projections，not as a one-box-one-class rule:

```text
SemanticRetrieval Business outbound
  caller SemanticRetrievalManager + capability-owned codec
  -> PeerManager.delegate
  -> selected PeerHTTPOutbound

SemanticRetrieval Business inbound
  provider Peer HTTP/FastAPI boundary
  -> semantic-retrieval route + capability-owned codec
  -> SemanticRetrievalManager.execute_local

Peer HTTP outbound role
  caller-local PeerHTTPOutbound implementation

Peer HTTP inbound role
  reusable peer JWT + envelope + execution-marker + CORS behavior
  composed into concrete Business routes
```

`SemanticRetrievalOutbound` and `SemanticRetrievalInbound` are therefore useful topology names but need not become public
classes。The Manager's protocol-codec responsibility belongs to the Business edge and explains its intentional contact with
transport-facing values；business ranking/embedding logic still does not move into HTTP。Likewise Peer HTTP inbound may be
implemented through FastAPI dependencies/helpers rather than a nominal `PeerHTTPInbound` object。Here “HTTP” identifies a
concrete Peer Protocol implementation；it does not restore a generic persisted transport domain or TransportManager。

Generic failover stops at provable non-execution。PeerManager may skip an ineligible candidate or try another Peer after
an outbound proves that nothing was dispatched。The Peer Protocol may also carry an explicit non-execution result after
contact，allowing another candidate without exposing service readiness。Once a domain response/error exists，return it；
once dispatch may have occurred but the outcome is unknown（for example a response timeout or post-write reset），surface
that failure without automatic replay。A future capability may deliberately add replay-safe behavior，but PeerManager
does not infer it from HTTP method or opaque payload。

### Rumination as the second capability landing（approved through D-185）

The accepted explicit single-Block rumination trigger creates a second concrete pressure for the same generic delegation
machinery。Use exact capability `core.organization.rumination.v1` with one fixed
business inbound：

```text
POST /organization/ruminate
body: { "block": <int> }
success: 204 No Content
```

A fixed route is important because `core.peer.protocol.http.v1` advertises one absolute inbound URL rather than a path-
template language。The Block identity therefore belongs in the capability-owned JSON body。The route is an action endpoint，
not a durable Rumination/run resource；its empty success mirrors `OrganizationManager.ruminate()`'s approved `None`
completion。

```text
client-web BlockDetailsPanel
  -> client-web OrganizationManager.ruminate(block_id)
       -> PeerManager.delegate(core.organization.rumination.v1, encoded HTTP payload)
            -> PeerHTTPOutbound
                 -> provider fixed inbound / codec
                      -> provider OrganizationManager non-delegating local path
```

The public domain facade retains the same local-or-delegate shape as SemanticRetrievalManager；the provider inbound always
uses a non-delegating local path to prevent loops。PeerManager sees only the opaque exact capability and normalized protocol
envelopes。This does not yet freeze another public method name；the exact private implementation shape belongs to planning。
A provider advertises support when its runtime contains the local implementation；Agent/provider/config
feasibility remains internal readiness。

This mutating capability is a stronger D-129 proof than retrieval。A pre-dispatch or exact
`InkCre-Peer-Execution: not-executed` outcome may select another provider。A normal `204` is executed completion，including
cannot-understand/no-write。Budget/failure responses after execution are returned without failover；timeout/reset after
possible dispatch is outcome-unknown and must stop，because replay could duplicate graph effects。

The proposed client-web action lives in the selected Block's existing `BlockDetailsPanel`。It is one explicit、non-
destructive “Ruminate” action with pending/success/error state，no confirmation、automatic retry、progress protocol or
cancel API。Success reloads the graph through its existing owner；the response cannot highlight exact new entities because
the approved organization result exposes none。Outcome-unknown tells the user to refresh/inspect rather than retrying
automatically。The UI/domain package never chooses a provider URL directly。

The Peer hard cut deletes legacy `Client(rest_api_url).request()` and its convenience methods rather than leaving a second
way for new capabilities to select a Core endpoint directly。The global `rest_api_url` field is already rejected by the
approved Peer persistence shape。Direct database Active Records remain legitimate for shared facts；callable business
capabilities use their domain facade、exact capability ID and PeerManager。Current client-web `Client.request()` additionally
assumes every success has a JSON body，so it is not adapted for rumination's `204` response。

### HTTP inbound public-address acquisition（approved through D-186）

D-130 requires every advertised HTTP inbound to carry an absolute URL and removes a global endpoint from Peer identity。
The provider runtime obtains its public base from its owner-specific persisted `peers.config`，initially exact field
`http_public_base_url` in the core-py Peer config model。Deployment may edit that shared row directly；client-web's existing
Client administration surface hard-cuts into a Peer view that edits the same owner config under its published
`config_schema`。This is per-Peer configuration and does not enter deployment-scoped `configs` or its schema registry。

At advertisement publication/refresh，the provider combines this base with each domain-owned fixed inbound path and writes
the resulting absolute URLs into its full capability snapshot。Config is authority；the snapshot is a routable derived
projection，so the repeated origin does not create a second independently authored address。Exact refresh cadence/change-
detection mechanics belong to implementation planning；no separate environment setting or public-address table is added。

The legacy `settings.client_base_url / CLIENT_BASE_URL`、Compose `CORE_PUBLIC_URL` projection and
`clients.rest_api_url` are deleted。Do not infer a replacement from bind host/port or an incoming request：`0.0.0.0` is not
a public address，TLS/proxy/path-prefix rewriting is invisible to Uvicorn，and advertisement exists before a request
arrives。The configured base is an absolute HTTP(S) URL and may include a deployment path prefix；normalization rejects
query/fragment/credentials before appending fixed paths。When absent，local execution remains available but no HTTP inbound
for those capabilities is advertised。

The exact HTTP representation that distinguishes a domain response from a protocol-guaranteed non-execution response is
one protocol response header with value `not-executed`。PeerHTTPOutbound alone interprets it and returns a protocol-neutral
internal outcome；absence means potentially executed regardless of HTTP status。The exact field is
`InkCre-Peer-Execution: not-executed`。RFC 6648 deprecates newly minted `X-*` parameters and RFC 9205 recommends a specific
application prefix。Browser callers require this field in CORS `Access-Control-Expose-Headers`。Acceptance crosses the
real deployment proxy；an intermediary that strips the field causes conservative no-failover，never unsafe replay。

The earlier rejected shape was:

```json
{
  "method": "POST",
  "path": "/semantic-retrieval",
  "request": {
    "target": "body",
    "media_type": "application/json"
  },
  "response": {
    "media_type": "application/json"
  }
}
```

It remains here only as failure evidence：query/body are not exclusive，and `media_type` needlessly renamed an existing
HTTP concept。

### Exact-target delegation and Extension management（approved through D-192）

The legacy client-web Extension domain is an evidenced consumer of `Client.request()`：remote config update、enable and
disable currently select one Client by identity and construct Core HTTP paths from its `rest_api_url`。D-185 requires that
generic escape path to disappear，but deleting it without replacement would regress Extension administration and hot
lifecycle behavior。

PeerManager therefore exposes one routing entry over the same opaque exact-capability/protocol machinery：

```text
delegate(capability, payload, route_to_peer: PeerRef | null = null)
  null     -> randomized eligible provider sequence
  non-null -> exactly that eligible Peer or explicit unavailability
```

Exact-target delegation applies the ordinary database-time lease、exact capability、valid inbound descriptor and local
outbound-protocol checks，but never substitutes another Peer。`route_to_peer` is caller-local routing policy and never
enters the protocol payload or advertisement。The target identity is a routing constraint supplied by the business owner；
PeerManager still does not import or interpret that business domain。Its type is UUID-backed `PeerRef`，not legacy
`ClientRef` or an integer identity。

The first target-specific consumer is exact `core.extension.management.v1`。client-web's Extension domain addresses the
selected Peer and sends a capability-owned command；the provider's fixed inbound validates/decodes it and calls the target
runtime's non-delegating local ExtensionManager。This preserves Extension-owned config validation and hot enable/disable
effects without a generic capability-invoke endpoint。Exact request/action/error shape remains implementation-plan review，
not a reason to restore arbitrary `Client.request()`。

Do not replace this synchronous target command with database desired-state polling in the current unit。That alternative
would introduce observation cadence、invalid-config handling、live reconciliation and failure-recovery semantics that are
not present merely because Extension rows are shared facts。
