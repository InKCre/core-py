# Plan: Update Tweet Schema to Include Optional Attachment and Enhance Resolver

## Objective

Update the Tweet schema in `extensions/twitter/schema.py` to include an optional `attachments` field. Modify the TweetResolver in `extensions/twitter/resolver.py` to populate `attachments` from relations when not present in the raw content.

## Current State Analysis

- **Tweet Schema**: Currently has `id`, `user_id`, `text`. No attachment handling in the schema itself.
- **TweetResolver**: Stub implementation with TODOs.
- **Attachment Handling**: From `bookmark.py`, attachments are stored as relations:
  - "attachment:photo" linking to ImageResolver blocks (solved content is binary of an image).
  - "attachment:video" linking to VideoResolver blocks (solved content is binary of a video).
- **Resolver Base**: Inherits from `Resolver[Tweet, str]`, where raw content is JSON string, solved content is Tweet object.

## Proposed Changes

### 1. Update Tweet Schema (`extensions/twitter/schema.py`)

Add `attachments: Opt[list[bytes]] = None` to the `Tweet` class.

### 2. Implement TweetResolver (`extensions/twitter/resolver.py`)

- In `_get_solved_content`: If not set, fetch relations, collect solved content from "attachment:*" relations' another side block's resolver, set `attachments`, create Tweet.
- Implement `get_text`: Return `text`.
- Implement `get_str_for_embedding`: Return `text`.
- Implement `create_block` and `create_graph` (based on existing patterns, see `extensions\twitter\bookmark.py` and `extensions\mail\resolver.py`).

## Implementation Steps

1. Edit `schema.py` to add the field.
2. Edit `resolver.py` to implement the resolver logic.
3. Test by running relevant tests or checking syntax.

## Questions for User

- Q: How to handle multiple attachment types (photo/video)?
  A: Collect all in one list (the `attachments`)
