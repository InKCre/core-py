Every extension has a `pyproject.toml`, see template:

```toml
[project]
version = "0.1.0"  # as extension version

[inkcre-ext]
id = "mail"  # optional since folder name is already the extension id
nickname = "Mail" 
```

Extensions won't be enabled until you manually enable it.