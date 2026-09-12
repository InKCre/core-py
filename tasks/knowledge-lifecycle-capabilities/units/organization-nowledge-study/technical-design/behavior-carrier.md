# Organization Behavior Carrier And Dependency Direction

- **State**: D-505/D-523 accepted exact BehaviorResolver candidate and operation carrier；exact graph-command methods remain
  independently callable beneath Agent-backed orchestration。
- **Question**: does “each Organization behavior owns its semantics” require a new `OrganizationBehavior` entity/base class，and
  can existing Resolver capability carry more of the design without coupling Organization to Agent/Tool execution mechanics？
- **Accepted recommendation**: do not add a generic runtime behavior entity、table or second registry。Use exact behavior
  modules/Managers as inward graph-command owners。D-504's `candidate for` routing proves a graph-addressable behavior Block；the
  accepted design lets that Block's exact concrete Resolver implement `consider_candidate()` and the complete behavior
  operation。This reuses
  Resolver registration without putting Organization methods on information content Resolvers or making Resolver base import
  Organization/Agent mechanics；the concrete BehaviorResolver depends inward on independently callable exact graph commands。

## Recovered Current Facts

There is no current `OrganizationBehavior` schema、model、protocol or base class。

- `OrganizationManager` is a facade over two exact paths：explicit focal rumination and system-driven media interpretation。
- media interpretation is an ordinary module with its own candidate query、configuration、Agent selection、execution and a
  behavior-specific report；the latter has a concrete caller but does not prove a universal Organization report contract。
- Agent runtime is graph-blind。Organization supplies context and code-owned Tool handlers；Agent does not own graph、Resolver or
  Organization policy。
- Resolver is already an exact namespaced/versioned Block interpretation contract。It can read direct Relations、produce solved
  projections and opt into typed graph drafting via `draft_input_model + create_graph()`。
- persisted Relation currently has no Resolver；its identity and generic projection use exact `from_ + to_ + content`。

D-523 treats the current rumination placement as migration evidence，not a pattern to preserve：rumination moves onto an exact
`RuminationBehaviorResolver`，while unrelated media interpretation is outside that placement correction。

The present code therefore demonstrates exact behavior by module composition，not by one behavior object or registry。

## Three Different “Carriers”

```text
execution carrier
  Job / Cron / explicit call
  owns occurrence、claim and timeout

code responsibility carrier
  exact behavior module + Manager functions + typed schemas
  owns candidate rule、SOP、semantic command、invariants and consuming law

durable semantic carrier
  ordinary Block / Relation graph facts under exact Resolver/content contracts
  survives the invocation and is available to later use
```

No reason currently requires one runtime entity to combine these roles。In particular，a Job is not the semantic behavior，and a
descriptor Block exists for graph reference/explanation rather than merely to select an Agent or schedule a command。

## Required Dependency Direction

```text
route / Job / Agent adapter / direct-AI adapter / deterministic caller
                         |
                         v
              exact Organization operation
              - candidate/context functions
              - typed proposal/command
              - validation + graph mutation
              - exact consumer/use law
                         |
                         v
        Resolver + retrieval + ordinary InfoBase contracts
```

Code dependencies for ordinary exact operations must follow the same arrows：

```text
organization_<behavior>_job         -> exact BehaviorResolver operation
exact BehaviorResolver/orchestrator -> optional DeploymentConfig + AgentManager + exact command methods
organization_<behavior>_tool        -> exact BehaviorResolver command/read methods
organization_<behavior>_command     -> Resolver/retrieval/InfoBase

forbidden:
organization_<behavior>_command -> AgentManager / Agent Tool registry / Thread
Resolver base / ResolverManager -> Organization behavior
InfoBase kernel                 -> Organization behavior
```

The proposal/command must be constructible、callable and testable without an Agent or Tool registry。For example，an evolution
command may be `record_supersession(newer, older, scope)`。If an exploratory Agent is used，an outer module imports this command
and exposes a thin Tool；the evolution module does not register or import that Tool。A deterministic rule、bounded direct model
call or future Human workflow can depend on the same operation directly。

This avoids introducing a speculative `JudgmentProvider` abstraction。The inward dependency is already the typed behavior
command；which outer caller/judge is delivered stays exact until two concrete implementations prove reusable polymorphism。

An exact behavior may still require an exploratory Agent in its ordinary automated path。D-523 places that orchestration directly
on the concrete BehaviorResolver method rather than adding an ExecutionAdapter。It is not the identity、command、persistence or
consumer model of the behavior。Use the least powerful judge that preserves
the behavior：deterministic first，one bounded AI judgment second，Agent loop only for demonstrated iterative exploration/action。

Current `AIManager.chat()` already supports provider-neutral calls without Agent or Tool，and Resolver faithful-text
materialization uses that path。It does not yet provide a general structured-output contract，so this evidence proves separation，
not that every semantic behavior should immediately switch to fragile prose/JSON parsing。

Current rumination/media code does not yet separate orchestration from exact graph commands cleanly：`organization.py` both
registers Agent Tools and implements `OrganizationManager`，while `organization_media.py` directly imports and runs
`AgentManager`。A concrete BehaviorResolver may legitimately occupy that outer orchestration role，but its graph commands must
remain independently importable/testable without Agent mechanics。

## Resolver Reuse

Resolver should be strengthened where it already owns the answer：

1. **Input interpretation**：Organization reads heterogeneous candidate Blocks through exact Resolver text/label/solved content。
2. **Agent exploration**：bounded Agent Tools expose Resolver-backed reading for Blocks discovered after the initial seed。
3. **Typed authoring**：when a behavior creates a new information Block whose content has an exact format，its Resolver owns the
   draft input and `create_graph()` mapping。
4. **Derived-information use**：when a synthesized or interpreted Block needs more than generic text projection，an exact Resolver
   may own its persisted content decoder and use-facing projection。
5. **Behavior execution receiver**：an exact behavior Block Resolver may explain its Block and orchestrate incoming
   `candidate for` seeds；the exact graph command remains independently callable beneath that concrete Resolver。

An **information content Resolver** should not become a generic Organization behavior host：

- a Resolver instance is selected by one Block's persisted content contract；evolution、linking、duplicate and synthesis judge
  relations among multiple potentially heterogeneous Resolvers；
- candidate selection、cross-Block scope、state law and automatic scheduling are not properties of one endpoint's content format；
- attaching behaviors to input Resolver classes creates cross-Resolver combinations and makes a new content decoder implicitly
  acquire Organization policy；
- Product design already distinguishes faithful Resolver meaning from Organization-authored semantic judgment。

This prohibition concerns attaching cross-Block Organization meaning to the Resolver selected by an input information format。
It does not prohibit an exact **behavior Block Resolver** whose receiver identity is the behavior itself and whose concrete class
acts as an outer orchestrator。D-520 places the non-trivial supersession lineage/current-frontier interpretation on
`SupersessionBehaviorResolver.read_lineage(focal_block_id, bounds)`；the focal information Block remains an explicit query input，
not the method owner。Duplicate connectivity over arbitrary caller-supplied Blocks has no semantic behavior owner and remains a
bounded vocabulary-blind Graph Navigation query；the application owns the later count-once interpretation of that neutral topology result。

## What “Improve Resolver Instead” Can Mean

| Proposal | Judgment | Reason |
| --- | --- | --- |
| Expose bounded Resolver-backed read/exploration capabilities，including Tools when an Agent is selected | **yes** | closes a demonstrated current inability to inspect candidates beyond initial context without making Tool the semantic API |
| Use exact Resolvers for new derived information Blocks when they have a real decoding/projection contract | **yes, per output** | reuses existing versioning、extension and use projection authority |
| Reuse draft-capable Resolver contracts from behavior commands or optional Agent Tools | **yes** | current code already proves Resolver-owned typed authoring；Tool remains only one adapter |
| Use one exact Resolver type per graph-addressable behavior Block with `consider_candidate()` | **yes, D-505** | reuses Resolver identity/registration and gives `candidate for` an actual receiver without coupling content Resolver types |
| Add a Source-like behavior pointer plus a second capability registry | **not yet** | no separately persisted behavior instance/config/state currently exists；the pointer would only duplicate Resolver registration |
| Put cross-Block evolution/linking/synthesis policy on each input Block Resolver | **no** | wrong semantic owner and combinatorial coupling |
| Add a Resolver to every Relation now | **not yet** | possible schema evolution，but it needs a concrete generic relation dispatch/indexing use；it still would not carry candidate/SOP/state law |
| Reify every Organization relation as a Resolver-backed Block | **no by default** | adds graph topology solely to obtain a discriminator；use only when the assertion itself needs identity、attribution or incoming relations |

Thus Resolver serves two honest receiver roles without merging them：content Resolvers interpret information Blocks；an exact
BehaviorResolver represents and orchestrates a graph-addressable behavior Block。The Resolver base/registry does not reverse its
dependency toward Organization，and the independently callable exact graph command remains the semantic mutation boundary。

## Minimal Planned Shape

For each accepted exact behavior，add only the code that behavior needs；do not require a shared interface：

```text
exact behavior module
  candidate query / trigger-facing function
  judge/Agent-independent Manager command(s)
  exact content/graph contract
  exact downstream consumer

optional Agent-backed methods on the concrete BehaviorResolver
  initial context + SOP + core.organization.<behavior> Agent selection
  AgentManager invocation through one complete purpose-built definition

Agent Tool bindings
  shared retrieval/Resolver/navigation meta-tools
  thin exact mutation Tool(s) -> the same Resolver command methods

optional exact Job Handler
  check Resolver availability + invoke its bounded behavior method only

optional exact behavior Block + BehaviorResolver
  required only when this behavior is addressable as a cross-model candidate target
  owns actual behavior operation and consider_candidate orchestration over independently callable exact commands
```

Extract a common abstraction only after concrete implementations repeat a material mechanism。Shared Agent read Tools and generic
InfoBase persistence are already such demonstrated mechanisms；a universal Organization behavior lifecycle is not。
