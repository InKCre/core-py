# Semantic-content acceptance assets

Every binary and textual sample in this directory is generated locally by
`generate_assets.py` from original, minimal InKCre test data. Generated samples are ignored by Git and rebuilt by the
shared pytest fixture before a test module uses them. No third-party media or document payload is copied into the
repository.

`cases.json` is the exact resolver-ID/media-family table used by semantic-content acceptance tests. Regenerate the
assets with:

```shell
pdm run python tests/assets/semantic-content/generate_assets.py
```

The samples are deliberately tiny but are real files parsed through the selected production libraries; they are not
mock parser results. Only this README, the generator, the exact case table, and the local `.gitignore` are source
artifacts.
