# Python Extension Targets

## Authority Boundary

The application image admits Python Extension code at build time; runtime never downloads or
installs code from the Registry.

- `extensions/twitter/target-publish.json` owns the Registry coordinate, target key, artifact
  format, entrypoint, and compatibility conditions.
- `scripts/build_extension_target.py bundle` creates the deterministic Python bytes from the
  checked-in `extensions/twitter` tree. The frozen root `pdm.lock` remains the only dependency
  authority.
- The pinned Extension Registry CLI owns canonical target-manifest bytes and their digest.
- `release/extension-targets/catalog.json` is local build authority mapping that exact digest to
  the bundle and manifest paths embedded in the image. It is not a second manifest authority.
- Runtime admission requires the Registry-selected target-manifest digest to equal the catalog
  digest, then verifies the manifest descriptor against the bundle before importing it.

The published image layout is:

```text
/app/extension-targets/
├── catalog.json
└── twitter/
    ├── bundle.zip
    └── manifest.json
```

`bundle.zip` contains `extensions/__init__.py` and the complete
`extensions/twitter/**` input except caches, distribution output, and bytecode. Entries are
lexically sorted and use one fixed timestamp, regular-file mode, and the uncompressed ZIP storage
method so zlib upgrades cannot change the target digest. The generated bundle, manifest, catalog,
and their real digests are ignored; source checkouts retain
only `release/extension-targets/README.md` so ordinary Docker contexts have a bounded marker.

## Exact-Main Delivery

`.github/workflows/artifact-publish.yml` runs only after checks pass for the exact current `main`
SHA. It performs this ordered transaction:

1. install the Registry `v0.1.2` CLI and every transitive build dependency from the frozen
   `extension-publisher` PDM group on Python 3.12;
2. build the bundle, canonical manifest, and catalog from one isolated artifact directory;
3. require the CLI digest, catalog digest, manifest descriptor, and bundle bytes to agree;
4. build, inspect, and push the immutable commit image containing that exact target tree;
5. publish the target with the scoped Registry token and verify the public exact release;
6. only after successful publication, move the mutable GHCR `main` tag.

Publishing the same target key and digest is an idempotent retry. The Registry retains the first
immutable target association, so a safe workflow rerun accepts its existing non-empty build ID
instead of requiring the new run ID. A different digest for the occupied target key fails before
the mutable image or automatic production delivery advances. The workflow summary records the
source SHA, immutable image digest, target digest, returned target build ID, publication result,
and promotion result without printing the publisher token.

## Build-Tool Lock

The `extension-publisher` dependency group pins the public Registry wheel URL, wheel SHA-256, CLI
extra, and all transitive publisher dependencies without adding them to the production default
group. The exact-main workflow installs only this frozen group and verifies Registry version and
Python minor before generating target bytes.

## Local Images

A source checkout intentionally contains no admitted target bytes. A plain local Docker build is
therefore suitable for legacy-extension development, but Registry enablement fails closed because
`/app/extension-targets/catalog.json` is absent. To test Registry enablement locally, run the same
bundle, `inkcre-ext build-target`, and catalog commands used by the exact-main workflow before
`docker build`; keep the CLI artifact directory separate from the generated manifest so only
`bundle.zip` contributes to the target digest. The generated tree remains ignored and must never
be committed.

Focused local verification is:

```bash
pdm run pytest -q tests/test_extension_target_artifact.py \
  tests/test_extension_target_delivery.py
```
