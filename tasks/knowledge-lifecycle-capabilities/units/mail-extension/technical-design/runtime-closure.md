# Mail Runtime Closure

- **Status**: implementation synthesis only；withdrawn as one review batch because it compressed too many independent
  judgments。Its sections are reviewed through smaller MIME、Source-foundation and Mail-collection batches before freezing。
- **Boundary**: closes Mail materialization、Source/config、ordinary/backfill collection and intentional remote effects。
  Exact MailAdapter DTO names、wire batching and checkpoint serialization remain implementation-owned under D-281。

## Common Source Contract Pressure（pending separate batch）

Mail requires four additive common Source fields/contracts rather than hiding them in its protocol config：

1. `sources.storage`: nullable writable-target reference frozen by D-283。
2. `sources.created_at` / `updated_at`: database-owned Source lifecycle timestamps。Mail uses `created_at` as the exact local
   setup boundary for its first ordinary collection；the timestamp is not external message time。
3. replace legacy `collect_at` with nullable `collect_cron`: one standard five-field cron expression；null disables scheduled
   job creation。This admits minute/hour/day cadence without adding interval/schedule-type abstractions。
4. `sources_types.collect_config_schema` and nullable `backfill_config_schema`: Source registration derives independent JSON
   Schemas for ordinary collect and optional backfill commands，just as it already owns setup `config_schema`。Absence of the
   latter means the Source type does not support backfill；client-web does not accept blind JSON。

Source registration/runtime validates Source、ordinary-collect and optional backfill configs independently。This is framework-
boundary validation；generic Job remains an execution envelope and does not interpret source-specific intent。

### Scheduled command coordination（open pressure）

Repository evidence invalidates treating `collect_cron` as only a field rename：

- `SourceManager.set_up_collect_jobs()` currently reads `sources.collect_at` only during runtime bootstrap and installs
  process-local APScheduler jobs；client-web writes the Source row directly，so a schedule edit does not reconfigure the
  running scheduler until restart。
- every core-py Peer that boots the Source type can install and fire its own schedule。Each firing creates a different collect
  job，so the existing atomic `PENDING → RUNNING` claim prevents two runners executing one row but cannot prevent duplicate
  scheduled rows。
- every Peer currently scans all pending jobs；without local Source-type eligibility in claim，a Peer lacking the extension
  implementation can claim a job it cannot execute。This conflicts with the already accepted job-table delegation model。

D-293/D-294 correct the first proposal：the Collect-domain Job must not become a generic scheduling ledger，but a Cron
abstraction alone is also insufficient。The exact requirement is distributed occurrence materialization：several capable
Peers may observe one due schedule，yet collectively create at most one durable Collect Job for that canonical occurrence。

The active topology candidate is：

```text
Cron domain
  recurring definition + timezone + due/misfire/firing coordination
      |
      +-- invokes one exact registered command-creation target
              |
              +-- Collect-owned target creates ordinary SourceCollectJob
                       |
                       +-- capable Peer claims and runs Collect-domain Job
```

The topology remains a useful ownership sketch，not yet a solution：without a shared atomic election/materialization protocol，
each Peer can still invoke the target once。PostgreSQL may serialize competing application attempts，but it must not evaluate
the schedule or implement domain Job creation through triggers/procedures。The winning application Peer must create the
Collect-owned command；normal Collect runner delegation remains unchanged except that claim must admit only locally registered
Source types。

D-295 places the primary arbitration in the invariant that one Cron may associate with at most one non-terminal
`SourceCollectJob`。The Cron cursor is nullable `last_scheduled_for`，and the winning Job insertion plus cursor advance commit
atomically。This both converges ordinary simultaneous attempts and prevents overlap accumulation。

Do not prematurely realize that invariant as `SourceCollectJob.cron` plus a partial unique index。A Job is an independently
executable Collect command after creation and must not depend on its optional creation mechanism；manual、Cron and future
producers must not become nullable provenance columns on the command model。The physical association belongs on the creation
side or an exact Collect–Cron binding seam。Its smallest shape and whether a locked creator-owned `last_job` pointer dominates
accepting the benign terminal-transition race remain the active review question。

One narrow edge remains before persistence design：a Peer may retain an old cursor snapshot until after the winning Job has
already become terminal，at which point partial active uniqueness alone no longer rejects the same occurrence。Freeze the
smallest exact occurrence fence for this stale-reader case；do not depend on Job duration making it unlikely。Generic Job
extraction is no longer the leading question。Schedule persistence、target binding、timezone and misfire semantics follow only
after this protocol is closed；they must not be silently derived from each Peer process's local timezone。

### Global Job + global Cron premise（active evaluation，not frozen）

Sir reopened the design under a stronger premise：promote the existing Source Collect Job lifecycle into a global durable Job
module，and make Cron global rather than Collect-owned。Under that premise the prior binding candidate changes shape：

```text
Global Cron
  ├── job_type: core.source.collect.v1
  ├── job_parameters: {source, config}
  └── last_job ──> Global Job envelope
```

- `crons.last_job` becomes a correctly directed creator-owned reference to `jobs.id`。It holds the most recently materialized
  Job even after terminal completion；Job completion never calls back into Cron。
- Cron-row locking、terminal-state recheck、Job creation、`last_job` replacement and `last_scheduled_for` advancement share one
  transaction。This closes the fast-terminal stale-reader race without putting `cron` or `scheduled_for` on Job。
- **Binding correction**：do not add `SourceCollectCronBinding`。The recurring command is a user-authored composition of a
  global Cron and a typed Job template；`job_parameters.source` already names the called Source。Source neither owns nor needs
  awareness of whether users scheduled its collect behavior。A binding table would duplicate that composition、imply reverse
  Source ownership and require lifecycle/query machinery without adding required behavior。
- Cron remains narrower than a generic invocation system：one firing copies its exact `job_type` and typed
  `job_parameters` into one persisted global Job。It does not execute the Job or understand Source collection。
- `last_scheduled_for` and `last_job` have separate jobs。Under the locked transaction，`last_scheduled_for` proves that the
  same canonical occurrence was already dispatched；`last_job` only tells whether the previously produced Job remains
  non-terminal and therefore whether later occurrences must be coalesced rather than stacked。Neither field alone provides
  both guarantees。

The global Job module is justified only as a deep durable background-command lifecycle：exact registered Job types、common
pending/running/terminal timestamps and atomic capable-Peer claim。It must not become `type + arbitrary unvalidated JSON +
universal behavior`，must not absorb request-response Peer delegation，and adds no retry。Whether typed Job input is stored in
the global envelope or an exact domain detail table remains a later persistence decision；the latter preserves FK authority but
costs an additional joined lifecycle。

`sources.collect_at` is removed as an authority，not retained as a projection or dual-written compatibility field。A non-null
legacy value maps conceptually to one global Cron whose `job_type` is `core.source.collect.v1` and whose typed parameters carry
that Source ID；null maps to no Cron。The old process-local `SourceManager.set_up_collect_jobs()` is deleted；APScheduler may
remain only as a Peer-local wake-up timer for `CronManager.check()` and `JobManager.check()`。client-web edits the global Cron
surface instead of `sources.collect_at`。Exact legacy-row conversion is blocked by the old schedule's implicit process timezone；under
the already accepted clean-baseline policy，reset is preferable to inventing a timezone，unless preflight discovers an explicit
deployment authority that makes lossless conversion possible。

### Cron schedule representation（frozen by D-298）

- `crons.schedule` is one five-field UNIX cron expression。
- deployment config `core.cron` owns one IANA `timezone`；absence falls back to `UTC`。
- Peer-local process/browser/OS timezone never interprets durable Cron。
- no `CRON_TZ`-style persisted dialect、per-row timezone override、seconds field or interval union enters the MVP。

### Global Job persistence（frozen by D-299；handler race open）

- `job_types` projects exact IDs、descriptions and parameter JSON Schemas from the runtime Handler Registry。
- `jobs` uses an `int8` identity and persists type、typed JSONB parameters/state、status and lifecycle timestamps；the old
  Source-specific Job table is hard-cut rather than retained as a detail table。
- `core.source.collect.v1` parameters carry Source and collect config；the Handler owns their semantics。
- Job remains a durable background-command lifecycle，not a generic invocation/retry/delegation mechanism。
- a boolean `can_handle(parameters)` is only a candidate。The design must close the interval between capability inspection and
  atomic pending-to-running claim，including extension/Source handler deactivation，before freezing the Handler interface。

### Handler eligibility and claim（frozen by D-300）

```text
pending candidate
  -> validate parameters
  -> local can_handle(parameters)
  -> atomic PENDING-to-RUNNING conditional update
  -> run only when the update returns the claimed Job
```

False eligibility leaves the Job untouched；a lost conditional update ends that Peer attempt。`can_handle` is a side-effect-free
local implementation check，not an external readiness probe。Capability disappearance after the check is an accepted narrow
TOCTOU rather than pressure for leases、draining、reverse status transitions or retries。

### Job execution budget and resumable Mail progress（persistence frozen by D-305）

- Job owns an explicit configurable execution timeout；remove the current universal five-minute running timeout。
- do not add `jobs.peer` or use Peer discovery lease expiry as Job abandonment detection。Job execution must not depend on
  Peer delegation/discovery lifecycle merely because both are distributed capabilities。
- Mail collection/backfill treats one Job as a bounded opportunity to advance，not as a promise to finish an entire historical
  horizon。Partial graph effects remain durable；ordinary synchronization may continue from its protocol checkpoint，while
  backfill deliberately has no durable continuation checkpoint under D-307。
- reaching an execution/load boundary neither rolls back prior graph writes nor creates retry/attempt lineage。Cron remains
  unaware of progress and simply materializes future Jobs under its ordinary schedule rules。
- timeout conditionally closes an overdue `running` Job as terminal `timed_out`。That outcome describes only this invocation；
  a normal bounded return is `finished` and an escaping execution/domain error is `failed`。A late worker close cannot overwrite
  an already-terminal row。
- incremental Source checkpointing is recommended because collect may be interrupted by timeout or process/system failure，
  but is not a required Source capability。A weaker Source may rescan and rely on its own identity/reconciliation；JobManager
  does not enforce checkpointing、resume traversal、rollback or retry。
- `job_types.default_timeout_seconds` owns the non-null exact-type default。Direct/manual creation and
  `crons.job_timeout_seconds` may override it；`jobs.timeout_seconds` snapshots the resolved non-null value at creation。
  Later type/Cron edits do not reinterpret existing Jobs。
- the positive integer seconds representation is portable across PostgreSQL/PostgREST、Python and TypeScript。The budget
  begins at successful claim，so pending time does not consume it；expiration derives from `started_at + timeout_seconds`。
- the executing worker establishes a local deadline and best-effort cancels the Handler。Independently，any Job worker may use
  database time to conditionally close an overdue `running` row as `timed_out`，covering original-worker/process loss without
  storing an execution Peer。The database terminal state wins over every late close。
- cancellation-insensitive external operations may rarely produce effects after the terminal timeout；those remain valid
  partial effects。MVP does not add Peer-heartbeat coupling、execution leases、requeue、retry or per-Job process isolation。

### Cron missed-occurrence semantics（corrected and frozen by D-302）

- Cron only examines the canonical current minute in the deployment timezone。If no capable checker observes a matching
  minute，that occurrence is lost；there is no catch-up、coalescing debt、misfire option or `active_from`。
- under the locked Cron row，equal `last_scheduled_for` suppresses duplicate creation for the current occurrence；a
  non-terminal `last_job` suppresses overlap。Successful creation atomically writes both fields。
- creation、re-enable、schedule/template edits and timezone edits simply affect subsequent current-minute checks；they do not
  create historical debt。
- run-now directly creates a Job from the Cron template and does not update Cron progress。

## Deployment Source Policy（pending separate batch）

- deployment config key/schema：`core.source` / `core.source.config.v1`。
- model：`SourceDeploymentConfig(default_storage: StorageID = -4)`。
- effective target：non-null `sources.storage` → configured deployment default → hard-coded built-in `-4` when the config
  record is absent。A present invalid reference does not fall through。
- Storage registry derives `storage_types.writable` from registered `WritableStorage` implementations；database integrity
  prevents `sources.storage` from selecting a read-only type。Deployment JSON references remain use-time defended and
  readiness-visible under the existing config-reference policy。

## Mail Configuration（pending separate batch）

### Extension default

`MailExtensionConfig.default_excluded_mailboxes` owns one `MailboxExclusionPolicy`：

- exact normalized mailbox names；
- canonical special-use roles，defaulting to `drafts`、`junk` and `trash`。

No glob/regex/provider-label language is introduced before real pressure。

### Source config

```text
protocol: Literal["imap"]
parameters: IMAPParameters
excluded_mailboxes: MailboxExclusionPolicy | null
ordinary_mark_as_seen: bool = true
backfill_mark_as_seen: bool = false
synchronize_deletions: bool = false
```

- `protocol` discriminates typed parameters；IMAP parameters contain endpoint/security/login values only。
- null exclusions are a transient materialization request，not dynamic inheritance。At Source creation or the first validated
  Mail command，whichever has the necessary extension-config snapshot，the runtime resolves the current extension default and
  compare-and-set persists that complete policy into Source config；the command then uses one concrete Source-owned snapshot。
  Later extension-default changes affect only future/unmaterialized Sources。Explicitly resetting the field to null requests
  one new materialization on next use；it does not permanently couple that Source to the extension default。
- a non-null Source value replaces the complete policy；there is no field-level merge authority。Exact-name and special-use
  role exclusions are ORed when evaluating one Mailbox，but their persisted lists do not merge with the extension default。
- ordinary/backfill seen mutation are independent linear Source policies。Each command reads only its matching field；there is
  no Job-local override、inheritance or fallback between them。
- synchronized deletion consumes only trustworthy incremental removal evidence；when QRESYNC/VANISHED is unavailable，the
  Source leaves membership untouched and records the unavailable behavior in diagnostics rather than scanning all UIDs。
- Newsletter Source/Resolver and `/mail/imap` creation shortcuts are PoC remnants and are hard-cut。Generic shared-database
  Source creation plus one exact Mail Source type remains the authority。

## Independent Mail Collect Commands（pending separate batch）

Mail registers two exact Job command paths rather than a discriminated intent union：

```text
core.source.collect.v1:
  parameters: { source, config: {} }

core.source.backfill.v1:
  parameters: {
  source,
  config: {
  since: date,             # required, inclusive remote INTERNALDATE boundary
  before: date | null      # optional, exclusive remote INTERNALDATE boundary
  }
}
```

- `core.source.collect.v1` is the ordinary manual/scheduled Job type；empty Mail config is valid。Cron templates use this exact
  type without learning Mail schema。
- `core.source.backfill.v1` is a distinct Job type。There is no persisted `intent` discriminator，and a Source type with no
  backfill config/implementation cannot handle it。The ordinary product journey presents it as an explicit action，but Cron
  remains free to materialize any valid Job template and does not judge recurrence value。
- Backfill is an explicit historical collect，not a parallel lifecycle or legacy `full`。Its boundaries use transient remote
  occurrence INTERNALDATE because that is the server query authority；INTERNALDATE is not copied into canonical Email。
- A required `since` prevents an accidental unbounded history traversal。Source mailbox exclusions apply equally to both
  intents；a job-level mailbox selector/override is not introduced without a user path。
- Backfill uses only `Source.backfill_mark_as_seen`（default false）；ordinary collection uses only
  `Source.ordinary_mark_as_seen`（default true）。Changing either is an explicit persisted Source-config update，not a per-Job
  override。
- typed validation requires `since < before` when `before` is present。A valid range with no matching occurrences finishes as
  an ordinary no-op；neither condition earns a domain-specific Job outcome。
- Backfill never reads、advances or regresses the ordinary continuous-sync checkpoint。A timed-out/failed backfill is followed
  only by an explicit new one-shot Job，normally with a narrower range or larger timeout，and relies on graph reconciliation；
  no durable backfill cursor、campaign or retry lifecycle is added。The ordinary product UI does not encourage a fixed range
  as recurring work，but a valid global Cron template remains valid under D-309。

## Ordinary Collection and Checkpoint Effects（pending separate batch）

1. Validate Source and typed job config，resolve live exclusion policy，open one async-context MailAdapter。
2. Discover eligible mailboxes and ensure Source/Mailbox provenance graph。
3. For each mailbox，read its adapter-typed checkpoint from Source state。If absent，limit initial ordinary acquisition by
   `sources.created_at`；later jobs use the accepted checkpoint and D-269 capability ladder。
4. Persist each occurrence graph independently，including its authoritative membership、observed flag snapshot and any exact
   incremental-removal effect enabled by Source policy。Partial prior effects remain valid and later observation reconciles
   them。
5. A primary graph failure stops traversal of that mailbox before its checkpoint can cross the unaccepted occurrence；the
   Source records a bounded diagnostic and continues other mailboxes。It does not invent per-occurrence rollback、retry or a
   generic partial-success status。
6. After each accepted graph commit，perform the matching configured seen action best-effort。On success，also add the local
   Seen tag fact；
   on failure，record bounded Job diagnostics。The action does not gate accepted collection progress or checkpoint advance。
7. Advance only successful mailboxes。Under overlapping jobs，briefly lock/merge Source state and accept a proposed mailbox
   checkpoint only if the stored checkpoint still equals the command's observed base；never overwrite newer progress。

The Source may isolate one mailbox failure and finish the generic job normally，recording bounded diagnostics/counters in
job state。There is no completed-with-errors status、job retry or mailbox-completeness promise。

Mailbox exclusion is collection scope，not a graph-deletion command。Excluding a previously observed Mailbox leaves its graph
and checkpoint intact；removing the exclusion lets the adapter continue from that checkpoint。Likewise，enabling synchronized
deletion later is prospective：while it is disabled，trusted remote-removal observations do not mutate the graph and ordinary
checkpoint progress is not held for possible future policy changes。Retroactive deletion reconciliation would require a
separate explicit operation and evidence source，not reinterpretation of an already-accepted checkpoint。

## Access-context continuity（frozen by D-311）

An in-place edit from one configured remote access context to another cannot be treated as proven continuity merely because
the `sources.id` row is unchanged。Existing Mailbox scope、ordinary checkpoints and lazy MIME references all depend on the old
context；blindly resetting only the checkpoint would still mix provenance and can make old remote content unreachable。

The selected Adapter projects a non-secret access binding persisted by the Mail Source as validator state after the first
successful adapter entry and before Mail graph effects。For IMAP it includes the public protocol plus normalized host、port、
security mode and login name，while excluding rotatable password/credential secrets。A later binding mismatch fails use with a
repairable configuration error instead of guessing continuity、deleting old graph or silently rebinding it；the user restores
the old binding fields or creates a new Source for a different context。A remote-I/O Mail Resolver validates an existing
binding but does not initialize or replace Source-owned state。Exact Pydantic field names and client-web edit guidance remain
implementation-owned under this frozen authority rule。

## MIME-Part Materialization（closed separately）

Closed by D-286–D-291 and [Mail MIME materialization](mime-materialization.md)：existing content short-circuits
Source/target-Storage routing；`SolvedMimePart.content` contains any one matching child's Block and direct solved content；
the singular InfoBase read promises no uniqueness、order or stable selection；redundant graph children remain benign and
Organization-repairable；lock/recheck reduces duplicates without making exact-one a correctness condition；Resolver base
solving exposes semantic completion rather than created/existing mechanics。

## Implementation-Owned Consequences

- Mail Source state is a typed map from stable local Mailbox BlockRef to adapter checkpoint；it remains cursor/validator
  state，not a collected-item ledger。
- The generic Source UI projects `config_schema` and `collect_config_schema` through its existing JSON-schema editor；a new
  Mail-only setup/backfill page is unnecessary。
- Exact Pydantic class names、diagnostic field names、IMAP TLS enum spelling、checkpoint DTOs、batch sizes and SQL helper names
  are finalized during implementation planning/preflight provided the above contracts remain unchanged。
