# Glossary

This file exists to reduce repeated naming drift. It is not a second architecture spec.

## Product Names vs Python Names

- `info-base`: the product/domain concept
- `info_base`: the Python package and module path
- `core-py`: this backend implementation

## Source Terms

- `source type`: the registered source class, identified by an import-path-like string in `sources_types`
- `source instance`: one configured row in `sources`
- `collect job`: one execution record in `sources_collect_jobs`

Do not use these terms interchangeably.

## Extension Terms

- `extension`: the installed capability identified by one global extension ID
- `extension runtime class`: the Python `Extension` subclass loaded from `extensions.<ext_id>`
- `extension config`: the persisted config payload stored on the extension record

An extension is not the same thing as a source instance created by that extension.

## Content Terms

- `block content`: the persisted string field on `BlockModel`
- `raw content`: the actual content fetched through storage or taken directly from `block.content`
- `solved content`: the resolver's interpreted representation of the block

## Runtime Terms

- `client`: one running node identified by `client_id`
- `enabled extension`: an extension whose `enabled` UUID array contains the current client ID

## Ownership Shortcuts

- sources gather data
- info-base persists and links data
- resolvers interpret data
- storages fetch raw content
- sinks retrieve and index data
