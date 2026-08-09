# Generated extension targets

The exact-main artifact workflow builds `twitter/bundle.zip`, asks the pinned public
Extension Registry CLI to produce `twitter/manifest.json`, and derives `catalog.json` only
after those bytes agree. Source checkouts contain only this marker. Generated target bytes and
digest-bearing metadata are ignored and must not be committed.
