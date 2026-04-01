# Phase 1: Source Namespace In `.github`

## Purpose

Define a clean authoring home for product-scope durable docs inside `InKCre/.github`.

## Design Pressure

`.github` is a required repository choice, but it is already semantically overloaded. The layout inside that repo must compensate for that overload instead of making it worse.

## Required Documents

### 1. Source Tree Proposal

Minimum content:

- top-level source subtree name
- child directories for `10-prd`, `15-alignment`, `20-product-tdd`
- policy for non-durable site or profile files

Current recommendation:

```text
product-memory/
  README.md
  10-prd/
  15-alignment/
  20-product-tdd/
```

### 2. Ownership README

This document should answer:

- what belongs here
- what does not belong here
- who edits here
- how mirrors are exported
- how local unit docs differ

### 3. Source Export Boundary Note

Small document defining:

- which subtree is exportable
- which files are internal to `.github` site/build concerns
- whether export is directory-based or manifest-based

## Key Decisions

- choose one dedicated subtree name
- decide whether every product doc must be mirrored or only a subset
- decide whether product alignment docs and product TDD are mirrored together or independently

## Review Questions

- Is the subtree name explicit enough that future contributors will not confuse it with site content?
- Are we preventing product durable docs from being mixed with profile/community repo concerns?
- Can a human understand the ownership model by reading one README?

## Exit Criteria

- one accepted source subtree layout
- one accepted ownership README outline
- one accepted export boundary rule
