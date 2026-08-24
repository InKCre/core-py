# Knowledge lifecycle capabilities

- **Objective**: improve InKCre's collection、organization and application capabilities through independently valuable、
  vertically acceptable units。
- **Guardrails**:
  - collection、organization and application are actions，not information states；Blocks/Relations remain info-base
    authority；
  - source、resolver、storage、extension and Peer mechanisms evolve only under concrete vertical pressure；
  - one implementable unit is active at a time；Product、Technical、Acceptance and preflight precede an Impact Handshake，
    then source implementation waits for Sir's explicit start；
  - use current Hub/local durable docs as truth；completed task history remains in Git and is not a second authority；
  - ask Sir only about credible non-dominated forks that materially change product behavior、authority、public contract or
    expensive recovery。Derive ordinary names、mechanical consequences and low-risk implementation choices locally。
- **Verification**: each unit closes through its real public boundary and projects stable truth to exactly one durable owner；
  use the least complex evidence that adequately proves the contract，without turning manual、scripted and automated evidence
  into a mandatory maturation sequence。
- **Current Truth**:
  - Memos backend、RSS hardening、Mail、semantic retrieval、lexical feature retrieval and graph-navigation retrieval are
    implemented、accepted and reflected in current Hub/Spoke durable docs；
  - graph-navigation retrieval closed through core-py PR #78、client-web PR #85 and ui `@inkcre/ui-web@1.4.0`；
  - no capability unit is currently active；baseline cleanup has established the next-unit repository baseline；
  - historical decisions、plans and acceptance evidence were removed from the checkout after promotion review；Git history
    remains the recovery path。
- **Next Step**: after baseline cleanup closes，select one unit from the remaining queue in
  [capability-map.md](capability-map.md) using current user value、dependency pressure and uncertainty—not table order。

## Discussion and delivery loop

```text
current model + evidence
  -> Product contract
  -> Technical contract <-> Acceptance <-> implementation-plan probe
  -> preflight / failure-branch simulation
  -> frozen execution baseline + Impact Handshake
  -> explicit start
  -> implementation -> verification -> durable projection -> closure
```

Topology is used when ownership crosses modules；sequence/state models are used when behavior repeats、waits or partially
persists。They are reasoning tools，not mandatory artifacts。When one coherent solution follows from established constraints，
present the result for review instead of manufacturing another decision。
