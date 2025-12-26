# README of InKCre extensions

- Built-in and third-party extensions placed under `extensions/`.
- Folder name is the extension id.
- Extensions are disabled by default.

## Development

- Every extension has a `pyproject.toml` storing the extension metadata:

```toml
[project]
version = "0.1.0"  # as extension version

[tool.inkcre-ext]
id = "mail"  # optional since folder name is already the extension id
nickname = "Mail" 
```

### Source

Sources collects data as graphs and insert into the info-base.

Graphs are consist of blocks and relations. To avoid complex database interaction, use `StarGraphForm`
to automatically resolves references and insert all at once.