# InKCre Core Product

## Purpose

InKCre is an information management system that collects information automatically, organizes it into a reusable base, and exposes ways to retrieve and use that information later.

`core-py` is the Python backend implementation of that system.

## Product Boundary

The product is organized around five domains:

- `source`: gathers data from external systems
- `info-base`: stores and links information as reusable units
- `sink`: retrieves, indexes, and serves information for downstream use
- `extension`: adds source, resolver, and sink capabilities without forking the core
- `client`: represents one running node that participates in the shared system

## Canonical Semantics

### Block

A block is the core information unit.

- It represents one piece of information in the info-base.
- A block may point at raw content stored elsewhere.
- A block is interpreted through its resolver, not by reading the row shape alone.

### Relation

A relation is a directed, typed link between two blocks.

- Relations express dynamic context around blocks.
- Relations are part of the info-base, not temporary query output.

### Storage

Storage is responsible for accessing a block's raw content when that content is not kept directly in the block row.

### Resolver

A resolver turns a block and its local graph context into usable meaning.

- It can derive text for retrieval and embedding.
- It may use related blocks as dynamic attributes of the current block.

### Source Collect Job

A collect job is a unit of source execution state.

- It records the lifecycle of a collection run.
- It is separate from the source type and separate from the source instance configuration.

## Core Workflows

### Collection

Sources collect or receive external data and turn it into blocks and relations.

### Organization

Collected information is normalized into the info-base so it can be linked, deduplicated, and reused.

### Retrieval and Use

Sinks consume the info-base to support retrieval, embedding, RAG, and other downstream workflows.

## Product Invariants

- The info-base is the shared memory center of the system.
- Multiple runtimes can operate around the same info-base.
- Source, info-base, and sink remain separate responsibilities even when implemented in one service.
- Extensions add capability by registration and lifecycle hooks, not by bypassing core ownership boundaries.
- Stable product semantics belong here; implementation detail belongs in code or TDD docs.
