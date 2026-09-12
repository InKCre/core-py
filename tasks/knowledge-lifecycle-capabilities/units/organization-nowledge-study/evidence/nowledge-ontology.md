# Evidence: Nowledge Ontology

- **Question served**: How does Nowledge use domain vocabulary to improve organization without requiring every information object
  to satisfy one closed schema？
- **Consumer**: [Product design](../product-design.md#ontology--initial-product-inquiry)。
- **Evidence horizon**: Nowledge official documentation observed 2026-09-01。Recheck before version-sensitive Product or
  Technical claims。

## Official Evidence

- Nowledge assigns types to extracted entities，using generic defaults such as `concept`、`product`、`method` and `term`。A
  configured domain vocabulary changes extraction reasoning、reduces one real-world thing landing under different types，and
  enables graph query by kind。Source：[Ontology](https://mem.nowledge.co/docs/ontology)。
- Ontology configuration is optional；doing nothing is documented to preserve existing behavior。Source：
  [Ontology](https://mem.nowledge.co/docs/ontology)。
- A conversational draft reads the actual graph，proposes vocabulary from words already present and reports entity coverage；it
  does not start from an empty schema editor。Source：[Ontology](https://mem.nowledge.co/docs/ontology)。
- Words outside the accepted vocabulary remain visible as unclaimed/grey；extraction never fails over a type and does not
  silently invent an accepted vocabulary type。Source：[Ontology](https://mem.nowledge.co/docs/ontology)。
- Merge/promote/retype suggestions state a reason and preview affected real entities/counts。Vocabulary and data changes require
  explicit acceptance/apply；retired types continue as aliases for old import compatibility。Source：
  [Ontology](https://mem.nowledge.co/docs/ontology)。
- Connected Agents may read types/descriptions/examples、search entity reuse candidates and propose ontology changes；they cannot
  directly change the vocabulary through that workflow。Source：[Ontology](https://mem.nowledge.co/docs/ontology)。

## Evidence Versus Inference

| Evidence / observation | Current inference | Missing evidence / confidence |
| --- | --- | --- |
| Vocabulary applies to extracted entity types。 | This is a partial interpretation/extraction lens，not a schema for all Memory/relation content。 | High。 |
| Draft is derived from existing graph words and coverage。 | Vocabulary follows observed information pressure rather than predefining admissible information。 | High。 |
| Unknown/unclaimed words remain and extraction does not fail。 | The model is open-world and non-blocking。 | High。 |
| Domain types make the graph queryable by kind and reduce type drift。 | Vocabulary alignment can improve candidate/query precision，but type compatibility does not prove entity identity。 | High separation；exact entity-resolution mechanics undocumented。 |
| Retyping previews effect and old types remain aliases。 | Type evolution treats compatibility and blast radius as first-class。 | High as Nowledge behavior；InKCre transfer unknown。 |
| Nowledge requires Human acceptance for vocabulary mutation。 | Human control belongs to its product authority；the open-world/preview principles may transfer independently。 | High boundary。 |

## Product Reconciliation / Closure

Nowledge Ontology does not contradict D-477：it does not normalize arbitrary Block/Relation content into referent/scope/unit
fields。Its strongest candidate learning is an optional、partial、open-world vocabulary lens derived from actual graph evidence。

InKCre currently has no accepted universal entity type system。Research must determine whether vocabulary is useful as
Resolver/LLM interpretation context and query support without inventing Entity storage、closed typing or an ingestion gate。No
transfer is accepted yet。

Vocabulary alignment、entity identity resolution and query execution remain correctly separated。Although domain vocabulary
could technically be passed as operation-owned Agent context，an available seam does not establish a Product need or owner。

D-478 closes Ontology with no InKCre transfer。Do not add a vocabulary capability、profile、lens、context contract、entity type
system or supporting principle。A future concrete operation may rediscover the pressure from its own use failure，without
inheriting this study's candidate。Official evidence remains here only to explain the rejected transfer。
