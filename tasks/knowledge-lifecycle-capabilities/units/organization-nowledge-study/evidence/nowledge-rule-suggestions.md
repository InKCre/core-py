# Evidence: Nowledge Rule Suggestions

- **Question served**: Does repeated behavior justify new standing normative information，and where does downstream behavioral
  force begin？
- **Consumer**: [Rule Suggestions Product shard](../product/rule-suggestions.md)。
- **Evidence horizon**: Nowledge official documentation/API observed 2026-09-04。Recheck before version-sensitive Product or
  Technical claims。

## Official Evidence

- Nowledge defines a Rule as an always-on behavior instruction for connected Agents，applied before search、tools or task-specific
  Skills。Rules are intended for behavior that should hold across many tasks。Source：
  [Rules](https://mem.nowledge.co/docs/concepts/rules)。
- Rule scope may be everyone、one AI Profile or one Space。Nowledge distinguishes Rule (“always behave this way”) from Skill
  (“for this task，follow this method”) and Memory (“worth remembering”)。Source：
  [Rules](https://mem.nowledge.co/docs/concepts/rules)。
- Suggested Rules arise when repeated behavior appears in work；a suggestion is not automatically applied and can be accepted、
  edited or ignored。Nowledge describes the observed material as repeated preferences and project habits。Source：
  [Rules](https://mem.nowledge.co/docs/concepts/rules)。
- Rule suggestions run every three days by default，look for repeated preferences and standing rules and remain drafts until
  Human review。Source：[Background intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)。
- Supported connectors receive Rules through the Context Bundle at session start，alongside profile、selected Agent profile、
  active Space and Working Memory。Source：[Rules](https://mem.nowledge.co/docs/concepts/rules)。
- The read API calls these owner-managed AI Context rules and exposes status、scope、source、evidence/support/unsupported Memory
  IDs、confidence、rationale、support count and archive fields。Source：
  [Get Guidance Rules](https://mem.nowledge.co/docs/api/settings/rules/get)。

## Evidence Versus Inference

| Evidence / observation | Current inference | Missing evidence / confidence |
| --- | --- | --- |
| A Rule is always-on connected-Agent behavior，injected before task behavior。 | Rule activation is downstream normative/operational authority，not neutral graph organization alone。 | High。 |
| Suggestions detect repetition but remain drafts until review。 | Repeated descriptive evidence is insufficient by itself to create normative force；review/acceptance is an authority-producing act。 | High conceptual confidence；Nowledge does not state this formal law。 |
| Rules have global/profile/space scope。 | Scope matching belongs to the downstream Agent-context contract；the underlying directive still needs actor/issuer/applicability semantics。 | High。 |
| Evidence IDs、confidence and rationale are retained。 | A proposed rule can preserve derivation basis，but confidence in recurrence does not establish authority to prescribe future behavior。 | High inference confidence。 |
| Accepted Rules reach Agents through Context Bundle。 | Representation and activation are distinct even when Nowledge packages them in one Rule object。 | High。 |
| Rules differ from Skills and Memories by future behavioral effect。 | `rule` can be a useful source-relative semantic role in InKCre without copying the entire operational Rule model。 | Medium-high；requires Product review。 |

## Product Disposition

D-488 finds no independent Rule Suggestions Organization method。Repeated behavior/preferences route to D-472
provenance-preserving n-ary synthesis as descriptive、scoped information。An explicit standing directive may be retained as
ordinary information with an exact source-relative `rule` Relation，but only an authorized actor/source or downstream
configuration action can give it normative force。

Draft/accept lifecycle、Agent/profile/space matching、priority/conflict semantics and Context injection remain downstream
capability/application concerns。No preferred Relation primitive list、Nowledge schedule、registry、field schema or confidence
threshold is transferred。D-493 gives the `rule` word no privileged status。
