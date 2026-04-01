# Task: Update Tweet Schema Attachment URLs

## Status

Open. This remains a task-layer document because the exact shape and migration path are still implementation work, not durable product truth.

## Objective

Update the Twitter tweet schema to support optional attachment URLs and update the resolver so it can derive attachments from relations when raw content does not include them.

## Current Observations

- `extensions/twitter/schema.py` does not expose attachment URLs on the tweet schema.
- `extensions/twitter/resolver.py` still has implementation gaps.
- Relation-derived attachments are already part of the graph model and should not require a second, conflicting source of truth.

## Candidate Change Shape

- extend the tweet schema with an optional attachments field
- update the resolver to hydrate attachments from relations when absent in raw content
- implement the remaining resolver methods needed to expose text and embedding strings consistently

## Constraints

- keep resolver/storage ownership boundaries intact
- avoid duplicating attachment truth in incompatible places
- prefer relation-derived data when the graph already owns that context
