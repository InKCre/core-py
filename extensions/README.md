- Built-in and third-party extensions placed here.
- Folder name is the extension id.
- Every extension has a `pyproject.toml`, following template:

```toml
[project]
version = "0.1.0"  # as extension version

[tool.inkcre-ext]
id = "mail"  # optional since folder name is already the extension id
nickname = "Mail" 
```

- Extensions are disabled by default.