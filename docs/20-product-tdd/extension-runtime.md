# Extension Runtime Contract

## Why This Doc Exists

Extensions cross filesystem discovery, database sync, client-scoped enablement, FastAPI route registration, and runtime lifecycle hooks. That behavior is wider than any one module.

## Cross-Unit Truths

### 1. Extension identity is global per deployment

- Each extension has one global extension ID.
- Installation state is stored in the `extensions` table.
- One deployment does not host multiple instances of the same extension ID.

### 2. Discovery is filesystem-first, sync is database reconciliation

- Runtime discovery scans the local `extensions/` directory.
- `ExtensionManager.sync()` reconciles local packages into `ExtensionModel` rows.
- Extension metadata comes from `pyproject.toml` or packaged dist-info metadata.

### 3. Enablement is client-scoped

- `ExtensionModel.enabled` stores the list of client IDs allowed to run the extension.
- An extension may be installed but disabled for the current client.
- `start_enabled()` only starts extensions enabled for the current client.

### 4. Startup has both API and capability side effects

- `ExtensionBase.on_start()` loads config, persists config schema, registers extension routes, initializes sources, and initializes resolvers.
- Starting an extension is not just toggling a flag; it mutates runtime registries and FastAPI state.

### 5. Shutdown must persist runtime config

- `ExtensionBase.on_close()` persists the runtime config back into the database.
- `ExtensionManager.close_running()` is part of clean application shutdown.

### 6. Install and runtime start are different phases

- `install()` ensures the extension package exists locally and in the database.
- `enable()` grants the current client permission and may start the runtime.
- `disable()` removes the current client permission and closes the runtime if needed.

## Authoritative Code Anchors

- `app/business/extension/main.py`
- `app/schemas/extension/main.py`
- `app/business/client/main.py`
- `run.py`

## What Does Not Belong Here

- per-extension feature docs
- extension-specific source configs
- packaging experiments or third-party marketplace ideas
