# Evidence: Nowledge Skill Suggestions

- **Question served**: Which parts of Skill Suggestions concern reusable information organization，and which parts concern
  downstream Agent capability lifecycle？
- **Consumer**: [Skill Suggestions Product shard](../product/skill-suggestions.md)。
- **Evidence horizon**: Nowledge official documentation/API observed 2026-09-03。Recheck before version-sensitive Product or
  Technical claims。

## Official Evidence

- Nowledge describes a Skill as a specific repeatable task procedure carrying non-obvious experience from real work，distinct
  from a prompt、rule、generic checklist or broad principle。Suggested Skills remain off until enabled。Source：
  [Skills](https://mem.nowledge.co/docs/concepts/skills)。
- Suggestions run every three days，search repeated ways of working across Memories and Threads，read procedure-typed Memories
  first and attach the source moments that taught the procedure。Source：
  [Background intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)。
- Skills may be suggested、authored or imported，and compile to `SKILL.md` with optional scripts、references and eval cases。
  Enabling materializes/registers them for connected Agent hosts；disabling stops materialization without deleting the Skill。
  Source：[Skills](https://mem.nowledge.co/docs/concepts/skills)。
- `Checked` means one passed test and `Proven` means two or more；tests are formed from the work evidence that produced the
  Skill。Sharpening proposes a revised version and keeps it when it performs better on tests。Source：
  [Skills](https://mem.nowledge.co/docs/concepts/skills)。
- The Skills API separates listing/matching、activity/outcomes、adoption/authoring and Agent host registration，making
  compilation/activation/usage lifecycle externally observable。Source：[Skills API](https://mem.nowledge.co/docs/api#skills)。
- Skill authoring accepts Memories、Threads and Sources as evidence；Thread inputs resolve through provenance。A promotable
  result may then be compiled into a reviewable draft。Source：
  [Author Skill](https://mem.nowledge.co/docs/api/skills/author/post)。

## Evidence Versus Inference

| Evidence / observation | Current inference | Missing evidence / confidence |
| --- | --- | --- |
| Suggestions mine repeated work and retain source moments。 | Candidate discovery plus provenance-preserving procedure synthesis is the information-side core。 | High decomposition confidence；exact detector/prompt is undocumented。 |
| Output compiles to files consumed by connected Agents。 | The compiled Skill is a consumer-specific capability projection，not the sole representation of procedure information。 | High。 |
| Human enablement controls materialization to Agent hosts。 | Review belongs to capability authorization/activation，not necessarily Organization synthesis acceptance。 | High conceptual confidence。 |
| Tests derive from original work evidence and produce `Checked`/`Proven` status。 | These statuses qualify compiled capability behavior，not global truth of every procedural claim。 | High；exact eval semantics are undocumented。 |
| Sharpening compares revised versions on tests。 | This is capability version/evaluation lifecycle，not an independent information-evolution law by itself。 | Medium-high。 |
| Procedures may be authored/imported as well as suggested。 | Repeated-pattern detection is one acquisition route，not the ontology or lifecycle of procedure information。 | High。 |

## Product Disposition

D-493 classifies repeated-procedure discovery as an application and candidate/qualification heuristic for accepted D-472
provenance-preserving n-ary synthesis，not another Product transfer。Its output would be neutral procedure information with
source、scope、rationale、exception、counterevidence and uncertainty preserved through ordinary graph Relations。

Compilation to `SKILL.md`、Agent-host materialization、enablement、activity logging、evaluation badges and sharpening are a separate
downstream capability lifecycle。No independent Skill object、Organization registry or automatic execution authority is inferred
from the official packaging。
