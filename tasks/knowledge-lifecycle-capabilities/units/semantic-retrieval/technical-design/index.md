# Semantic Retrieval Technical Design

- **Status**: Product/Technical contracts，both capability landings and HTTP inbound address authority are approved through
  D-186；Acceptance is approved through D-190；implementation planning remains。
- **Current review**: exact implementation decomposition and preflight evidence。
- **Rule**: each topic becomes a contract only after explicit review；later findings revise it through a visible decision，
  not silent prose drift。

## Topic Navigation

| Topic | Ownership / contents |
| --- | --- |
| [Embedding profiles and vector records](embedding-profiles.md) | Stable vocabulary、Profile/Record schema、pgvector and ANN boundary、review order |
| [AI routing and semantic projection](ai-and-projection.md) | AIDialect/Provider/Model/Manager、Block/Relation projection、Resolver labels |
| [Embedding maintenance and deployment config](maintenance-and-config.md) | Freshness/outcomes、maintenance、ConfigContract and DeploymentConfigManager |
| [Semantic retrieval contract](retrieval-contract.md) | Request、score、ranked Block/Relation result and bounded filters |
| [Peer capability delegation](peer-delegation.md) | Discovery、lease、protocol inbound/outbound、HTTP delegation and failover |
| [Rumination and graph forms](rumination-agent-graph.md) | Rumination semantics、Resolver draft Tools、StarsGraphForm/GraphForm and graph-command authority ledger |
| [Agent definition、Thread and runtime](agent-runtime.md) | AgentManager、persisted Agent definitions、Thread persistence boundary、Tool binding/execution and Message lifecycle |
| [Shared row timestamp contract](shared-row-timestamps.md) | Database-owned `updated_at` boundary |
| [Delivery map](../delivery-map.md) | Dependency-ordered implementation increments；design probe only |

## Current Technical Edge

Producer Forms、Agent/Thread/Tool execution and Agent-validate → Resolver-create → InfoBase-normalize ownership are closed
through D-186。Acceptance is approved through D-190；the active design edge is implementation planning and preflight。
Approved upstream
contracts remain linked by decision ID through the [decision register](../../../decisions/index.md)。

For the current graph-command boundary，use the topic file's [boundary ledger](rumination-agent-graph.md#current-boundary-ledger)
as the active contract。D-175–D-177 document how the correction was reached；they must not be merged as simultaneous
responsibilities。

## File Boundary

- Topic files own detailed task-state technical contracts；this index owns only navigation and the current edge。
- Splitting by technical owner does not create additional runtime services or persistence authorities。
- New material goes to the smallest owning topic。Create another topic only when an existing file gains a second independent
  review/navigation pressure，not merely because of line count。
