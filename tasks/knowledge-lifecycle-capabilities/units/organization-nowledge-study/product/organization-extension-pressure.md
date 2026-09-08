# Product Pressure: Extension-Influenced Organization

- **State**: accepted cross-unit Product pressure under D-490；exact contribution mechanism intentionally undecided。
- **Purpose**: retain Organization extensibility as a parent-task goal without turning the Nowledge study into premature
  Technical design or forcing every useful learned behavior into Core。
- **Decision authority**: [D-490](../../../decisions/D481-D490.md)。

## Why This Pressure Exists

InKCre's knowledge lifecycle has three action axes：collection、Organization and use/application。Extension growth cannot stop at
collection adapters and Resolver types if domain- or product-specific Organization behaviors are expected to evolve outside the
Core release cycle。

A future first-party Extension could provide capabilities resembling parts of Nowledge。That possibility changes how this study
interprets rejection：

```text
not a Core Organization behavior
  != invalid Product idea
  != forbidden ecosystem capability
  != approved Extension implementation
```

The study must still discover the underlying information semantics first。Extension delivery cannot rescue a behavior whose
authority、graph effect or later-use value is undefined。

## Independent Decisions

For every future candidate，keep these axes separate：

| Axis | Question |
| --- | --- |
| Product validity | Is there a reusable information distinction or downstream capability worth providing？ |
| Behavior owner | Which exact Organization/source/use contract owns semantics and effects？ |
| Delivery owner | Is the implementation Core、first-party Extension or third-party Extension？ |
| Durable owner | Where does stable Product/Technical truth live？ |
| Interface | How is the exact behavior discovered、configured、triggered and observed？ |
| External capability owner | Does execution depend on an Agent、AI provider、host protocol or another runtime？ |

Success on one axis does not decide another。In particular，first-party distribution and high value do not imply Core ownership。

## Minimum Product Invariants For Later Design

An Extension-influenced Organization behavior must eventually expose：

- an exact behavior identity and Product semantics，rather than one generic “organize” mandate；
- its trigger、inputs、candidate/exploration law、graph outcome and honest no-op/failure boundary；
- ordinary Block/Relation validation and persistence rather than private graph authority；
- explicit lifecycle/configuration/availability semantics appropriate to its delivery owner；
- enough observability for a caller to distinguish lifecycle、no-op/replay diagnosis and persisted graph effects without
  requiring one universal report shape；
- no automatic coupling to collection merely because one Extension happens to supply both capabilities。

These are requirements on a future seam，not a proposed registry or API shape。

## Current Repository Evidence And Gap

The current Extension path can publish Sources、Resolvers、HTTP routes and exact Peer capabilities。Current Core Organization
entry points directly expose rumination and media interpretation，while Extension-delivered Resolvers may already influence what
those behaviors can interpret or draft。There is no established general contract for an Extension to contribute or specialize an
Organization behavior as such。

This is sufficient evidence for a future design pressure，not for selecting a mechanism。A generic hook、global behavior registry
or reversible mutation scheme would introduce authority and lifecycle questions before a concrete behavior proves what the seam
must carry。

## Re-entry Condition

Open Technical design only when at least one concrete Extension-owned or Extension-influenced Organization behavior has approved
Product semantics and an Acceptance draft can identify the required discovery、invocation、effect and lifecycle boundaries。A
future first-party Nowledge-inspired Extension is one possible source of that case，not a commitment made by this unit。
