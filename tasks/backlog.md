# Backlog

This file tracks volatile work that is still useful, but not yet stable enough for durable docs.

## Architecture

- Route scheduled source collection through persisted collect-job records instead of calling `source.collect(...)` directly from startup scheduling.
- Move organization ownership fully into info-base orchestration instead of leaving it partly implied on source classes.
- Define the stable resolver contract for relation-derived solved content and for raw-content vs solved-content schemas.
- Add a storage-level URL export contract for sinks or external consumers that need URLs instead of raw bytes.
- Split sink responsibilities into clearer runtime types instead of letting `SinkManager.rag` stay the single catch-all path.
- Add an explicit data directory and migration story for installed extensions.

## Runtime And Tooling

- Restore and cleanly manage tracked Alembic version scripts for CI and reviewability.
- Add stronger repository guidance or skills for schema, business-layer, and extension patterns.

## Feature Work

- Support passive source inputs such as webhooks as first-class collection paths.
- Extend tweet schema and resolver handling for attachment URLs and relation-derived attachments.
- Support mail attachment collection in the mail extension.
